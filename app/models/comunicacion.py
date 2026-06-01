from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    # Campos para poder mostrar y filtrar noticias importantes.
    titulo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    categoria: Mapped[str] = mapped_column(
        Enum("GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"),
        nullable=False,
        default="GENERAL",
    )
    prioridad: Mapped[str] = mapped_column(
        Enum("BAJA", "NORMAL", "ALTA", "URGENTE"),
        nullable=False,
        default="NORMAL",
    )
    fijado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    visible_desde: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    visible_hasta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    targets: Mapped[list["AnuncioTarget"]] = relationship(
        "AnuncioTarget",
        back_populates="anuncio",
        cascade="all, delete-orphan",
    )


class AnuncioUsuario(Base):
    __tablename__ = "Anuncio_Usuario"

    id_anuncio: Mapped[int] = mapped_column(ForeignKey("Anuncio.id_anuncio"), primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)


class AnuncioTarget(Base):
    __tablename__ = "Anuncio_Target"

    id_target: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_anuncio: Mapped[int] = mapped_column(
        ForeignKey("Anuncio.id_anuncio", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_usuario: Mapped[str | None] = mapped_column(
        Enum("ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN", "INVITADO"),
        nullable=True,
        index=True,
    )
    carrera: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    semestre: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    id_grupo: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    id_grupo_materia: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    anuncio: Mapped[Anuncio] = relationship("Anuncio", back_populates="targets")
