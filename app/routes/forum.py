from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_auth, require_user
from app.schemas.forum import (
    ForumCommunityCreate,
    ForumCommunityUpdate,
    ForumMessageCreate,
    ForumMessageUpdate,
    ForumPinUpdate,
)
from app.controllers.forum_controller import (
    create_community_controller,
    delete_community_controller,
    delete_message_controller,
    get_community_controller,
    list_communities_controller,
    list_images_controller,
    list_messages_controller,
    list_pinned_messages_controller,
    send_message_controller,
    set_message_pin_controller,
    update_community_controller,
    update_message_controller,
)

router = APIRouter(prefix="/foros", tags=["Foros"])


def get_forum_user(session_data: dict = Depends(require_auth)):
    return require_user(session_data)


@router.get("/comunidades")
def list_communities(db: Session = Depends(get_db)):
    return list_communities_controller(db)


@router.post("/comunidades")
def create_community(
    payload: ForumCommunityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return create_community_controller(payload, db, current_user)


@router.get("/comunidades/{id_community}")
def get_community(id_community: int, db: Session = Depends(get_db)):
    return get_community_controller(id_community, db)


@router.put("/comunidades/{id_community}")
def update_community(
    id_community: int,
    payload: ForumCommunityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return update_community_controller(id_community, payload, db, current_user)


@router.delete("/comunidades/{id_community}")
def delete_community(
    id_community: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return delete_community_controller(id_community, db, current_user)


@router.get("/comunidades/{id_community}/mensajes")
def list_messages(
    id_community: int,
    limit: int = Query(80, ge=1, le=150),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_messages_controller(id_community, db, limit, offset)


@router.post("/comunidades/{id_community}/mensajes")
def send_message(
    id_community: int,
    payload: ForumMessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return send_message_controller(id_community, payload, db, current_user)


@router.get("/comunidades/{id_community}/anclados")
def list_pinned_messages(id_community: int, db: Session = Depends(get_db)):
    return list_pinned_messages_controller(id_community, db)


@router.get("/comunidades/{id_community}/imagenes")
def list_images(id_community: int, db: Session = Depends(get_db)):
    return list_images_controller(id_community, db)


@router.put("/mensajes/{id_message}")
def update_message(
    id_message: int,
    payload: ForumMessageUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return update_message_controller(id_message, payload, db, current_user)


@router.delete("/mensajes/{id_message}")
def delete_message(
    id_message: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return delete_message_controller(id_message, db, current_user)


@router.put("/mensajes/{id_message}/pin")
def set_message_pin(
    id_message: int,
    payload: ForumPinUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_forum_user),
):
    return set_message_pin_controller(id_message, payload, db, current_user)
