import enum
from datetime import time
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiaSemana(str, enum.Enum):
    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    SABADO = "SABADO"


class Materia(Base):
    __tablename__ = "Materia"

    id_materia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)


class GrupoAcademico(Base):
    __tablename__ = "GrupoAcademico"

    id_grupo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_materia: Mapped[int] = mapped_column(ForeignKey("Materia.id_materia"), nullable=False)
    id_docente: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), nullable=False)

    materia: Mapped[Materia] = relationship()


class UsuarioGrupo(Base):
    __tablename__ = "Usuario_Grupo"

    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), primary_key=True)
    id_grupo: Mapped[int] = mapped_column(ForeignKey("GrupoAcademico.id_grupo"), primary_key=True)


class SesionClase(Base):
    __tablename__ = "SesionClase"

    id_sesion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_grupo: Mapped[int] = mapped_column(ForeignKey("GrupoAcademico.id_grupo"), nullable=False)
    dia: Mapped[DiaSemana] = mapped_column(Enum(DiaSemana), nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    aula: Mapped[Optional[str]] = mapped_column(String(50))
