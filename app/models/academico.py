import enum
from datetime import datetime, time
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DiaSemana(str, enum.Enum):
    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    SABADO = "SABADO"


class TurnoGrupo(str, enum.Enum):
    MATUTINO = "MATUTINO"
    VESPERTINO = "VESPERTINO"
    MIXTO = "MIXTO"


class EstadoInscripcion(str, enum.Enum):
    INSCRITO = "INSCRITO"
    BAJA = "BAJA"


class Materia(Base):
    __tablename__ = "Materia"

    id_materia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    grupos_materia: Mapped[list["GrupoMateria"]] = relationship(back_populates="materia")


class GrupoAcademico(Base):
    __tablename__ = "GrupoAcademico"
    __table_args__ = (
        UniqueConstraint("clave", "carrera", "semestre", name="uq_grupo_academico"),
    )

    id_grupo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clave: Mapped[str] = mapped_column(String(30), nullable=False)
    carrera: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semestre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    turno: Mapped[TurnoGrupo] = mapped_column(Enum(TurnoGrupo), nullable=False, default=TurnoGrupo.MIXTO)

    materias: Mapped[list["GrupoMateria"]] = relationship(back_populates="grupo")


class GrupoMateria(Base):
    __tablename__ = "GrupoMateria"
    __table_args__ = (
        UniqueConstraint("id_grupo", "id_materia", "id_docente", name="uq_grupo_materia_docente"),
        UniqueConstraint("id_grupo_materia", "id_materia", name="uq_grupo_materia_materia"),
        Index("idx_grupo_materia_grupo", "id_grupo"),
        Index("idx_grupo_materia_materia", "id_materia"),
        Index("idx_grupo_materia_docente", "id_docente"),
    )

    id_grupo_materia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_grupo: Mapped[int] = mapped_column(ForeignKey("GrupoAcademico.id_grupo", ondelete="CASCADE"), nullable=False)
    id_materia: Mapped[int] = mapped_column(ForeignKey("Materia.id_materia", ondelete="CASCADE"), nullable=False)
    id_docente: Mapped[int] = mapped_column(ForeignKey("Docente.id_usuario", ondelete="CASCADE"), nullable=False)
    cupo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    grupo: Mapped[GrupoAcademico] = relationship(back_populates="materias")
    materia: Mapped[Materia] = relationship(back_populates="grupos_materia")
    sesiones: Mapped[list["SesionClase"]] = relationship(back_populates="grupo_materia")
    alumnos: Mapped[list["AlumnoMateriaGrupo"]] = relationship(back_populates="grupo_materia")


class AlumnoMateriaGrupo(Base):
    __tablename__ = "Alumno_MateriaGrupo"
    __table_args__ = (
        UniqueConstraint("id_alumno", "id_materia", name="uq_alumno_materia"),
        ForeignKeyConstraint(
            ["id_grupo_materia", "id_materia"],
            ["GrupoMateria.id_grupo_materia", "GrupoMateria.id_materia"],
            ondelete="CASCADE",
        ),
        Index("idx_alumno_materia_grupo", "id_grupo_materia"),
        Index("idx_alumno_materia", "id_materia"),
    )

    id_alumno: Mapped[int] = mapped_column(ForeignKey("Alumno.id_usuario", ondelete="CASCADE"), primary_key=True)
    id_grupo_materia: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_materia: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inscripcion: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    estado: Mapped[EstadoInscripcion] = mapped_column(Enum(EstadoInscripcion), nullable=False, default=EstadoInscripcion.INSCRITO)

    grupo_materia: Mapped[GrupoMateria] = relationship(back_populates="alumnos")


class SesionClase(Base):
    __tablename__ = "SesionClase"
    __table_args__ = (
        Index("idx_sesion_grupo_materia", "id_grupo_materia"),
    )

    id_sesion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_grupo_materia: Mapped[int] = mapped_column(ForeignKey("GrupoMateria.id_grupo_materia", ondelete="CASCADE"), nullable=False)
    dia: Mapped[DiaSemana] = mapped_column(Enum(DiaSemana), nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    aula: Mapped[Optional[str]] = mapped_column(String(50))

    grupo_materia: Mapped[GrupoMateria] = relationship(back_populates="sesiones")
