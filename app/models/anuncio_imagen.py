from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class AnuncioImagen(Base):
    __tablename__ = "AnuncioImagen"

    id_imagen = Column(Integer, primary_key=True, autoincrement=True)
    id_anuncio = Column(Integer, ForeignKey("Anuncio.id_anuncio"), nullable=False)

    url = Column(String(500), nullable=False)
    path_storage = Column(String(500), nullable=True)
    nombre_original = Column(String(255), nullable=True)

    fecha_subida = Column(DateTime, server_default=func.now())