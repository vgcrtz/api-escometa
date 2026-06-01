from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ChatDirectoCreate(BaseModel):
    id_usuario_destino: int


class ChatDirectoNicknameCreate(BaseModel):
    nickname_destino: str = Field(..., min_length=1, max_length=80)


class ChatGrupalCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    participantes: List[int] = Field(..., min_length=1)


class ChatGrupalNicknamesCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    participantes: List[str] = Field(..., min_length=1)


class ChatUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    activo: Optional[bool] = None


class ParticipanteAdd(BaseModel):
    id_usuario: int
    rol: Optional[str] = "MIEMBRO"


class MensajeAdjuntoCreate(BaseModel):
    url: str
    path_storage: Optional[str] = None
    nombre_original: Optional[str] = None
    tipo_mime: Optional[str] = None
    tamano_bytes: Optional[int] = None


class MensajeCreate(BaseModel):
    contenido: Optional[str] = None
    tipo: str = "TEXTO"
    id_mensaje_respuesta: Optional[int] = None
    adjuntos: Optional[List[MensajeAdjuntoCreate]] = None


class MensajeUpdate(BaseModel):
    contenido: str = Field(..., min_length=1)


class UsuarioChatResponse(BaseModel):
    id_usuario: int
    nombre: Optional[str] = None
    nombre_usuario: Optional[str] = None
    correo: Optional[str] = None
    foto_perfil_url: Optional[str] = None


class MensajeResponse(BaseModel):
    id_mensaje: int
    id_conversacion: int
    id_emisor: int
    contenido: Optional[str]
    tipo: str
    fecha_envio: datetime
    fecha_edicion: Optional[datetime] = None
    editado: bool
    eliminado: bool
    id_mensaje_respuesta: Optional[int] = None


class ChatResponse(BaseModel):
    id_conversacion: int
    tipo: str
    titulo: Optional[str]
    creado_por: int
    fecha_creacion: datetime
    actualizado_en: datetime
    activo: bool
