from datetime import time
from typing import Optional

from pydantic import BaseModel, Field

from app.models.academico import DiaSemana, TurnoGrupo


class MateriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)


class MateriaUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)


class GrupoCreate(BaseModel):
    clave: str = Field(..., min_length=1, max_length=30)
    carrera: Optional[str] = Field(default=None, max_length=100)
    semestre: Optional[int] = Field(default=None, ge=1, le=12)
    turno: TurnoGrupo = TurnoGrupo.MIXTO


class GrupoUpdate(BaseModel):
    clave: Optional[str] = Field(default=None, min_length=1, max_length=30)
    carrera: Optional[str] = Field(default=None, max_length=100)
    semestre: Optional[int] = Field(default=None, ge=1, le=12)
    turno: Optional[TurnoGrupo] = None


class GrupoMateriaCreate(BaseModel):
    id_grupo: int
    id_materia: int
    id_docente: int
    cupo: Optional[int] = Field(default=None, ge=0)


class GrupoMateriaUpdate(BaseModel):
    id_grupo: Optional[int] = None
    id_materia: Optional[int] = None
    id_docente: Optional[int] = None
    cupo: Optional[int] = Field(default=None, ge=0)


class InscripcionPayload(BaseModel):
    id_usuario: int


class SesionCreate(BaseModel):
    id_grupo_materia: int
    dia: DiaSemana
    hora_inicio: time
    hora_fin: time
    aula: Optional[str] = Field(default=None, max_length=50)


class SesionUpdate(BaseModel):
    id_grupo_materia: Optional[int] = None
    dia: Optional[DiaSemana] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    aula: Optional[str] = Field(default=None, max_length=50)
