from pydantic import BaseModel, HttpUrl
from typing import Optional


class FotoPerfilUpdate(BaseModel):
    foto_perfil_url: HttpUrl


class AnuncioImagenCreate(BaseModel):
    url: HttpUrl
    path_storage: Optional[str] = None
    nombre_original: Optional[str] = None