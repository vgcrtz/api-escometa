from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.archivo_asistencia import Notificacion
from app.models.comunicacion import Anuncio, AnuncioUsuario
from app.models.usuario import Usuario
from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate


def _obtener_usuario(db: Session, id_usuario: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def _destinatarios_para_anuncio(db: Session, id_emisor: int, destinatarios: list[int] | None) -> list[int]:
    if destinatarios:
        ids_unicos = sorted(set(destinatarios))
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(ids_unicos), Usuario.activo.is_(True)).all()
        encontrados = {u.id_usuario for u in usuarios}
        faltantes = [uid for uid in ids_unicos if uid not in encontrados]
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Uno o más destinatarios no existen o están inactivos", "ids": faltantes},
            )
        return ids_unicos

    usuarios = db.query(Usuario).filter(Usuario.activo.is_(True), Usuario.id_usuario != id_emisor).all()
    return [u.id_usuario for u in usuarios]


def crear_anuncio(db: Session, id_emisor: int, payload: AnuncioCreate) -> Anuncio:
    _obtener_usuario(db, id_emisor)

    destinatarios = _destinatarios_para_anuncio(db, id_emisor, payload.destinatarios)

    anuncio = Anuncio(contenido=payload.contenido, id_emisor=id_emisor)
    db.add(anuncio)
    db.flush()

    from app.models.anuncio_imagen import AnuncioImagen
    for imagen in payload.imagenes or []:
        db.add(AnuncioImagen(
            id_anuncio=anuncio.id_anuncio,
            url=str(imagen.url),
            path_storage=imagen.path_storage,
            nombre_original=imagen.nombre_original
        ))

    for id_usuario in destinatarios:
        db.add(AnuncioUsuario(id_anuncio=anuncio.id_anuncio, id_usuario=id_usuario))
        db.add(Notificacion(id_usuario=id_usuario, contenido=f"Nuevo anuncio: {payload.contenido}"))

    db.commit()
    db.refresh(anuncio)
    return anuncio


def listar_anuncios(db: Session) -> list[Anuncio]:
    return db.query(Anuncio).order_by(Anuncio.fecha.desc()).all()


def obtener_anuncio(db: Session, id_anuncio: int) -> Anuncio:
    anuncio = db.query(Anuncio).filter(Anuncio.id_anuncio == id_anuncio).first()
    if not anuncio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anuncio no encontrado")
    return anuncio


def listar_mis_anuncios(db: Session, id_usuario: int) -> list[Anuncio]:
    return (
        db.query(Anuncio)
        .join(AnuncioUsuario, AnuncioUsuario.id_anuncio == Anuncio.id_anuncio)
        .filter(AnuncioUsuario.id_usuario == id_usuario)
        .order_by(Anuncio.fecha.desc())
        .all()
    )


def listar_destinatarios_anuncio(db: Session, id_anuncio: int) -> list[int]:
    return [
        r.id_usuario
        for r in db.query(AnuncioUsuario).filter(AnuncioUsuario.id_anuncio == id_anuncio).all()
    ]


def eliminar_anuncio(db: Session, id_anuncio: int) -> None:
    anuncio = obtener_anuncio(db, id_anuncio)
    db.query(AnuncioUsuario).filter(AnuncioUsuario.id_anuncio == id_anuncio).delete()
    db.delete(anuncio)
    db.commit()


def crear_notificacion(db: Session, payload: NotificacionCreate) -> Notificacion:
    _obtener_usuario(db, payload.id_usuario)
    notificacion = Notificacion(id_usuario=payload.id_usuario, contenido=payload.contenido, leida=False)
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def listar_notificaciones_usuario(db: Session, id_usuario: int) -> list[Notificacion]:
    return (
        db.query(Notificacion)
        .filter(Notificacion.id_usuario == id_usuario)
        .order_by(Notificacion.fecha.desc())
        .all()
    )


def listar_notificaciones(db: Session) -> list[Notificacion]:
    return db.query(Notificacion).order_by(Notificacion.fecha.desc()).all()


def marcar_notificacion_leida(db: Session, id_notificacion: int, id_usuario: int | None = None) -> Notificacion:
    query = db.query(Notificacion).filter(Notificacion.id_notificacion == id_notificacion)
    if id_usuario is not None:
        query = query.filter(Notificacion.id_usuario == id_usuario)

    notificacion = query.first()
    if not notificacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")

    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion


def marcar_todas_leidas(db: Session, id_usuario: int) -> int:
    actualizadas = (
        db.query(Notificacion)
        .filter(Notificacion.id_usuario == id_usuario, Notificacion.leida.is_(False))
        .update({"leida": True}, synchronize_session=False)
    )
    db.commit()
    return int(actualizadas)

# Agrega estas funciones a app/services/comunicacion_service.py
# Requiere que hayas ejecutado la migracion SQL y que Anuncio tenga los campos:
# titulo, categoria, prioridad, fijado, activo, visible_desde, visible_hasta.
#
# Si tu tabla Alumno tiene otro nombre, ajusta solamente _get_user_target_profile.

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.comunicacion import Anuncio


def _get_user_target_profile(db: Session, id_usuario: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                u.id_usuario,
                u.tipo_usuario,
                a.carrera,
                a.semestre
            FROM Usuario u
            LEFT JOIN Alumno a ON a.id_usuario = u.id_usuario
            WHERE u.id_usuario = :id_usuario
            """
        ),
        {"id_usuario": id_usuario},
    ).mappings().first()

    if not row:
        return {
            "id_usuario": id_usuario,
            "tipo_usuario": None,
            "carrera": None,
            "semestre": None,
        }

    return dict(row)


def list_important_news(db: Session, id_usuario: int, limit: int = 10):
    profile = _get_user_target_profile(db, id_usuario)

    rows = db.execute(
        text(
            """
            SELECT a.id_anuncio
            FROM Anuncio a
            WHERE
                COALESCE(a.activo, 1) = 1
                AND (a.visible_desde IS NULL OR a.visible_desde <= NOW())
                AND (a.visible_hasta IS NULL OR a.visible_hasta >= NOW())
                AND (
                    EXISTS (
                        SELECT 1
                        FROM Anuncio_Usuario au
                        WHERE au.id_anuncio = a.id_anuncio
                          AND au.id_usuario = :id_usuario
                    )
                    OR EXISTS (
                        SELECT 1
                        FROM Anuncio_Target atg
                        WHERE atg.id_anuncio = a.id_anuncio
                          AND (atg.tipo_usuario IS NULL OR atg.tipo_usuario = :tipo_usuario)
                          AND (atg.carrera IS NULL OR atg.carrera = :carrera)
                          AND (atg.semestre IS NULL OR atg.semestre = :semestre)
                    )
                )
            ORDER BY
                CASE
                    WHEN a.prioridad = 'URGENTE' THEN 1
                    WHEN a.prioridad = 'ALTA' THEN 2
                    WHEN a.fijado = 1 THEN 3
                    WHEN a.prioridad = 'NORMAL' THEN 4
                    ELSE 5
                END ASC,
                a.fecha DESC
            LIMIT :limit
            """
        ),
        {
            "id_usuario": id_usuario,
            "tipo_usuario": profile.get("tipo_usuario"),
            "carrera": profile.get("carrera"),
            "semestre": profile.get("semestre"),
            "limit": limit,
        },
    ).mappings().all()

    ids = [row["id_anuncio"] for row in rows]

    if not ids:
        return []

    announcements = db.query(Anuncio).filter(Anuncio.id_anuncio.in_(ids)).all()
    announcement_by_id = {
        announcement.id_anuncio: announcement
        for announcement in announcements
    }

    return [
        announcement_by_id[id_anuncio]
        for id_anuncio in ids
        if id_anuncio in announcement_by_id
    ]