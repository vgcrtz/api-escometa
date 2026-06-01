from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UserRole = Literal["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN", "INVITADO"]
NoticeCategory = Literal["GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"]
NoticePriority = Literal["BAJA", "NORMAL", "ALTA", "URGENTE"]


class AnnouncementImageCreate(BaseModel):
    url: str
    path_storage: str | None = None
    nombre_original: str | None = None


class AnnouncementTargetCreate(BaseModel):
    tipo_usuario: UserRole | None = None
    carrera: str | None = Field(default=None, max_length=120)
    semestre: int | None = Field(default=None, ge=1, le=12)
    id_grupo: int | None = None
    id_grupo_materia: int | None = None


class AnnouncementCreate(BaseModel):
    titulo: str | None = Field(default=None, max_length=160)
    contenido: str = Field(min_length=1)
    categoria: NoticeCategory = "GENERAL"
    prioridad: NoticePriority = "NORMAL"
    fijado: bool = False
    activo: bool = True
    visible_desde: datetime | None = None
    visible_hasta: datetime | None = None
    destinatarios: list[int] | None = None
    filtros: list[AnnouncementTargetCreate] | None = None
    imagenes: list[AnnouncementImageCreate] | None = None


class AnnouncementUpdate(BaseModel):
    titulo: str | None = Field(default=None, max_length=160)
    contenido: str | None = None
    categoria: NoticeCategory | None = None
    prioridad: NoticePriority | None = None
    fijado: bool | None = None
    activo: bool | None = None
    visible_desde: datetime | None = None
    visible_hasta: datetime | None = None
    filtros: list[AnnouncementTargetCreate] | None = None


class AnnouncementOut(BaseModel):
    id_anuncio: int
    titulo: str | None = None
    contenido: str
    fecha: datetime
    id_emisor: int | None = None
    categoria: NoticeCategory = "GENERAL"
    prioridad: NoticePriority = "NORMAL"
    fijado: bool = False
    imagenes: list[AnnouncementImageCreate] = []
