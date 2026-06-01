from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, BigInteger, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ChatConversacion(Base):
    __tablename__ = "conversaciones"

    id_conversacion = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(Enum("DIRECTO", "GRUPO"), nullable=False, default="DIRECTO")
    titulo = Column(String(150), nullable=True)
    creado_por = Column(Integer, ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    activo = Column(Boolean, nullable=False, default=True)

    participantes = relationship(
        "ChatParticipante",
        back_populates="conversacion",
        cascade="all, delete-orphan",
    )
    mensajes = relationship(
        "ChatMensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
    )


class ChatParticipante(Base):
    __tablename__ = "conversacion_participantes"

    id_conversacion = Column(
        Integer,
        ForeignKey("conversaciones.id_conversacion", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    id_usuario = Column(
        Integer,
        ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    rol = Column(Enum("MIEMBRO", "ADMIN"), nullable=False, default="MIEMBRO")
    fecha_union = Column(DateTime, nullable=False, server_default=func.now())
    fecha_salida = Column(DateTime, nullable=True)
    silenciado = Column(Boolean, nullable=False, default=False)
    archivado = Column(Boolean, nullable=False, default=False)

    conversacion = relationship("ChatConversacion", back_populates="participantes")


class ChatMensaje(Base):
    __tablename__ = "mensajes"

    id_mensaje = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_conversacion = Column(
        Integer,
        ForeignKey("conversaciones.id_conversacion", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_emisor = Column(
        Integer,
        ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    contenido = Column(Text, nullable=True)
    tipo = Column(Enum("TEXTO", "IMAGEN", "ARCHIVO", "SISTEMA"), nullable=False, default="TEXTO")
    fecha_envio = Column(DateTime, nullable=False, server_default=func.now())
    fecha_edicion = Column(DateTime, nullable=True)
    editado = Column(Boolean, nullable=False, default=False)
    eliminado = Column(Boolean, nullable=False, default=False)
    id_mensaje_respuesta = Column(
        Integer,
        ForeignKey("mensajes.id_mensaje", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )

    conversacion = relationship("ChatConversacion", back_populates="mensajes")
    adjuntos = relationship(
        "ChatMensajeAdjunto",
        back_populates="mensaje",
        cascade="all, delete-orphan",
    )
    lecturas = relationship(
        "ChatMensajeLectura",
        back_populates="mensaje",
        cascade="all, delete-orphan",
    )
    respuesta = relationship("ChatMensaje", remote_side=[id_mensaje])


class ChatMensajeLectura(Base):
    __tablename__ = "mensaje_lecturas"

    id_mensaje = Column(
        Integer,
        ForeignKey("mensajes.id_mensaje", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    id_usuario = Column(
        Integer,
        ForeignKey("Usuario.id_usuario", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    leido_en = Column(DateTime, nullable=False, server_default=func.now())

    mensaje = relationship("ChatMensaje", back_populates="lecturas")


class ChatMensajeAdjunto(Base):
    __tablename__ = "mensaje_adjuntos"

    id_adjunto = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_mensaje = Column(
        Integer,
        ForeignKey("mensajes.id_mensaje", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url = Column(Text, nullable=False)
    path_storage = Column(String(255), nullable=True)
    nombre_original = Column(String(255), nullable=True)
    tipo_mime = Column(String(100), nullable=True)
    tamano_bytes = Column(BigInteger, nullable=True)
    fecha_subida = Column(DateTime, nullable=False, server_default=func.now())

    mensaje = relationship("ChatMensaje", back_populates="adjuntos")
