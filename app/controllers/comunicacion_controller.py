from sqlalchemy.orm import Session

from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate
from app.services import comunicacion_service


def crear_anuncio(db: Session, id_emisor: int, payload: AnuncioCreate):
    return comunicacion_service.crear_anuncio(db, id_emisor, payload)


def listar_anuncios(db: Session):
    return comunicacion_service.listar_anuncios(db)


def obtener_anuncio(db: Session, id_anuncio: int):
    return comunicacion_service.obtener_anuncio(db, id_anuncio)


def listar_mis_anuncios(db: Session, id_usuario: int):
    return comunicacion_service.listar_mis_anuncios(db, id_usuario)


def listar_destinatarios_anuncio(db: Session, id_anuncio: int):
    return comunicacion_service.listar_destinatarios_anuncio(db, id_anuncio)


def eliminar_anuncio(db: Session, id_anuncio: int):
    return comunicacion_service.eliminar_anuncio(db, id_anuncio)


def crear_notificacion(db: Session, payload: NotificacionCreate):
    return comunicacion_service.crear_notificacion(db, payload)


def listar_notificaciones_usuario(db: Session, id_usuario: int):
    return comunicacion_service.listar_notificaciones_usuario(db, id_usuario)


def listar_notificaciones(db: Session):
    return comunicacion_service.listar_notificaciones(db)


def marcar_notificacion_leida(db: Session, id_notificacion: int, id_usuario: int | None = None):
    return comunicacion_service.marcar_notificacion_leida(db, id_notificacion, id_usuario)


def marcar_todas_leidas(db: Session, id_usuario: int):
    return comunicacion_service.marcar_todas_leidas(db, id_usuario)
