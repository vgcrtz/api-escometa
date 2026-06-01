from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.announcement import AnnouncementCreate
from app.services.announcement_service import AnnouncementService


def create_announcement(db: Session, payload: AnnouncementCreate, current_user: Usuario) -> dict:
    data = AnnouncementService.create_announcement(db, payload, current_user)
    return {"status": "success", "message": "Anuncio creado", "data": data}


def get_all_announcements(db: Session) -> dict:
    return {"status": "success", "data": AnnouncementService.list_all(db)}


def get_my_announcements(db: Session, current_user: Usuario) -> dict:
    return {"status": "success", "data": AnnouncementService.list_for_user(db, current_user)}


def get_important_news(db: Session, current_user: Usuario) -> dict:
    return {"status": "success", "data": AnnouncementService.list_for_user(db, current_user, important_only=True)}
