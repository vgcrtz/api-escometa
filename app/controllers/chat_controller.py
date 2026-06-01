from sqlalchemy.orm import Session

from app.schemas.chat import (
    ChatDirectoCreate,
    ChatDirectoNicknameCreate,
    ChatGrupalCreate,
    ChatGrupalNicknamesCreate,
    ChatUpdate,
    MensajeCreate,
    MensajeUpdate,
    ParticipanteAdd,
)
from app.services.chat_service import ChatService


def listar_chats_controller(db: Session, usuario_actual: dict):
    return ChatService.listar_chats(db, usuario_actual["id_usuario"])


def crear_chat_directo_controller(payload: ChatDirectoCreate, db: Session, usuario_actual: dict):
    return ChatService.crear_chat_directo(db, usuario_actual["id_usuario"], payload.id_usuario_destino)


def crear_chat_directo_nickname_controller(payload: ChatDirectoNicknameCreate, db: Session, usuario_actual: dict):
    return ChatService.crear_chat_directo_por_nickname(
        db,
        usuario_actual["id_usuario"],
        payload.nickname_destino,
    )


def crear_chat_grupal_controller(payload: ChatGrupalCreate, db: Session, usuario_actual: dict):
    return ChatService.crear_chat_grupal(db, usuario_actual["id_usuario"], payload.titulo, payload.participantes)


def crear_chat_grupal_nicknames_controller(payload: ChatGrupalNicknamesCreate, db: Session, usuario_actual: dict):
    return ChatService.crear_chat_grupal_por_nicknames(
        db,
        usuario_actual["id_usuario"],
        payload.titulo,
        payload.participantes,
    )


def obtener_chat_controller(id_conversacion: int, db: Session, usuario_actual: dict):
    return ChatService.obtener_chat(db, id_conversacion, usuario_actual["id_usuario"])


def actualizar_chat_controller(id_conversacion: int, payload: ChatUpdate, db: Session, usuario_actual: dict):
    return ChatService.actualizar_chat(db, id_conversacion, usuario_actual["id_usuario"], payload)


def eliminar_chat_controller(id_conversacion: int, db: Session, usuario_actual: dict):
    return ChatService.eliminar_chat(db, id_conversacion, usuario_actual["id_usuario"])


def listar_mensajes_controller(id_conversacion: int, db: Session, usuario_actual: dict, limit: int = 50, offset: int = 0):
    return ChatService.listar_mensajes(db, id_conversacion, usuario_actual["id_usuario"], limit, offset)


def enviar_mensaje_controller(id_conversacion: int, payload: MensajeCreate, db: Session, usuario_actual: dict):
    return ChatService.enviar_mensaje(db, id_conversacion, usuario_actual["id_usuario"], payload)


def editar_mensaje_controller(id_mensaje: int, payload: MensajeUpdate, db: Session, usuario_actual: dict):
    return ChatService.editar_mensaje(db, id_mensaje, usuario_actual["id_usuario"], payload.contenido)


def eliminar_mensaje_controller(id_mensaje: int, db: Session, usuario_actual: dict):
    return ChatService.eliminar_mensaje(db, id_mensaje, usuario_actual["id_usuario"])


def agregar_participante_controller(id_conversacion: int, payload: ParticipanteAdd, db: Session, usuario_actual: dict):
    return ChatService.agregar_participante(db, id_conversacion, usuario_actual["id_usuario"], payload.id_usuario, payload.rol)


def remover_participante_controller(id_conversacion: int, id_usuario: int, db: Session, usuario_actual: dict):
    return ChatService.remover_participante(db, id_conversacion, usuario_actual["id_usuario"], id_usuario)


def marcar_chat_leido_controller(id_conversacion: int, db: Session, usuario_actual: dict):
    return ChatService.marcar_chat_leido(db, id_conversacion, usuario_actual["id_usuario"])


def contar_no_leidos_controller(db: Session, usuario_actual: dict):
    return ChatService.contar_no_leidos(db, usuario_actual["id_usuario"])
