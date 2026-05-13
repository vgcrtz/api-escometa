from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Conversacion(Base):
    __tablename__ = "Conversacion"

    id_conversacion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class Participante(Base):
    __tablename__ = "Participante"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
    id_conversacion: Mapped[int] = mapped_column(ForeignKey("Conversacion.id_conversacion"), primary_key=True)


class Mensaje(Base):
    __tablename__ = "Mensaje"

    id_mensaje: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), nullable=False)
    id_conversacion: Mapped[int] = mapped_column(ForeignKey("Conversacion.id_conversacion"), nullable=False)


class Anuncio(Base):
    __tablename__ = "Anuncio"

    id_anuncio: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    id_emisor: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), nullable=False)


class AnuncioUsuario(Base):
    __tablename__ = "Anuncio_Usuario"

    id_anuncio: Mapped[int] = mapped_column(ForeignKey("Anuncio.id_anuncio"), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
