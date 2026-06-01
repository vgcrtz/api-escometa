from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class AnuncioTarget(Base):
    __tablename__ = "anuncio_targets"

    id_target = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_anuncio = Column(Integer, ForeignKey("anuncios.id_anuncio", ondelete="CASCADE"), nullable=False, index=True)
    tipo_usuario = Column(Enum("ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN", "INVITADO"), nullable=True, index=True)
    carrera = Column(String(120), nullable=True, index=True)
    semestre = Column(Integer, nullable=True, index=True)
    id_grupo = Column(Integer, nullable=True, index=True)
    id_grupo_materia = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    anuncio = relationship("Anuncio", back_populates="targets")
