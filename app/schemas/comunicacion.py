from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.media import AnuncioImagenCreate

# Agrega estos campos a app/schemas/comunicacion.py
# No reemplaza todo tu archivo; es un parche para tus schemas actuales.

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnuncioTargetCreate(BaseModel):
    tipo_usuario: Literal["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN", "INVITADO"] | None = None
    carrera: str | None = None
    semestre: int | None = Field(default=None, ge=1, le=10)
    id_grupo: int | None = None
    id_grupo_materia: int | None = None


class AnuncioCreate(BaseModel):
    titulo: str | None = Field(default=None, max_length=160)
    categoria: Literal["GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"] = "GENERAL"
    prioridad: Literal["BAJA", "NORMAL", "ALTA", "URGENTE"] = "NORMAL"
    fijado: bool = False
    activo: bool = True
    visible_desde: datetime | None = None
    visible_hasta: datetime | None = None
    targets: list[AnuncioTargetCreate] | None = None
    contenido: str = Field(..., min_length=1)
    # Si se omite o se manda lista vacía, se enviará a todos los usuarios activos excepto el emisor.
    destinatarios: list[int] | None = None
    imagenes: Optional[List[AnuncioImagenCreate]] = []


class NotificacionCreate(BaseModel):
    id_usuario: int
    contenido: str = Field(..., min_length=1)
