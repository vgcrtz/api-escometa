from sqlalchemy.orm import Session

from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate
from app.services import comunicacion_service


# Nuevos nombres en ingles.
def create_announcement(db: Session, id_emisor: int, payload: AnuncioCreate):
    return comunicacion_service.crear_anuncio(db, id_emisor, payload)


def list_announcements(db: Session):
    return comunicacion_service.listar_anuncios(db)


def get_announcement(db: Session, id_anuncio: int):
    return comunicacion_service.obtener_anuncio(db, id_anuncio)


def list_my_announcements(db: Session, id_usuario: int):
    return comunicacion_service.listar_mis_anuncios(db, id_usuario)


def list_important_news(db: Session, id_usuario: int):
    return comunicacion_service.list_important_news(db, id_usuario)


def list_announcement_recipients(db: Session, id_anuncio: int):
    return comunicacion_service.listar_destinatarios_anuncio(db, id_anuncio)


def delete_announcement(db: Session, id_anuncio: int):
    return comunicacion_service.eliminar_anuncio(db, id_anuncio)


def create_notification(db: Session, payload: NotificacionCreate):
    return comunicacion_service.crear_notificacion(db, payload)


def list_user_notifications(db: Session, id_usuario: int):
    return comunicacion_service.listar_notificaciones_usuario(db, id_usuario)


def list_notifications(db: Session):
    return comunicacion_service.listar_notificaciones(db)


def mark_notification_read(db: Session, id_notificacion: int, id_usuario: int | None = None):
    return comunicacion_service.marcar_notificacion_leida(db, id_notificacion, id_usuario)


def mark_all_notifications_read(db: Session, id_usuario: int):
    return comunicacion_service.marcar_todas_leidas(db, id_usuario)


# Alias para no romper imports existentes.
crear_anuncio = create_announcement
listar_anuncios = list_announcements
obtener_anuncio = get_announcement
listar_mis_anuncios = list_my_announcements
listar_destinatarios_anuncio = list_announcement_recipients
eliminar_anuncio = delete_announcement
crear_notificacion = create_notification
listar_notificaciones_usuario = list_user_notifications
listar_notificaciones = list_notifications
marcar_notificacion_leida = mark_notification_read
marcar_todas_leidas = mark_all_notifications_read
