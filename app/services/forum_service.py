from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.forum import ForumAttachment, ForumCommunity, ForumMessage
from app.models.usuario import Usuario
from app.schemas.forum import ForumCommunityCreate, ForumCommunityUpdate, ForumMessageCreate


class ForumService:
    @staticmethod
    def _get_active_user(db: Session, id_user: int):
        user = db.query(Usuario).filter(
            Usuario.id_usuario == id_user,
            Usuario.activo == True,
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

        return user

    @staticmethod
    def _get_active_community(db: Session, id_community: int):
        community = db.query(ForumCommunity).filter(
            ForumCommunity.id_community == id_community,
            ForumCommunity.active == True,
        ).first()

        if not community:
            raise HTTPException(status_code=404, detail="Comunidad no encontrada")

        return community

    @staticmethod
    def _ensure_registered_user(db: Session, current_user: dict):
        id_user = current_user.get("id_usuario")

        if not id_user:
            raise HTTPException(status_code=403, detail="Los invitados no pueden realizar esta acción")

        user = ForumService._get_active_user(db, id_user)

        if getattr(user, "tipo_usuario", None) == "INVITADO":
            raise HTTPException(status_code=403, detail="Los invitados no pueden realizar esta acción")

        return user

    @staticmethod
    def _is_admin(user: Usuario) -> bool:
        return getattr(user, "tipo_usuario", None) == "ADMIN"

    @staticmethod
    def _can_manage_community(user: Usuario, community: ForumCommunity) -> bool:
        return ForumService._is_admin(user) or community.created_by == user.id_usuario

    @staticmethod
    def _ensure_community_manager(user: Usuario, community: ForumCommunity):
        if not ForumService._can_manage_community(user, community):
            raise HTTPException(status_code=403, detail="No tienes permisos para administrar esta comunidad")

    @staticmethod
    def list_communities(db: Session):
        communities = (
            db.query(ForumCommunity)
            .filter(ForumCommunity.active == True)
            .order_by(desc(ForumCommunity.updated_at))
            .all()
        )

        return {
            "status": "success",
            "data": [ForumService._community_to_dict(db, community, include_stats=True) for community in communities],
        }

    @staticmethod
    def create_community(db: Session, current_user: dict, payload: ForumCommunityCreate):
        user = ForumService._ensure_registered_user(db, current_user)

        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Ingresa un nombre válido")

        community = ForumCommunity(
            name=name,
            description=(payload.description or "").strip() or None,
            image_url=payload.image_url,
            created_by=user.id_usuario,
            active=True,
        )

        db.add(community)
        db.commit()
        db.refresh(community)

        return {
            "status": "success",
            "message": "Comunidad creada",
            "data": ForumService._community_to_dict(db, community, include_stats=True),
        }

    @staticmethod
    def get_community(db: Session, id_community: int):
        community = ForumService._get_active_community(db, id_community)

        return {
            "status": "success",
            "data": ForumService._community_to_dict(db, community, include_stats=True),
        }

    @staticmethod
    def update_community(db: Session, id_community: int, current_user: dict, payload: ForumCommunityUpdate):
        user = ForumService._ensure_registered_user(db, current_user)
        community = ForumService._get_active_community(db, id_community)
        ForumService._ensure_community_manager(user, community)

        data = payload.model_dump(exclude_unset=True)

        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
            if not data["name"]:
                raise HTTPException(status_code=400, detail="Ingresa un nombre válido")

        if "description" in data and data["description"] is not None:
            data["description"] = data["description"].strip() or None

        for key, value in data.items():
            setattr(community, key, value)

        community.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(community)

        return {
            "status": "success",
            "message": "Comunidad actualizada",
            "data": ForumService._community_to_dict(db, community, include_stats=True),
        }

    @staticmethod
    def delete_community(db: Session, id_community: int, current_user: dict):
        user = ForumService._ensure_registered_user(db, current_user)
        community = ForumService._get_active_community(db, id_community)
        ForumService._ensure_community_manager(user, community)

        community.active = False
        community.updated_at = datetime.utcnow()
        db.commit()

        return {"status": "success", "message": "Comunidad eliminada"}

    @staticmethod
    def list_messages(db: Session, id_community: int, limit: int = 80, offset: int = 0):
        ForumService._get_active_community(db, id_community)

        messages = (
            db.query(ForumMessage)
            .filter(ForumMessage.id_community == id_community)
            .order_by(ForumMessage.created_at.asc(), ForumMessage.id_message.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "status": "success",
            "data": [ForumService._message_to_dict(db, message) for message in messages],
        }

    @staticmethod
    def send_message(db: Session, id_community: int, current_user: dict, payload: ForumMessageCreate):
        user = ForumService._ensure_registered_user(db, current_user)
        community = ForumService._get_active_community(db, id_community)

        has_content = bool((payload.content or "").strip())
        has_attachments = bool(payload.attachments)

        if not has_content and not has_attachments:
            raise HTTPException(status_code=400, detail="El mensaje debe tener contenido o imágenes")

        message_type = payload.message_type or "TEXT"
        if has_attachments and message_type == "TEXT":
            message_type = "IMAGE"

        message = ForumMessage(
            id_community=id_community,
            id_sender=user.id_usuario,
            content=(payload.content or "").strip() or None,
            message_type=message_type,
            reply_message_id=payload.reply_message_id,
            pinned=False,
            deleted=False,
        )

        db.add(message)
        db.flush()

        if payload.attachments:
            for attachment in payload.attachments:
                db.add(
                    ForumAttachment(
                        id_message=message.id_message,
                        url=attachment.url,
                        storage_path=attachment.storage_path,
                        original_name=attachment.original_name,
                        mime_type=attachment.mime_type,
                        size_bytes=attachment.size_bytes,
                    )
                )

        community.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)

        return {
            "status": "success",
            "message": "Mensaje enviado",
            "data": ForumService._message_to_dict(db, message),
        }

    @staticmethod
    def update_message(db: Session, id_message: int, current_user: dict, content: str):
        user = ForumService._ensure_registered_user(db, current_user)

        message = db.query(ForumMessage).filter(ForumMessage.id_message == id_message).first()
        if not message:
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")

        if message.id_sender != user.id_usuario:
            raise HTTPException(status_code=403, detail="Solo puedes editar tus propios mensajes")

        if message.deleted:
            raise HTTPException(status_code=400, detail="No puedes editar un mensaje eliminado")

        message.content = content.strip()
        message.edited = True
        message.edited_at = datetime.utcnow()
        db.commit()
        db.refresh(message)

        return {
            "status": "success",
            "message": "Mensaje actualizado",
            "data": ForumService._message_to_dict(db, message),
        }

    @staticmethod
    def delete_message(db: Session, id_message: int, current_user: dict):
        user = ForumService._ensure_registered_user(db, current_user)

        message = db.query(ForumMessage).filter(ForumMessage.id_message == id_message).first()
        if not message:
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")

        community = ForumService._get_active_community(db, message.id_community)
        can_delete = (
            message.id_sender == user.id_usuario
            or ForumService._can_manage_community(user, community)
        )

        if not can_delete:
            raise HTTPException(status_code=403, detail="No tienes permisos para borrar este mensaje")

        message.deleted = True
        message.content = None
        message.pinned = False

        community.updated_at = datetime.utcnow()
        db.commit()

        return {"status": "success", "message": "Mensaje eliminado"}

    @staticmethod
    def set_message_pin(db: Session, id_message: int, current_user: dict, pinned: bool):
        user = ForumService._ensure_registered_user(db, current_user)

        message = db.query(ForumMessage).filter(ForumMessage.id_message == id_message).first()
        if not message:
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")

        if message.deleted:
            raise HTTPException(status_code=400, detail="No puedes anclar un mensaje eliminado")

        community = ForumService._get_active_community(db, message.id_community)
        ForumService._ensure_community_manager(user, community)

        message.pinned = pinned
        community.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(message)

        return {
            "status": "success",
            "message": "Mensaje anclado" if pinned else "Mensaje desanclado",
            "data": ForumService._message_to_dict(db, message),
        }

    @staticmethod
    def list_pinned_messages(db: Session, id_community: int):
        ForumService._get_active_community(db, id_community)

        messages = (
            db.query(ForumMessage)
            .filter(
                ForumMessage.id_community == id_community,
                ForumMessage.deleted == False,
                ForumMessage.pinned == True,
            )
            .order_by(desc(ForumMessage.created_at))
            .all()
        )

        return {
            "status": "success",
            "data": [ForumService._message_to_dict(db, message) for message in messages],
        }

    @staticmethod
    def list_images(db: Session, id_community: int):
        ForumService._get_active_community(db, id_community)

        attachments = (
            db.query(ForumAttachment)
            .join(ForumMessage, ForumMessage.id_message == ForumAttachment.id_message)
            .filter(
                ForumMessage.id_community == id_community,
                ForumMessage.deleted == False,
                ForumAttachment.mime_type.like("image/%"),
            )
            .order_by(desc(ForumAttachment.created_at))
            .all()
        )

        return {
            "status": "success",
            "data": [ForumService._attachment_to_dict(attachment) for attachment in attachments],
        }

    @staticmethod
    def _community_to_dict(db: Session, community: ForumCommunity, include_stats: bool = False):
        creator = db.query(Usuario).filter(Usuario.id_usuario == community.created_by).first()

        data = {
            "id_community": community.id_community,
            "name": community.name,
            "description": community.description,
            "image_url": community.image_url,
            "created_by": community.created_by,
            "creator": ForumService._user_to_dict(creator),
            "created_at": community.created_at,
            "updated_at": community.updated_at,
            "active": community.active,
        }

        if include_stats:
            data["message_count"] = db.query(func.count(ForumMessage.id_message)).filter(
                ForumMessage.id_community == community.id_community,
                ForumMessage.deleted == False,
            ).scalar()

            data["image_count"] = (
                db.query(func.count(ForumAttachment.id_attachment))
                .join(ForumMessage, ForumMessage.id_message == ForumAttachment.id_message)
                .filter(
                    ForumMessage.id_community == community.id_community,
                    ForumMessage.deleted == False,
                    ForumAttachment.mime_type.like("image/%"),
                )
                .scalar()
            )

            last_message = (
                db.query(ForumMessage)
                .filter(
                    ForumMessage.id_community == community.id_community,
                    ForumMessage.deleted == False,
                )
                .order_by(desc(ForumMessage.created_at), desc(ForumMessage.id_message))
                .first()
            )

            data["last_message"] = ForumService._message_to_dict(db, last_message) if last_message else None

        return data

    @staticmethod
    def _message_to_dict(db: Session, message: ForumMessage):
        if not message:
            return None

        sender = db.query(Usuario).filter(Usuario.id_usuario == message.id_sender).first()
        attachments = db.query(ForumAttachment).filter(ForumAttachment.id_message == message.id_message).all()

        return {
            "id_message": message.id_message,
            "id_community": message.id_community,
            "id_sender": message.id_sender,
            "sender": ForumService._user_to_dict(sender),
            "content": None if message.deleted else message.content,
            "message_type": message.message_type,
            "created_at": message.created_at,
            "edited_at": message.edited_at,
            "edited": message.edited,
            "deleted": message.deleted,
            "pinned": message.pinned,
            "reply_message_id": message.reply_message_id,
            "attachments": [] if message.deleted else [
                ForumService._attachment_to_dict(attachment) for attachment in attachments
            ],
        }

    @staticmethod
    def _attachment_to_dict(attachment: ForumAttachment):
        return {
            "id_attachment": attachment.id_attachment,
            "url": attachment.url,
            "storage_path": attachment.storage_path,
            "original_name": attachment.original_name,
            "mime_type": attachment.mime_type,
            "size_bytes": attachment.size_bytes,
            "created_at": attachment.created_at,
        }

    @staticmethod
    def _user_to_dict(user: Usuario | None):
        if not user:
            return None

        return {
            "id_usuario": user.id_usuario,
            "nombre": user.nombre,
            "nombre_usuario": user.nombre_usuario,
            "correo": user.correo,
            "foto_perfil_url": getattr(user, "foto_perfil_url", None),
            "tipo_usuario": getattr(user, "tipo_usuario", None),
        }
