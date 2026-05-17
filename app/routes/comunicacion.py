from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers import comunicacion_controller
from app.database import get_db
from app.middleware.auth import require_auth, require_role
from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate

router = APIRouter(tags=["Comunicación"])


def _datetime(valor):
    return valor.isoformat() if valor else None


def _anuncio_to_dict(anuncio, destinatarios: list[int] | None = None):
    data = {
        "id_anuncio": anuncio.id_anuncio,
        "contenido": anuncio.contenido,
        "fecha": _datetime(anuncio.fecha),
        "id_emisor": anuncio.id_emisor,
    }
    if destinatarios is not None:
        data["destinatarios"] = destinatarios
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


# Anuncios
@router.post("/anuncios", status_code=status.HTTP_201_CREATED)
def crear_anuncio(
    payload: AnuncioCreate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    _require_staff(session_data)
    anuncio = comunicacion_controller.crear_anuncio(db, int(session_data["id_usuario"]), payload)
    destinatarios = comunicacion_controller.listar_destinatarios_anuncio(db, anuncio.id_anuncio)
    return {
        "status": "success",
        "message": "Anuncio creado",
        "data": _anuncio_to_dict(anuncio, destinatarios),
    }


@router.get("/anuncios")
def listar_anuncios(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_staff(session_data)
    anuncios = comunicacion_controller.listar_anuncios(db)
    return {"status": "success", "data": [_anuncio_to_dict(a) for a in anuncios]}


@router.get("/anuncios/mis-anuncios")
def listar_mis_anuncios(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    anuncios = comunicacion_controller.listar_mis_anuncios(db, int(session_data["id_usuario"]))
    return {"status": "success", "data": [_anuncio_to_dict(a) for a in anuncios]}


@router.get("/anuncios/{id_anuncio}")
def obtener_anuncio(id_anuncio: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    anuncio = comunicacion_controller.obtener_anuncio(db, id_anuncio)
    destinatarios = comunicacion_controller.listar_destinatarios_anuncio(db, id_anuncio)
    return {"status": "success", "data": _anuncio_to_dict(anuncio, destinatarios)}


@router.delete("/anuncios/{id_anuncio}")
def eliminar_anuncio(id_anuncio: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ADMIN"])
    comunicacion_controller.eliminar_anuncio(db, id_anuncio)
    return {"status": "success", "message": "Anuncio eliminado"}


# Notificaciones
@router.get("/notificaciones")
def mis_notificaciones(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    notificaciones = comunicacion_controller.listar_notificaciones_usuario(db, int(session_data["id_usuario"]))
    return {"status": "success", "data": [_notificacion_to_dict(n) for n in notificaciones]}


@router.get("/notificaciones/todas")
def listar_notificaciones(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ADMIN"])
    notificaciones = comunicacion_controller.listar_notificaciones(db)
    return {"status": "success", "data": [_notificacion_to_dict(n) for n in notificaciones]}


@router.post("/notificaciones", status_code=status.HTTP_201_CREATED)
def crear_notificacion(
    payload: NotificacionCreate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])
    notificacion = comunicacion_controller.crear_notificacion(db, payload)
    return {
        "status": "success",
        "message": "Notificación creada",
        "data": _notificacion_to_dict(notificacion),
    }


@router.put("/notificaciones/leer-todas")
def marcar_todas_leidas(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    total = comunicacion_controller.marcar_todas_leidas(db, int(session_data["id_usuario"]))
    return {"status": "success", "message": "Notificaciones marcadas como leídas", "data": {"actualizadas": total}}


@router.put("/notificaciones/{id_notificacion}/leer")
def marcar_notificacion_leida(
    id_notificacion: int,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])
    id_usuario = None if session_data.get("tipo_usuario") == "ADMIN" else int(session_data["id_usuario"])
    notificacion = comunicacion_controller.marcar_notificacion_leida(db, id_notificacion, id_usuario)
    return {"status": "success", "message": "Notificación marcada como leída", "data": _notificacion_to_dict(notificacion)}
