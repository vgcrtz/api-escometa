from sqlalchemy.orm import Session

from app.schemas.forum import (
    ForumCommunityCreate,
    ForumCommunityUpdate,
    ForumMessageCreate,
    ForumMessageUpdate,
    ForumPinUpdate,
)
from app.services.forum_service import ForumService


def list_communities_controller(db: Session):
    return ForumService.list_communities(db)


def create_community_controller(payload: ForumCommunityCreate, db: Session, current_user: dict):
    return ForumService.create_community(db, current_user, payload)


def get_community_controller(id_community: int, db: Session):
    return ForumService.get_community(db, id_community)


def update_community_controller(id_community: int, payload: ForumCommunityUpdate, db: Session, current_user: dict):
    return ForumService.update_community(db, id_community, current_user, payload)


def delete_community_controller(id_community: int, db: Session, current_user: dict):
    return ForumService.delete_community(db, id_community, current_user)


def list_messages_controller(id_community: int, db: Session, limit: int = 80, offset: int = 0):
    return ForumService.list_messages(db, id_community, limit, offset)


def send_message_controller(id_community: int, payload: ForumMessageCreate, db: Session, current_user: dict):
    return ForumService.send_message(db, id_community, current_user, payload)


def update_message_controller(id_message: int, payload: ForumMessageUpdate, db: Session, current_user: dict):
    return ForumService.update_message(db, id_message, current_user, payload.content)


def delete_message_controller(id_message: int, db: Session, current_user: dict):
    return ForumService.delete_message(db, id_message, current_user)


def set_message_pin_controller(id_message: int, payload: ForumPinUpdate, db: Session, current_user: dict):
    return ForumService.set_message_pin(db, id_message, current_user, payload.pinned)


def list_pinned_messages_controller(id_community: int, db: Session):
    return ForumService.list_pinned_messages(db, id_community)


def list_images_controller(id_community: int, db: Session):
    return ForumService.list_images(db, id_community)
