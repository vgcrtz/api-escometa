from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.controllers import comunicacion_controller
from app.database import get_db
from app.middleware.auth import require_auth, require_role
from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate

router = APIRouter(tags=["Comunicacion"])

PRIORIDADES_PERMITIDAS = {"NORMAL", "ALTA", "URGENTE"}
CATEGORIAS_PERMITIDAS = {"GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"}


def _datetime(value):
    return value.isoformat() if value else None


def _safe_get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return getattr(obj, key, default)
    except Exception:
        return default


def _safe_query_mappings(db: Session | None, query: str, params: dict):
    if db is None:
        return []
    try:
        return [dict(row) for row in db.execute(text(query), params).mappings().all()]
    except Exception:
        db.rollback()
        return []


def _load_announcement_images(db: Session | None, id_anuncio: int | None):
    if not id_anuncio:
        return []

    rows = _safe_query_mappings(
        db,
        """
        SELECT id_imagen, url, nombre_original
        FROM AnuncioImagen
        WHERE id_anuncio = :id_anuncio
        ORDER BY id_imagen ASC
        """,
        {"id_anuncio": id_anuncio},
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


def _load_announcement_targets(db: Session | None, id_anuncio: int | None):
    if not id_anuncio:
        return []

    rows = _safe_query_mappings(
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
        {"id_anuncio": id_anuncio},
    )

    return rows


def _load_announcement_recipients(db: Session | None, id_anuncio: int | None):
    if not id_anuncio:
        return []

    rows = _safe_query_mappings(
        db,
        """
        SELECT id_usuario
        FROM Anuncio_Usuario
        WHERE id_anuncio = :id_anuncio
        ORDER BY id_usuario ASC
        """,
        {"id_anuncio": id_anuncio},
    )

    return [row.get("id_usuario") for row in rows if row.get("id_usuario") is not None]


def _anuncio_to_dict(anuncio, destinatarios: list[int] | None = None, db: Session | None = None):
    id_anuncio = _safe_get(anuncio, "id_anuncio")

    data = {
        "id_anuncio": id_anuncio,
        "contenido": _safe_get(anuncio, "contenido"),
        "fecha": _datetime(_safe_get(anuncio, "fecha")),
        "id_emisor": _safe_get(anuncio, "id_emisor"),
    }

    optional_fields = [
        "titulo",
        "categoria",
        "prioridad",
        "fijado",
        "activo",
        "visible_desde",
        "visible_hasta",
        "emisor",
    ]

    for field in optional_fields:
        value = _safe_get(anuncio, field)
        if value is not None:
            data[field] = _datetime(value) if isinstance(value, datetime) else value

    imagenes = []
    related_images = _safe_get(anuncio, "imagenes") or []
    for imagen in related_images:
        url = _safe_get(imagen, "url")
        if url:
            imagenes.append(
                {
                    "id_imagen": _safe_get(imagen, "id_imagen"),
                    "url": url,
                    "nombre_original": _safe_get(imagen, "nombre_original"),
                }
            )

    if not imagenes:
        imagenes = _load_announcement_images(db, int(id_anuncio) if id_anuncio else None)

    data["imagenes"] = imagenes

    targets = []
    related_targets = _safe_get(anuncio, "targets") or []
    for target in related_targets:
        targets.append(
            {
                "id_target": _safe_get(target, "id_target"),
                "tipo_usuario": _safe_get(target, "tipo_usuario"),
                "carrera": _safe_get(target, "carrera"),
                "semestre": _safe_get(target, "semestre"),
                "id_grupo": _safe_get(target, "id_grupo"),
                "grupo": _safe_get(target, "grupo"),
                "id_grupo_materia": _safe_get(target, "id_grupo_materia"),
            }
        )

    if not targets:
        targets = _load_announcement_targets(db, int(id_anuncio) if id_anuncio else None)

    if targets:
        data["targets"] = targets
        first_target = targets[0]
        for key in ("tipo_usuario", "carrera", "semestre", "id_grupo", "grupo", "id_grupo_materia"):
            if first_target.get(key) is not None and key not in data:
                data[key] = first_target.get(key)

    if destinatarios is not None:
        data["destinatarios"] = destinatarios
    else:
        data["destinatarios"] = _load_announcement_recipients(db, int(id_anuncio) if id_anuncio else None)

    data["etiquetas"] = [
        value
        for value in [
            data.get("categoria"),
            data.get("prioridad"),
            "FIJADO" if data.get("fijado") else None,
        ]
        if value
    ]

    return data

def _notificacion_to_dict(notificacion):
    return {
        "id_notificacion": notificacion.id_notificacion,
        "id_usuario": notificacion.id_usuario,
        "contenido": notificacion.contenido,
        "fecha": _datetime(notificacion.fecha),
        "leida": bool(notificacion.leida),
    }


def _require_staff(session_data: dict):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])


def _is_admin(session_data: dict) -> bool:
    return str(session_data.get("tipo_usuario", "")).upper() == "ADMIN"


def _can_post(session_data: dict) -> bool:
    return str(session_data.get("tipo_usuario", "")).upper() in {"ADMIN", "DOCENTE", "ADMINISTRATIVO"}


def _payload_to_dict(payload):
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=False)
    if hasattr(payload, "dict"):
        return payload.dict(exclude_unset=False)
    return {}


def _datetime_input(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value).replace("T", " ")


def _normalize_priority(value):
    priority = str(value or "NORMAL").strip().upper()
    return priority if priority in PRIORIDADES_PERMITIDAS else "NORMAL"


def _normalize_category(value):
    category = str(value or "GENERAL").strip().upper()
    return category if category in CATEGORIAS_PERMITIDAS else "GENERAL"


def _merge_announcements(*lists):
    merged = {}
    for items in lists:
        for item in items or []:
            announcement_id = _safe_get(item, "id_anuncio")
            if announcement_id is not None:
                merged[int(announcement_id)] = item
    return list(merged.values())


def _list_authored_announcements(db: Session, id_usuario: int):
    rows = _safe_query_mappings(
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
        WHERE a.id_emisor = :id_usuario
        ORDER BY a.fijado DESC, a.fecha DESC
        """,
        {"id_usuario": id_usuario},
    )
    return rows


def _extract_direct_recipient_ids(payload: dict):
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


def _extract_targets(payload: dict):
    targets = payload.get("targets")
    target = payload.get("target")
    result = []

    if isinstance(targets, list):
        result.extend([item for item in targets if isinstance(item, dict)])
    elif isinstance(targets, dict):
        result.append(targets)

    if isinstance(target, dict):
        result.append(target)

    cleaned = []
    for item in result:
        normalized = {
            "tipo_usuario": item.get("tipo_usuario") or None,
            "carrera": item.get("carrera") or None,
            "semestre": item.get("semestre") or None,
            "id_grupo": item.get("id_grupo") or None,
            "id_grupo_materia": item.get("id_grupo_materia") or None,
        }
        if any(value not in (None, "") for value in normalized.values()):
            cleaned.append(normalized)
    return cleaned


def _resolve_target_user_ids(db: Session, targets: list[dict], emisor_id: int):
    ids = []

    for target in targets:
        conditions = ["u.activo = TRUE", "u.id_usuario <> :emisor_id"]
        params = {"emisor_id": emisor_id}

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

        rows = _safe_query_mappings(
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
                ids.append(user_id)

    return ids


def _resolve_payload_recipient_ids(db: Session, payload: dict, emisor_id: int):
    direct_ids = _extract_direct_recipient_ids(payload)
    targets = _extract_targets(payload)
    ids = list(direct_ids)

    for user_id in _resolve_target_user_ids(db, targets, emisor_id):
        if user_id not in ids:
            ids.append(user_id)

    # Si no se especifica destinatario ni target, el aviso es general.
    # Se notifica a todos los usuarios activos excepto al emisor.
    if not direct_ids and not targets:
        rows = _safe_query_mappings(
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


def _ensure_announcement_notifications(db: Session, id_anuncio: int, titulo: str | None, recipient_ids: list[int]):
    if not recipient_ids:
        return

    notification_text = f"Nuevo anuncio: {titulo or 'Aviso importante'}"

    for user_id in recipient_ids:
        db.execute(
            text(
                """
                INSERT IGNORE INTO Anuncio_Usuario (id_anuncio, id_usuario)
                VALUES (:id_anuncio, :id_usuario)
                """
            ),
            {"id_anuncio": id_anuncio, "id_usuario": user_id},
        )
        db.execute(
            text(
                """
                INSERT INTO Notificacion (id_usuario, contenido, tipo, id_anuncio, url_accion, leida)
                SELECT :id_usuario, :contenido, 'ANUNCIO', :id_anuncio, :url_accion, FALSE
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM Notificacion
                    WHERE id_usuario = :id_usuario
                      AND id_anuncio = :id_anuncio
                      AND tipo = 'ANUNCIO'
                )
                """
            ),
            {
                "id_usuario": user_id,
                "contenido": notification_text,
                "id_anuncio": id_anuncio,
                "url_accion": "/inicio",
            },
        )


def _sync_announcement_details(db: Session, id_anuncio: int, payload: dict, emisor_id: int, replace_recipients: bool):
    db.execute(text("DELETE FROM AnuncioImagen WHERE id_anuncio = :id_anuncio"), {"id_anuncio": id_anuncio})
    for image in payload.get("imagenes") or []:
        if not isinstance(image, dict) or not image.get("url"):
            continue
        db.execute(
            text(
                """
                INSERT INTO AnuncioImagen (id_anuncio, url, nombre_original)
                VALUES (:id_anuncio, :url, :nombre_original)
                """
            ),
            {
                "id_anuncio": id_anuncio,
                "url": image.get("url"),
                "nombre_original": image.get("nombre_original") or image.get("nombre") or "imagen-anuncio",
            },
        )

    db.execute(text("DELETE FROM Anuncio_Target WHERE id_anuncio = :id_anuncio"), {"id_anuncio": id_anuncio})
    for target in _extract_targets(payload):
        db.execute(
            text(
                """
                INSERT INTO Anuncio_Target (id_anuncio, tipo_usuario, carrera, semestre, id_grupo, id_grupo_materia)
                VALUES (:id_anuncio, :tipo_usuario, :carrera, :semestre, :id_grupo, :id_grupo_materia)
                """
            ),
            {
                "id_anuncio": id_anuncio,
                "tipo_usuario": target.get("tipo_usuario"),
                "carrera": target.get("carrera"),
                "semestre": target.get("semestre"),
                "id_grupo": target.get("id_grupo"),
                "id_grupo_materia": target.get("id_grupo_materia"),
            },
        )

    recipient_ids = _resolve_payload_recipient_ids(db, payload, emisor_id)
    if replace_recipients:
        db.execute(text("DELETE FROM Anuncio_Usuario WHERE id_anuncio = :id_anuncio"), {"id_anuncio": id_anuncio})
    _ensure_announcement_notifications(db, id_anuncio, payload.get("titulo"), recipient_ids)


def _update_announcement_record(db: Session, id_anuncio: int, payload: dict):
    update_data = {
        "titulo": payload.get("titulo"),
        "contenido": payload.get("contenido"),
        "categoria": _normalize_category(payload.get("categoria")),
        "prioridad": _normalize_priority(payload.get("prioridad")),
        "fijado": bool(payload.get("fijado")),
        "activo": True if payload.get("activo") is None else bool(payload.get("activo")),
        "visible_desde": _datetime_input(payload.get("visible_desde")),
        "visible_hasta": _datetime_input(payload.get("visible_hasta")),
        "id_anuncio": id_anuncio,
    }

    if not str(update_data.get("contenido") or "").strip():
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
            WHERE id_anuncio = :id_anuncio
            """
        ),
        update_data,
    )


def _create_announcement_record(db: Session, id_emisor: int, payload: dict):
    contenido = str(payload.get("contenido") or "").strip()
    if not contenido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contenido del anuncio es obligatorio")

    result = db.execute(
        text(
            """
            INSERT INTO Anuncio (
                titulo, contenido, categoria, prioridad, fijado, activo,
                visible_desde, visible_hasta, id_emisor
            )
            VALUES (
                :titulo, :contenido, :categoria, :prioridad, :fijado, :activo,
                :visible_desde, :visible_hasta, :id_emisor
            )
            """
        ),
        {
            "titulo": payload.get("titulo") or None,
            "contenido": contenido,
            "categoria": _normalize_category(payload.get("categoria")),
            "prioridad": _normalize_priority(payload.get("prioridad")),
            "fijado": bool(payload.get("fijado")),
            "activo": True if payload.get("activo") is None else bool(payload.get("activo")),
            "visible_desde": _datetime_input(payload.get("visible_desde")),
            "visible_hasta": _datetime_input(payload.get("visible_hasta")),
            "id_emisor": id_emisor,
        },
    )

    id_anuncio = result.lastrowid
    rows = _safe_query_mappings(
        db,
        """
        SELECT
            a.id_anuncio, a.titulo, a.contenido, a.categoria, a.prioridad,
            a.fijado, a.activo, a.visible_desde, a.visible_hasta,
            a.fecha, a.id_emisor, ue.nombre AS emisor
        FROM Anuncio a
        LEFT JOIN Usuario ue ON ue.id_usuario = a.id_emisor
        WHERE a.id_anuncio = :id_anuncio
        LIMIT 1
        """,
        {"id_anuncio": id_anuncio},
    )
    return rows[0] if rows else {"id_anuncio": id_anuncio, **payload, "id_emisor": id_emisor}


@router.post("/anuncios", status_code=status.HTTP_201_CREATED)
def create_announcement_route(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    _require_staff(session_data)
    payload_data = _payload_to_dict(payload)
    anuncio = _create_announcement_record(db, int(session_data["id_usuario"]), payload_data)
    id_anuncio = int(_safe_get(anuncio, "id_anuncio"))
    _sync_announcement_details(
        db,
        id_anuncio,
        payload_data,
        int(session_data["id_usuario"]),
        replace_recipients=False,
    )
    db.commit()
    destinatarios = _load_announcement_recipients(db, id_anuncio)
    return {
        "status": "success",
        "message": "Anuncio creado",
        "data": _anuncio_to_dict(anuncio, destinatarios, db),
    }


@router.get("/anuncios")
def list_announcements_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_staff(session_data)
    anuncios = comunicacion_controller.list_announcements(db)
    return {"status": "success", "data": [_anuncio_to_dict(a, db=db) for a in anuncios]}


# IMPORTANTE:
# Esta ruta estatica debe estar antes de /anuncios/{id_anuncio:int}
# para que FastAPI no intente parsear "noticias-importantes" como entero.
@router.get("/anuncios/noticias-importantes")
def list_important_news_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])

    # ADMIN ve todos los anuncios en Inicio. El resto conserva el filtrado
    # personalizado por perfil academico.
    if _is_admin(session_data):
        anuncios = comunicacion_controller.list_announcements(db)
    else:
        anuncios = comunicacion_controller.list_important_news(db, int(session_data["id_usuario"]))
        if _can_post(session_data):
            anuncios = _merge_announcements(anuncios, _list_authored_announcements(db, int(session_data["id_usuario"])))

    return {"status": "success", "data": [_anuncio_to_dict(a, db=db) for a in anuncios]}


@router.get("/anuncios/mis-anuncios")
def list_my_announcements_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    anuncios = comunicacion_controller.list_my_announcements(db, int(session_data["id_usuario"]))
    anuncios = _merge_announcements(anuncios, _list_authored_announcements(db, int(session_data["id_usuario"])))
    return {"status": "success", "data": [_anuncio_to_dict(a, db=db) for a in anuncios]}


@router.get("/anuncios/{id_anuncio:int}")
def get_announcement_route(id_anuncio: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    anuncio = comunicacion_controller.get_announcement(db, id_anuncio)
    destinatarios = comunicacion_controller.list_announcement_recipients(db, id_anuncio)
    return {"status": "success", "data": _anuncio_to_dict(anuncio, destinatarios, db)}


@router.put("/anuncios/{id_anuncio:int}")
def update_announcement_route(
    id_anuncio: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])

    anuncio = comunicacion_controller.get_announcement(db, id_anuncio)
    is_owner = int(getattr(anuncio, "id_emisor", -1)) == int(session_data.get("id_usuario", -1))

    if not _is_admin(session_data) and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes editar tus propios anuncios")

    _update_announcement_record(db, id_anuncio, payload)
    _sync_announcement_details(
        db,
        id_anuncio,
        payload,
        int(getattr(anuncio, "id_emisor", session_data.get("id_usuario"))),
        replace_recipients=True,
    )
    db.commit()

    updated = comunicacion_controller.get_announcement(db, id_anuncio)
    destinatarios = comunicacion_controller.list_announcement_recipients(db, id_anuncio)
    return {
        "status": "success",
        "message": "Anuncio actualizado",
        "data": _anuncio_to_dict(updated, destinatarios, db),
    }


@router.delete("/anuncios/{id_anuncio:int}")
def delete_announcement_route(id_anuncio: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])

    anuncio = comunicacion_controller.get_announcement(db, id_anuncio)
    is_owner = int(getattr(anuncio, "id_emisor", -1)) == int(session_data.get("id_usuario", -1))

    if not _is_admin(session_data) and not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puedes eliminar tus propios anuncios")

    comunicacion_controller.delete_announcement(db, id_anuncio)
    return {"status": "success", "message": "Anuncio eliminado"}


@router.get("/notificaciones")
def list_user_notifications_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    notificaciones = comunicacion_controller.list_user_notifications(db, int(session_data["id_usuario"]))
    return {"status": "success", "data": [_notificacion_to_dict(n) for n in notificaciones]}


@router.get("/notificaciones/todas")
def list_notifications_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ADMIN"])
    notificaciones = comunicacion_controller.list_notifications(db)
    return {"status": "success", "data": [_notificacion_to_dict(n) for n in notificaciones]}


@router.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def create_notification_route(
    payload: NotificacionCreate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])
    notificacion = comunicacion_controller.create_notification(db, payload)
    return {
        "status": "success",
        "message": "Notificación creada",
        "data": _notificacion_to_dict(notificacion),
    }


@router.put("/notificaciones/leer-todas")
def mark_all_notifications_read_route(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    total = comunicacion_controller.mark_all_notifications_read(db, int(session_data["id_usuario"]))
    return {"status": "success", "message": "Notificaciones marcadas como leídas", "data": {"actualizadas": total}}


@router.put("/notificaciones/{id_notificacion:int}/leer")
def mark_notification_read_route(
    id_notificacion: int,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    id_usuario = None if session_data.get("tipo_usuario") == "ADMIN" else int(session_data["id_usuario"])
    notificacion = comunicacion_controller.mark_notification_read(db, id_notificacion, id_usuario)
    return {"status": "success", "message": "Notificación marcada como leída", "data": _notificacion_to_dict(notificacion)}
