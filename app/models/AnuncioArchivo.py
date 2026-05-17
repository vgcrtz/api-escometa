import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class AnuncioArchivo(Base):
    __tablename__ = "AnuncioArchivo"

    id_archivo = Column(Integer, primary_key=True, autoincrement=True)
    id_anuncio = Column(Integer, ForeignKey("Anuncio.id_anuncio"), nullable=False)
    url = Column(String(500), nullable=False)
    tipo = Column(String(50), default="imagen")
    nombre_original = Column(String(255), nullable=True)
    fecha_subida = Column(DateTime, server_default=func.now())