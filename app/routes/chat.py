from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_auth, require_user
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
from app.controllers.chat_controller import (
    listar_chats_controller,
    crear_chat_directo_controller,
    crear_chat_directo_nickname_controller,
    crear_chat_grupal_controller,
    crear_chat_grupal_nicknames_controller,
    obtener_chat_controller,
    actualizar_chat_controller,
    eliminar_chat_controller,
    listar_mensajes_controller,
    enviar_mensaje_controller,
    editar_mensaje_controller,
    eliminar_mensaje_controller,
    agregar_participante_controller,
    remover_participante_controller,
    marcar_chat_leido_controller,
    contar_no_leidos_controller,
)

router = APIRouter(prefix="/chats", tags=["Chats"])


def get_chat_user(session_data: dict = Depends(require_auth)):
    return require_user(session_data)



@router.get("")
def listar_chats(db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return listar_chats_controller(db, usuario_actual)


@router.post("/directo")
def crear_chat_directo(payload: ChatDirectoCreate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return crear_chat_directo_controller(payload, db, usuario_actual)


@router.post("/directo/nickname")
def crear_chat_directo_nickname(payload: ChatDirectoNicknameCreate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return crear_chat_directo_nickname_controller(payload, db, usuario_actual)


@router.post("/grupal")
def crear_chat_grupal(payload: ChatGrupalCreate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return crear_chat_grupal_controller(payload, db, usuario_actual)


@router.post("/grupal/nicknames")
def crear_chat_grupal_nicknames(payload: ChatGrupalNicknamesCreate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return crear_chat_grupal_nicknames_controller(payload, db, usuario_actual)


@router.get("/no-leidos")
def contar_no_leidos(db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return contar_no_leidos_controller(db, usuario_actual)


@router.get("/{id_conversacion}")
def obtener_chat(id_conversacion: int, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return obtener_chat_controller(id_conversacion, db, usuario_actual)


@router.put("/{id_conversacion}")
def actualizar_chat(id_conversacion: int, payload: ChatUpdate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return actualizar_chat_controller(id_conversacion, payload, db, usuario_actual)


@router.delete("/{id_conversacion}")
def eliminar_chat(id_conversacion: int, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return eliminar_chat_controller(id_conversacion, db, usuario_actual)


@router.get("/{id_conversacion}/mensajes")
def listar_mensajes(
    id_conversacion: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(get_chat_user),
):
    return listar_mensajes_controller(id_conversacion, db, usuario_actual, limit, offset)


@router.post("/{id_conversacion}/mensajes")
def enviar_mensaje(id_conversacion: int, payload: MensajeCreate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return enviar_mensaje_controller(id_conversacion, payload, db, usuario_actual)


@router.put("/mensajes/{id_mensaje}")
def editar_mensaje(id_mensaje: int, payload: MensajeUpdate, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return editar_mensaje_controller(id_mensaje, payload, db, usuario_actual)


@router.delete("/mensajes/{id_mensaje}")
def eliminar_mensaje(id_mensaje: int, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return eliminar_mensaje_controller(id_mensaje, db, usuario_actual)


@router.post("/{id_conversacion}/participantes")
def agregar_participante(id_conversacion: int, payload: ParticipanteAdd, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return agregar_participante_controller(id_conversacion, payload, db, usuario_actual)


@router.delete("/{id_conversacion}/participantes/{id_usuario}")
def remover_participante(id_conversacion: int, id_usuario: int, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return remover_participante_controller(id_conversacion, id_usuario, db, usuario_actual)


@router.put("/{id_conversacion}/leer")
def marcar_chat_leido(id_conversacion: int, db: Session = Depends(get_db), usuario_actual: dict = Depends(get_chat_user)):
    return marcar_chat_leido_controller(id_conversacion, db, usuario_actual)
