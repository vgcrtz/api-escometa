from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.media import AnuncioImagenCreate

class AnuncioCreate(BaseModel):
    contenido: str = Field(..., min_length=1)
    # Si se omite o se manda lista vacía, se enviará a todos los usuarios activos excepto el emisor.
    destinatarios: list[int] | None = None
    imagenes: Optional[List[AnuncioImagenCreate]] = []


class NotificacionCreate(BaseModel):
    id_usuario: int
    contenido: str = Field(..., min_length=1)
