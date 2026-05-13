import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoUsuario(str, enum.Enum):
    ALUMNO = "ALUMNO"
    DOCENTE = "DOCENTE"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    ADMIN = "ADMIN"


class Usuario(Base):
    __tablename__ = "Usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre_usuario: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    correo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    contraseña: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(Enum(TipoUsuario), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    alumno: Mapped[Optional["Alumno"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    docente: Mapped[Optional["Docente"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")
    administrativo: Mapped[Optional["Administrativo"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Alumno(Base):
    __tablename__ = "Alumno"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
    boleta: Mapped[Optional[str]] = mapped_column(String(20))
    carrera: Mapped[Optional[str]] = mapped_column(String(100))
    semestre: Mapped[Optional[int]] = mapped_column(Integer)
    creditos: Mapped[Optional[int]] = mapped_column(Integer)
    carga: Mapped[Optional[int]] = mapped_column(Integer)

    usuario: Mapped[Usuario] = relationship(back_populates="alumno")


class Docente(Base):
    __tablename__ = "Docente"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
    grado_academico: Mapped[Optional[str]] = mapped_column(String(100))
    departamento: Mapped[Optional[str]] = mapped_column(String(100))

    usuario: Mapped[Usuario] = relationship(back_populates="docente")


class Administrativo(Base):
    __tablename__ = "Administrativo"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
    area: Mapped[Optional[str]] = mapped_column(String(100))
    puesto: Mapped[Optional[str]] = mapped_column(String(100))

    usuario: Mapped[Usuario] = relationship(back_populates="administrativo")
