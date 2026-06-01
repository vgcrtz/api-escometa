from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.chat import (
    ChatConversacion,
    ChatParticipante,
    ChatMensaje,
    ChatMensajeAdjunto,
    ChatMensajeLectura,
)
from app.models.usuario import Usuario
from app.schemas.chat import ChatUpdate, MensajeCreate


class ChatService:
    @staticmethod
    def _usuario_existe_activo(db: Session, id_usuario: int):
        usuario = db.query(Usuario).filter(
            Usuario.id_usuario == id_usuario,
            Usuario.activo == True,
        ).first()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

        return usuario

    @staticmethod
    def _limpiar_nickname(nickname: str) -> str:
        return (nickname or "").strip().lstrip("@").strip()

    @staticmethod
    def _usuario_por_nickname_activo(db: Session, nickname: str):
        nickname_limpio = ChatService._limpiar_nickname(nickname)

        if not nickname_limpio:
            raise HTTPException(status_code=400, detail="Ingresa un nickname válido")

        usuario = db.query(Usuario).filter(
            func.lower(Usuario.nombre_usuario) == nickname_limpio.lower(),
            Usuario.activo == True,
        ).first()

        if not usuario:
            raise HTTPException(status_code=404, detail=f"No existe un usuario activo con el nickname @{nickname_limpio}")

        return usuario

    @staticmethod
    def _es_participante(db: Session, id_conversacion: int, id_usuario: int):
        return db.query(ChatParticipante).filter(
            ChatParticipante.id_conversacion == id_conversacion,
            ChatParticipante.id_usuario == id_usuario,
            ChatParticipante.fecha_salida.is_(None),
        ).first()

    @staticmethod
    def _validar_participante(db: Session, id_conversacion: int, id_usuario: int):
        participante = ChatService._es_participante(db, id_conversacion, id_usuario)

        if not participante:
            raise HTTPException(status_code=403, detail="No perteneces a esta conversación")

        return participante

    @staticmethod
    def _validar_admin_chat(db: Session, id_conversacion: int, id_usuario: int):
        participante = ChatService._validar_participante(db, id_conversacion, id_usuario)

        if participante.rol != "ADMIN":
            raise HTTPException(status_code=403, detail="No tienes permisos para modificar esta conversación")

        return participante

    @staticmethod
    def listar_chats(db: Session, id_usuario: int):
        chats = (
            db.query(ChatConversacion)
            .join(ChatParticipante)
            .filter(
                ChatParticipante.id_usuario == id_usuario,
                ChatParticipante.fecha_salida.is_(None),
                ChatConversacion.activo == True,
            )
            .order_by(desc(ChatConversacion.actualizado_en))
            .all()
        )

        return {
            "status": "success",
            "data": [ChatService._chat_to_dict(db, chat, id_usuario) for chat in chats],
        }

    @staticmethod
    def crear_chat_directo(db: Session, id_usuario_origen: int, id_usuario_destino: int):
        if id_usuario_origen == id_usuario_destino:
            raise HTTPException(status_code=400, detail="No puedes crear un chat contigo mismo")

        ChatService._usuario_existe_activo(db, id_usuario_destino)

        chats_origen = (
            db.query(ChatConversacion.id_conversacion)
            .join(ChatParticipante)
            .filter(
                ChatConversacion.tipo == "DIRECTO",
                ChatConversacion.activo == True,
                ChatParticipante.id_usuario == id_usuario_origen,
                ChatParticipante.fecha_salida.is_(None),
            )
            .subquery()
        )

        chat_existente = (
            db.query(ChatConversacion)
            .join(ChatParticipante)
            .filter(
                ChatConversacion.id_conversacion.in_(chats_origen),
                ChatParticipante.id_usuario == id_usuario_destino,
                ChatParticipante.fecha_salida.is_(None),
            )
            .first()
        )

        if chat_existente:
            return {
                "status": "success",
                "message": "Chat directo existente",
                "data": ChatService._chat_to_dict(db, chat_existente, id_usuario_origen),
            }

        chat = ChatConversacion(tipo="DIRECTO", titulo=None, creado_por=id_usuario_origen, activo=True)
        db.add(chat)
        db.flush()

        db.add(ChatParticipante(id_conversacion=chat.id_conversacion, id_usuario=id_usuario_origen, rol="ADMIN"))
        db.add(ChatParticipante(id_conversacion=chat.id_conversacion, id_usuario=id_usuario_destino, rol="MIEMBRO"))

        db.commit()
        db.refresh(chat)

        return {
            "status": "success",
            "message": "Chat directo creado",
            "data": ChatService._chat_to_dict(db, chat, id_usuario_origen),
        }

    @staticmethod
    def crear_chat_directo_por_nickname(db: Session, id_usuario_origen: int, nickname_destino: str):
        usuario_destino = ChatService._usuario_por_nickname_activo(db, nickname_destino)
        return ChatService.crear_chat_directo(db, id_usuario_origen, usuario_destino.id_usuario)

    @staticmethod
    def crear_chat_grupal(db: Session, creado_por: int, titulo: str, participantes: list[int]):
        ids_participantes = list(set(participantes + [creado_por]))

        if len(ids_participantes) < 3:
            raise HTTPException(status_code=400, detail="Un chat grupal requiere al menos 3 participantes")

        for id_usuario in ids_participantes:
            ChatService._usuario_existe_activo(db, id_usuario)

        chat = ChatConversacion(tipo="GRUPO", titulo=titulo, creado_por=creado_por, activo=True)
        db.add(chat)
        db.flush()

        for id_usuario in ids_participantes:
            db.add(
                ChatParticipante(
                    id_conversacion=chat.id_conversacion,
                    id_usuario=id_usuario,
                    rol="ADMIN" if id_usuario == creado_por else "MIEMBRO",
                )
            )

        db.commit()
        db.refresh(chat)

        return {
            "status": "success",
            "message": "Chat grupal creado",
            "data": ChatService._chat_to_dict(db, chat, creado_por),
        }

    @staticmethod
    def crear_chat_grupal_por_nicknames(db: Session, creado_por: int, titulo: str, participantes: list[str]):
        ids_participantes = []
        vistos = set()

        for nickname in participantes:
            usuario = ChatService._usuario_por_nickname_activo(db, nickname)
            if usuario.id_usuario not in vistos:
                ids_participantes.append(usuario.id_usuario)
                vistos.add(usuario.id_usuario)

        return ChatService.crear_chat_grupal(db, creado_por, titulo, ids_participantes)

    @staticmethod
    def obtener_chat(db: Session, id_conversacion: int, id_usuario: int):
        ChatService._validar_participante(db, id_conversacion, id_usuario)

        chat = db.query(ChatConversacion).filter(
            ChatConversacion.id_conversacion == id_conversacion,
            ChatConversacion.activo == True,
        ).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        return {
            "status": "success",
            "data": ChatService._chat_to_dict(db, chat, id_usuario, incluir_participantes=True),
        }

    @staticmethod
    def actualizar_chat(db: Session, id_conversacion: int, id_usuario: int, payload: ChatUpdate):
        ChatService._validar_admin_chat(db, id_conversacion, id_usuario)

        chat = db.query(ChatConversacion).filter(ChatConversacion.id_conversacion == id_conversacion).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        if chat.tipo != "GRUPO" and payload.titulo is not None:
            raise HTTPException(status_code=400, detail="Solo los chats grupales pueden tener título")

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(chat, key, value)

        chat.actualizado_en = datetime.utcnow()
        db.commit()
        db.refresh(chat)

        return {
            "status": "success",
            "message": "Conversación actualizada",
            "data": ChatService._chat_to_dict(db, chat, id_usuario),
        }

    @staticmethod
    def eliminar_chat(db: Session, id_conversacion: int, id_usuario: int):
        ChatService._validar_admin_chat(db, id_conversacion, id_usuario)

        chat = db.query(ChatConversacion).filter(ChatConversacion.id_conversacion == id_conversacion).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        chat.activo = False
        chat.actualizado_en = datetime.utcnow()
        db.commit()

        return {"status": "success", "message": "Conversación eliminada"}

    @staticmethod
    def listar_mensajes(db: Session, id_conversacion: int, id_usuario: int, limit: int = 50, offset: int = 0):
        ChatService._validar_participante(db, id_conversacion, id_usuario)

        mensajes = (
            db.query(ChatMensaje)
            .filter(ChatMensaje.id_conversacion == id_conversacion)
            .order_by(desc(ChatMensaje.fecha_envio))
            .offset(offset)
            .limit(limit)
            .all()
        )
        mensajes.reverse()

        return {"status": "success", "data": [ChatService._mensaje_to_dict(db, mensaje) for mensaje in mensajes]}

    @staticmethod
    def enviar_mensaje(db: Session, id_conversacion: int, id_emisor: int, payload: MensajeCreate):
        ChatService._validar_participante(db, id_conversacion, id_emisor)

        if not payload.contenido and not payload.adjuntos:
            raise HTTPException(status_code=400, detail="El mensaje debe tener contenido o adjuntos")

        mensaje = ChatMensaje(
            id_conversacion=id_conversacion,
            id_emisor=id_emisor,
            contenido=payload.contenido,
            tipo=payload.tipo,
            id_mensaje_respuesta=payload.id_mensaje_respuesta,
        )
        db.add(mensaje)
        db.flush()

        if payload.adjuntos:
            for adjunto in payload.adjuntos:
                db.add(
                    ChatMensajeAdjunto(
                        id_mensaje=mensaje.id_mensaje,
                        url=adjunto.url,
                        path_storage=adjunto.path_storage,
                        nombre_original=adjunto.nombre_original,
                        tipo_mime=adjunto.tipo_mime,
                        tamaño_bytes=adjunto.tamaño_bytes,
                    )
                )

        db.add(ChatMensajeLectura(id_mensaje=mensaje.id_mensaje, id_usuario=id_emisor))

        chat = db.query(ChatConversacion).filter(ChatConversacion.id_conversacion == id_conversacion).first()
        if chat:
            chat.actualizado_en = datetime.utcnow()

        db.commit()
        db.refresh(mensaje)

        return {"status": "success", "message": "ChatMensaje enviado", "data": ChatService._mensaje_to_dict(db, mensaje)}

    @staticmethod
    def editar_mensaje(db: Session, id_mensaje: int, id_usuario: int, contenido: str):
        mensaje = db.query(ChatMensaje).filter(ChatMensaje.id_mensaje == id_mensaje).first()

        if not mensaje:
            raise HTTPException(status_code=404, detail="ChatMensaje no encontrado")

        if mensaje.id_emisor != id_usuario:
            raise HTTPException(status_code=403, detail="Solo puedes editar tus propios mensajes")

        if mensaje.eliminado:
            raise HTTPException(status_code=400, detail="No puedes editar un mensaje eliminado")

        mensaje.contenido = contenido
        mensaje.editado = True
        mensaje.fecha_edicion = datetime.utcnow()
        db.commit()
        db.refresh(mensaje)

        return {"status": "success", "message": "ChatMensaje actualizado", "data": ChatService._mensaje_to_dict(db, mensaje)}

    @staticmethod
    def eliminar_mensaje(db: Session, id_mensaje: int, id_usuario: int):
        mensaje = db.query(ChatMensaje).filter(ChatMensaje.id_mensaje == id_mensaje).first()

        if not mensaje:
            raise HTTPException(status_code=404, detail="ChatMensaje no encontrado")

        if mensaje.id_emisor != id_usuario:
            raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propios mensajes")

        mensaje.eliminado = True
        mensaje.contenido = None
        db.commit()

        return {"status": "success", "message": "ChatMensaje eliminado"}

    @staticmethod
    def agregar_participante(db: Session, id_conversacion: int, id_usuario_solicitante: int, id_usuario_nuevo: int, rol: str = "MIEMBRO"):
        ChatService._validar_admin_chat(db, id_conversacion, id_usuario_solicitante)
        ChatService._usuario_existe_activo(db, id_usuario_nuevo)

        chat = db.query(ChatConversacion).filter(ChatConversacion.id_conversacion == id_conversacion).first()

        if not chat:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        if chat.tipo != "GRUPO":
            raise HTTPException(status_code=400, detail="No puedes agregar participantes a un chat directo")

        existente = db.query(ChatParticipante).filter(
            ChatParticipante.id_conversacion == id_conversacion,
            ChatParticipante.id_usuario == id_usuario_nuevo,
        ).first()

        if existente and existente.fecha_salida is None:
            raise HTTPException(status_code=409, detail="El usuario ya pertenece a esta conversación")

        if existente and existente.fecha_salida is not None:
            existente.fecha_salida = None
            existente.rol = rol
        else:
            db.add(ChatParticipante(id_conversacion=id_conversacion, id_usuario=id_usuario_nuevo, rol=rol))

        db.commit()
        return {"status": "success", "message": "Participante agregado"}

    @staticmethod
    def remover_participante(db: Session, id_conversacion: int, id_usuario_solicitante: int, id_usuario_remover: int):
        ChatService._validar_admin_chat(db, id_conversacion, id_usuario_solicitante)

        participante = db.query(ChatParticipante).filter(
            ChatParticipante.id_conversacion == id_conversacion,
            ChatParticipante.id_usuario == id_usuario_remover,
            ChatParticipante.fecha_salida.is_(None),
        ).first()

        if not participante:
            raise HTTPException(status_code=404, detail="Participante no encontrado en la conversación")

        participante.fecha_salida = datetime.utcnow()
        db.commit()

        return {"status": "success", "message": "Participante removido"}

    @staticmethod
    def marcar_chat_leido(db: Session, id_conversacion: int, id_usuario: int):
        ChatService._validar_participante(db, id_conversacion, id_usuario)

        mensajes = db.query(ChatMensaje).filter(
            ChatMensaje.id_conversacion == id_conversacion,
            ChatMensaje.id_emisor != id_usuario,
            ChatMensaje.eliminado == False,
        ).all()

        actualizadas = 0
        for mensaje in mensajes:
            lectura = db.query(ChatMensajeLectura).filter(
                ChatMensajeLectura.id_mensaje == mensaje.id_mensaje,
                ChatMensajeLectura.id_usuario == id_usuario,
            ).first()
            if not lectura:
                db.add(ChatMensajeLectura(id_mensaje=mensaje.id_mensaje, id_usuario=id_usuario))
                actualizadas += 1

        db.commit()
        return {"status": "success", "message": "Conversación marcada como leída", "data": {"actualizadas": actualizadas}}

    @staticmethod
    def contar_no_leidos(db: Session, id_usuario: int):
        conversaciones = db.query(ChatParticipante.id_conversacion).filter(
            ChatParticipante.id_usuario == id_usuario,
            ChatParticipante.fecha_salida.is_(None),
        ).subquery()

        lecturas = db.query(ChatMensajeLectura.id_mensaje).filter(ChatMensajeLectura.id_usuario == id_usuario).subquery()

        total = db.query(func.count(ChatMensaje.id_mensaje)).filter(
            ChatMensaje.id_conversacion.in_(conversaciones),
            ChatMensaje.id_emisor != id_usuario,
            ChatMensaje.eliminado == False,
            ~ChatMensaje.id_mensaje.in_(lecturas),
        ).scalar()

        return {"status": "success", "data": {"no_leidos": total}}

    @staticmethod
    def _chat_to_dict(db: Session, chat: ChatConversacion, id_usuario_actual: int, incluir_participantes: bool = False):
        data = {
            "id_conversacion": chat.id_conversacion,
            "tipo": chat.tipo,
            "titulo": chat.titulo,
            "creado_por": chat.creado_por,
            "fecha_creacion": chat.fecha_creacion,
            "actualizado_en": chat.actualizado_en,
            "activo": chat.activo,
        }

        participantes = (
            db.query(ChatParticipante, Usuario)
            .join(Usuario, Usuario.id_usuario == ChatParticipante.id_usuario)
            .filter(
                ChatParticipante.id_conversacion == chat.id_conversacion,
                ChatParticipante.fecha_salida.is_(None),
            )
            .all()
        )

        if chat.tipo == "DIRECTO":
            otro = next((usuario for participante, usuario in participantes if usuario.id_usuario != id_usuario_actual), None)
            if otro:
                data["titulo"] = otro.nombre
                data["usuario_directo"] = {
                    "id_usuario": otro.id_usuario,
                    "nombre": otro.nombre,
                    "nombre_usuario": otro.nombre_usuario,
                    "correo": otro.correo,
                    "foto_perfil_url": getattr(otro, "foto_perfil_url", None),
                }

        if incluir_participantes:
            data["participantes"] = [
                {
                    "id_usuario": usuario.id_usuario,
                    "nombre": usuario.nombre,
                    "nombre_usuario": usuario.nombre_usuario,
                    "correo": usuario.correo,
                    "foto_perfil_url": getattr(usuario, "foto_perfil_url", None),
                    "rol_chat": participante.rol,
                }
                for participante, usuario in participantes
            ]

        return data

    @staticmethod
    def _mensaje_to_dict(db: Session, mensaje: ChatMensaje):
        adjuntos = db.query(ChatMensajeAdjunto).filter(ChatMensajeAdjunto.id_mensaje == mensaje.id_mensaje).all()
        emisor = db.query(Usuario).filter(Usuario.id_usuario == mensaje.id_emisor).first()

        return {
            "id_mensaje": mensaje.id_mensaje,
            "id_conversacion": mensaje.id_conversacion,
            "id_emisor": mensaje.id_emisor,
            "emisor": {
                "id_usuario": emisor.id_usuario,
                "nombre": emisor.nombre,
                "nombre_usuario": emisor.nombre_usuario,
                "foto_perfil_url": getattr(emisor, "foto_perfil_url", None),
            } if emisor else None,
            "contenido": None if mensaje.eliminado else mensaje.contenido,
            "tipo": mensaje.tipo,
            "fecha_envio": mensaje.fecha_envio,
            "fecha_edicion": mensaje.fecha_edicion,
            "editado": mensaje.editado,
            "eliminado": mensaje.eliminado,
            "id_mensaje_respuesta": mensaje.id_mensaje_respuesta,
            "adjuntos": [
                {
                    "id_adjunto": adjunto.id_adjunto,
                    "url": adjunto.url,
                    "path_storage": adjunto.path_storage,
                    "nombre_original": adjunto.nombre_original,
                    "tipo_mime": adjunto.tipo_mime,
                    "tamaño_bytes": adjunto.tamaño_bytes,
                }
                for adjunto in adjuntos
            ],
        }
