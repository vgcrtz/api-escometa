from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field


class AsistenciaCreate(BaseModel):
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)


class AsistenciaResponse(BaseModel):
    id_asistencia: int
    id_usuario: int
    fecha: date
    hora: time
    coordenadas: str
    distancia_metros: float
    dentro_zona: bool


class AsistenciaOut(BaseModel):
    id_asistencia: int
    id_usuario: Optional[int]
    fecha: Optional[date]
    hora: Optional[time]
    coordenadas: Optional[str]
