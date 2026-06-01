from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any
from app.controllers.announcement_controller import (
    create_announcement,
    get_all_announcements,
    get_important_news,
    get_my_announcements,
)
from fastapi import APIRouter, Body, Depends, HTTPException, status
from app.database import get_db
from app.middleware.auth import require_auth, require_role, require_user
from app.models.usuario import Usuario
from app.schemas.announcement import AnnouncementCreate

router = APIRouter(prefix="/anuncios", tags=["Anuncios"])

ALLOWED_PRIORITIES = {"NORMAL", "ALTA", "URGENTE"}
ALLOWED_CATEGORIES = {"GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"}


def safe_query_mappings(db: Session, query: str, params: dict) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.execute(text(query), params).mappings().all()]
    except Exception:
        db.rollback()
        return []


def load_announcement_images(db: Session, announcement_id: int) -> list[dict[str, Any]]:
    rows = safe_query_mappings(
        db,
        """
        SELECT id_imagen, url, nombre_original
        FROM AnuncioImagen
        WHERE id_anuncio = :id_anuncio
        ORDER BY id_imagen ASC
        """,
        {"id_anuncio": announcement_id},
    )
    return [
        {
            "id_imagen": row.get("id_imagen"),
            "url": row.get("url"),
            "nombre_original": row.get("nombre_original"),
        }
        for row in rows
        if row.get("url")
    ]


def load_announcement_targets(db: Session, announcement_id: int) -> list[dict[str, Any]]:
    return safe_query_mappings(
        db,
        """
        SELECT
            atg.id_target,
            atg.tipo_usuario,
            atg.carrera,
            atg.semestre,
            atg.id_grupo,
            ga.clave AS grupo,
            atg.id_grupo_materia
        FROM Anuncio_Target atg
        LEFT JOIN GrupoAcademico ga ON ga.id_grupo = atg.id_grupo
        WHERE atg.id_anuncio = :id_anuncio
        ORDER BY atg.id_target ASC
        """,
        {"id_anuncio": announcement_id},
    )


def load_announcement_recipients(db: Session, announcement_id: int) -> list[int]:
    rows = safe_query_mappings(
        db,
        """
        SELECT id_usuario
        FROM Anuncio_Usuario
        WHERE id_anuncio = :id_anuncio
        ORDER BY id_usuario ASC
        """,
        {"id_anuncio": announcement_id},
    )
    return [row.get("id_usuario") for row in rows if row.get("id_usuario") is not None]


def enrich_announcement_item(db: Session, item: Any) -> Any:
    if not isinstance(item, dict):
        return item

    announcement_id = item.get("id_anuncio") or item.get("id")
    if not announcement_id:
        return item

    try:
        announcement_id = int(announcement_id)
    except (TypeError, ValueError):
        return item

    if not item.get("imagenes"):
        item["imagenes"] = load_announcement_images(db, announcement_id)

    if not item.get("targets"):
        targets = load_announcement_targets(db, announcement_id)
        if targets:
            item["targets"] = targets
            first_target = targets[0]
            for key in ("tipo_usuario", "carrera", "semestre", "id_grupo", "grupo", "id_grupo_materia"):
                if first_target.get(key) is not None and key not in item:
                    item[key] = first_target.get(key)

    if "destinatarios" not in item:
        item["destinatarios"] = load_announcement_recipients(db, announcement_id)

    if "etiquetas" not in item:
        item["etiquetas"] = [
            value
            for value in [
                item.get("categoria"),
                item.get("prioridad"),
                "FIJADO" if item.get("fijado") else None,
            ]
            if value
        ]

    return item


def enrich_announcement_response(db: Session, response: Any) -> Any:
    if isinstance(response, list):
        return [enrich_announcement_item(db, item) for item in response]

    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list):
            response["data"] = [enrich_announcement_item(db, item) for item in data]
        elif isinstance(data, dict):
            response["data"] = enrich_announcement_item(db, data)
        elif response.get("id_anuncio") or response.get("id"):
            response = enrich_announcement_item(db, response)

    return response


def response_data_as_list(response: Any) -> list[Any]:
    if isinstance(response, list):
        return response
    if isinstance(response, dict) and isinstance(response.get("data"), list):
        return response.get("data") or []
    return []


def merge_announcement_items(*lists: list[Any]) -> list[Any]:
    merged: dict[int, Any] = {}
    for items in lists:
        for item in items or []:
            if not isinstance(item, dict):
                continue
            announcement_id = item.get("id_anuncio") or item.get("id")
            try:
                announcement_id = int(announcement_id)
            except (TypeError, ValueError):
                continue
            merged[announcement_id] = {**merged.get(announcement_id, {}), **item}
    return list(merged.values())


def is_staff(session_data: dict[str, Any]) -> bool:
    return str(session_data.get("tipo_usuario", "")).upper() in {"ADMIN", "DOCENTE", "ADMINISTRATIVO"}


def is_admin(session_data: dict[str, Any]) -> bool:
    return str(session_data.get("tipo_usuario", "")).upper() == "ADMIN"


def payload_to_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=False)
    if hasattr(payload, "dict"):
        return payload.dict(exclude_unset=False)
    return {}


def datetime_input(value: Any) -> Any:
    if value in (None, ""):
        return None
    return str(value).replace("T", " ")


def normalize_priority(value: Any) -> str:
    priority = str(value or "NORMAL").strip().upper()
    return priority if priority in ALLOWED_PRIORITIES else "NORMAL"


def normalize_category(value: Any) -> str:
    category = str(value or "GENERAL").strip().upper()
    return category if category in ALLOWED_CATEGORIES else "GENERAL"


def extract_announcement_id(response: Any) -> int | None:
    candidates = []
    if isinstance(response, dict):
        candidates.extend([response.get("id_anuncio"), response.get("id")])
        data = response.get("data")
        if isinstance(data, dict):
            candidates.extend([data.get("id_anuncio"), data.get("id")])
    else:
        candidates.extend([getattr(response, "id_anuncio", None), getattr(response, "id", None)])
    for candidate in candidates:
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def list_authored_announcements(db: Session, user_id: int) -> list[dict[str, Any]]:
    return safe_query_mappings(
        db,
        """
        SELECT
            a.id_anuncio,
            a.titulo,
            a.contenido,
            a.categoria,
            a.prioridad,
            a.fijado,
            a.activo,
            a.visible_desde,
            a.visible_hasta,
            a.fecha,
            a.id_emisor,
            ue.nombre AS emisor
        FROM Anuncio a
        LEFT JOIN Usuario ue ON ue.id_usuario = a.id_emisor
        WHERE a.id_emisor = :user_id
        ORDER BY a.fijado DESC, a.fecha DESC
        """,
        {"user_id": user_id},
    )


def get_announcement_row(db: Session, announcement_id: int) -> dict[str, Any] | None:
    rows = safe_query_mappings(
        db,
        """
        SELECT
            a.id_anuncio,
            a.titulo,
            a.contenido,
            a.categoria,
            a.prioridad,
            a.fijado,
            a.activo,
            a.visible_desde,
            a.visible_hasta,
            a.fecha,
            a.id_emisor,
            ue.nombre AS emisor
        FROM Anuncio a
        LEFT JOIN Usuario ue ON ue.id_usuario = a.id_emisor
        WHERE a.id_anuncio = :announcement_id
        LIMIT 1
        """,
        {"announcement_id": announcement_id},
    )
    return rows[0] if rows else None


def extract_direct_recipient_ids(payload: dict[str, Any]) -> list[int]:
    recipients = payload.get("destinatarios")
    if recipients is None:
        recipients = payload.get("recipients")
    if isinstance(recipients, str):
        raw_items = recipients.split(",")
    elif isinstance(recipients, list):
        raw_items = recipients
    else:
        raw_items = []
    ids = []
    for item in raw_items:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in ids:
            ids.append(parsed)
    return ids


def extract_targets(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_targets = payload.get("targets")
    raw_target = payload.get("target")
    items = []
    if isinstance(raw_targets, list):
        items.extend([item for item in raw_targets if isinstance(item, dict)])
    elif isinstance(raw_targets, dict):
        items.append(raw_targets)
    if isinstance(raw_target, dict):
        items.append(raw_target)
    targets = []
    for item in items:
        target = {
            "tipo_usuario": item.get("tipo_usuario") or None,
            "carrera": item.get("carrera") or None,
            "semestre": item.get("semestre") or None,
            "id_grupo": item.get("id_grupo") or None,
            "id_grupo_materia": item.get("id_grupo_materia") or None,
        }
        if any(value not in (None, "") for value in target.values()):
            targets.append(target)
    return targets


def resolve_target_user_ids(db: Session, targets: list[dict[str, Any]], emisor_id: int) -> list[int]:
    ids = []
    for target in targets:
        conditions = ["u.activo = TRUE", "u.id_usuario <> :emisor_id"]
        params: dict[str, Any] = {"emisor_id": emisor_id}
        if target.get("tipo_usuario"):
            conditions.append("u.tipo_usuario = :tipo_usuario")
            params["tipo_usuario"] = target.get("tipo_usuario")
        if target.get("carrera"):
            conditions.append("al.carrera = :carrera")
            params["carrera"] = target.get("carrera")
        if target.get("semestre") not in (None, ""):
            conditions.append("al.semestre = :semestre")
            params["semestre"] = int(target.get("semestre"))
        if target.get("id_grupo") not in (None, ""):
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM Alumno_MateriaGrupo amg
                    INNER JOIN GrupoMateria gm ON gm.id_grupo_materia = amg.id_grupo_materia
                    WHERE amg.id_alumno = u.id_usuario
                      AND gm.id_grupo = :id_grupo
                      AND amg.estado = 'INSCRITO'
                )
                """
            )
            params["id_grupo"] = int(target.get("id_grupo"))
        if target.get("id_grupo_materia") not in (None, ""):
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM Alumno_MateriaGrupo amg2
                    WHERE amg2.id_alumno = u.id_usuario
                      AND amg2.id_grupo_materia = :id_grupo_materia
                      AND amg2.estado = 'INSCRITO'
                )
                """
            )
            params["id_grupo_materia"] = int(target.get("id_grupo_materia"))
        rows = safe_query_mappings(
            db,
            f"""
            SELECT DISTINCT u.id_usuario
            FROM Usuario u
            LEFT JOIN Alumno al ON al.id_usuario = u.id_usuario
            WHERE {' AND '.join(conditions)}
            """,
            params,
        )
        for row in rows:
            user_id = row.get("id_usuario")
            if user_id is not None and user_id not in ids:
                ids.append(int(user_id))
    return ids


def resolve_payload_recipient_ids(db: Session, payload: dict[str, Any], emisor_id: int) -> list[int]:
    direct_ids = extract_direct_recipient_ids(payload)
    targets = extract_targets(payload)
    ids = list(direct_ids)

    for user_id in resolve_target_user_ids(db, targets, emisor_id):
        if user_id not in ids:
            ids.append(user_id)

    # Sin destinatarios ni targets, el aviso es general.
    if not direct_ids and not targets:
        rows = safe_query_mappings(
            db,
            """
            SELECT id_usuario
            FROM Usuario
            WHERE activo = TRUE
              AND id_usuario <> :emisor_id
            """,
            {"emisor_id": emisor_id},
        )
        ids = [row.get("id_usuario") for row in rows if row.get("id_usuario") is not None]

    return [int(user_id) for user_id in ids if int(user_id) != int(emisor_id)]


def ensure_announcement_notifications(db: Session, announcement_id: int, title: str | None, recipient_ids: list[int]) -> None:
    if not recipient_ids:
        return
    notification_text = f"Nuevo anuncio: {title or 'Aviso importante'}"
    for user_id in recipient_ids:
        db.execute(
            text("INSERT IGNORE INTO Anuncio_Usuario (id_anuncio, id_usuario) VALUES (:announcement_id, :user_id)"),
            {"announcement_id": announcement_id, "user_id": user_id},
        )
        db.execute(
            text(
                """
                INSERT INTO Notificacion (id_usuario, contenido, tipo, id_anuncio, url_accion, leida)
                SELECT :user_id, :content, 'ANUNCIO', :announcement_id, :url_action, FALSE
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM Notificacion
                    WHERE id_usuario = :user_id
                      AND id_anuncio = :announcement_id
                      AND tipo = 'ANUNCIO'
                )
                """
            ),
            {
                "user_id": user_id,
                "content": notification_text,
                "announcement_id": announcement_id,
                "url_action": "/inicio",
            },
        )


def sync_announcement_details(db: Session, announcement_id: int, payload: dict[str, Any], emisor_id: int, replace_recipients: bool) -> None:
    db.execute(text("DELETE FROM AnuncioImagen WHERE id_anuncio = :announcement_id"), {"announcement_id": announcement_id})
    for image in payload.get("imagenes") or []:
        if not isinstance(image, dict) or not image.get("url"):
            continue
        db.execute(
            text("INSERT INTO AnuncioImagen (id_anuncio, url, nombre_original) VALUES (:announcement_id, :url, :name)"),
            {"announcement_id": announcement_id, "url": image.get("url"), "name": image.get("nombre_original") or "imagen-anuncio"},
        )
    db.execute(text("DELETE FROM Anuncio_Target WHERE id_anuncio = :announcement_id"), {"announcement_id": announcement_id})
    for target in extract_targets(payload):
        db.execute(
            text(
                """
                INSERT INTO Anuncio_Target (id_anuncio, tipo_usuario, carrera, semestre, id_grupo, id_grupo_materia)
                VALUES (:announcement_id, :tipo_usuario, :carrera, :semestre, :id_grupo, :id_grupo_materia)
                """
            ),
            {
                "announcement_id": announcement_id,
                "tipo_usuario": target.get("tipo_usuario"),
                "carrera": target.get("carrera"),
                "semestre": target.get("semestre"),
                "id_grupo": target.get("id_grupo"),
                "id_grupo_materia": target.get("id_grupo_materia"),
            },
        )
    recipient_ids = resolve_payload_recipient_ids(db, payload, emisor_id)
    if replace_recipients:
        db.execute(text("DELETE FROM Anuncio_Usuario WHERE id_anuncio = :announcement_id"), {"announcement_id": announcement_id})
    ensure_announcement_notifications(db, announcement_id, payload.get("titulo"), recipient_ids)


def update_announcement_record(db: Session, announcement_id: int, payload: dict[str, Any]) -> None:
    if not str(payload.get("contenido") or "").strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contenido del anuncio es obligatorio")
    db.execute(
        text(
            """
            UPDATE Anuncio
            SET titulo = :titulo,
                contenido = :contenido,
                categoria = :categoria,
                prioridad = :prioridad,
                fijado = :fijado,
                activo = :activo,
                visible_desde = :visible_desde,
                visible_hasta = :visible_hasta
            WHERE id_anuncio = :announcement_id
            """
        ),
        {
            "announcement_id": announcement_id,
            "titulo": payload.get("titulo"),
            "contenido": payload.get("contenido"),
            "categoria": normalize_category(payload.get("categoria")),
            "prioridad": normalize_priority(payload.get("prioridad")),
            "fijado": bool(payload.get("fijado")),
            "activo": True if payload.get("activo") is None else bool(payload.get("activo")),
            "visible_desde": datetime_input(payload.get("visible_desde")),
            "visible_hasta": datetime_input(payload.get("visible_hasta")),
        },
    )

def create_announcement_record(db: Session, current_user: Usuario, payload: dict[str, Any]) -> dict[str, Any]:
    contenido = str(payload.get("contenido") or "").strip()
    if not contenido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contenido del anuncio es obligatorio")

    result = db.execute(
        text(
            """
            INSERT INTO Anuncio (titulo, contenido, categoria, prioridad, fijado, activo, visible_desde, visible_hasta, id_emisor)
            VALUES (:titulo, :contenido, :categoria, :prioridad, :fijado, :activo, :visible_desde, :visible_hasta, :emisor_id)
            """
        ),
        {
            "titulo": payload.get("titulo") or None,
            "contenido": contenido,
            "categoria": normalize_category(payload.get("categoria")),
            "prioridad": normalize_priority(payload.get("prioridad")),
            "fijado": bool(payload.get("fijado")),
            "activo": True if payload.get("activo") is None else bool(payload.get("activo")),
            "visible_desde": datetime_input(payload.get("visible_desde")),
            "visible_hasta": datetime_input(payload.get("visible_hasta")),
            "emisor_id": current_user.id_usuario,
        },
    )

    announcement_id = int(result.lastrowid)
    row = get_announcement_row(db, announcement_id)
    return row or {"id_anuncio": announcement_id, **payload, "id_emisor": current_user.id_usuario}

def resolve_current_user(db: Session, session_data: dict[str, Any]) -> Usuario:
    require_user(session_data)

    user_id = session_data.get("id_usuario")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    current_user = (
        db.query(Usuario)
        .filter(
            Usuario.id_usuario == int(user_id),
            Usuario.activo.is_(True),
        )
        .first()
    )

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    return current_user


@router.post("")
def post_announcement(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])
    current_user = resolve_current_user(db, session_data)

    payload_data = payload_to_dict(payload)
    response_data = create_announcement_record(db, current_user, payload_data)
    announcement_id = extract_announcement_id(response_data)
    if announcement_id:
        sync_announcement_details(db, announcement_id, payload_data, current_user.id_usuario, replace_recipients=False)
        db.commit()
    return enrich_announcement_response(db, {"status": "success", "message": "Anuncio creado", "data": response_data})


@router.get("")
def list_announcements(
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])

    return enrich_announcement_response(db, get_all_announcements(db))


@router.get("/noticias-importantes")
def list_important_news(
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    current_user = resolve_current_user(db, session_data)

    if is_admin(session_data):
        return enrich_announcement_response(db, get_all_announcements(db))

    response = get_important_news(db, current_user)
    if is_staff(session_data):
        merged = merge_announcement_items(
            response_data_as_list(response),
            list_authored_announcements(db, current_user.id_usuario),
        )
        return enrich_announcement_response(db, {"status": "success", "data": merged})

    return enrich_announcement_response(db, response)


@router.get("/mis-anuncios")
def list_my_announcements(
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    current_user = resolve_current_user(db, session_data)

    return enrich_announcement_response(db, get_my_announcements(db, current_user))

@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])
    current_user = resolve_current_user(db, session_data)
    current = get_announcement_row(db, announcement_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anuncio no encontrado")

    is_owner = int(current.get("id_emisor")) == int(current_user.id_usuario)
    if not is_admin(session_data) and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes editar tus propios anuncios")

    update_announcement_record(db, announcement_id, payload)
    sync_announcement_details(db, announcement_id, payload, int(current.get("id_emisor")), replace_recipients=True)
    db.commit()

    updated = get_announcement_row(db, announcement_id)
    return enrich_announcement_response(db, {"status": "success", "message": "Anuncio actualizado", "data": updated})


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    session_data: dict[str, Any] = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])
    current_user = resolve_current_user(db, session_data)
    current = get_announcement_row(db, announcement_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anuncio no encontrado")

    is_owner = int(current.get("id_emisor")) == int(current_user.id_usuario)
    if not is_admin(session_data) and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes eliminar tus propios anuncios")

    db.execute(text("DELETE FROM Anuncio WHERE id_anuncio = :announcement_id"), {"announcement_id": announcement_id})
    db.commit()
    return {"status": "success", "message": "Anuncio eliminado"}
