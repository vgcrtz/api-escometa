from datetime import time
from typing import Optional

from pydantic import BaseModel, Field

from app.models.academico import DiaSemana


class MateriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)


class MateriaUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)


class GrupoCreate(BaseModel):
    id_materia: int
    id_docente: int


class GrupoUpdate(BaseModel):
    id_materia: Optional[int] = None
    id_docente: Optional[int] = None


class InscripcionPayload(BaseModel):
    id_usuario: int


class SesionCreate(BaseModel):
    id_grupo: int
    dia: DiaSemana
    hora_inicio: time
    hora_fin: time
    aula: Optional[str] = Field(default=None, max_length=50)


class SesionUpdate(BaseModel):
    dia: Optional[DiaSemana] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    aula: Optional[str] = Field(default=None, max_length=50)
