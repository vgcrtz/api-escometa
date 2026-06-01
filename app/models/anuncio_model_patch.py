# Merge these fields into your current app/models/anuncio.py Anuncio model.
# Keep your existing columns and relationships.

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

# Inside class Anuncio(Base):
# titulo = Column(String(160), nullable=True)
# categoria = Column(Enum("GENERAL", "ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"), nullable=False, default="GENERAL")
# prioridad = Column(Enum("BAJA", "NORMAL", "ALTA", "URGENTE"), nullable=False, default="NORMAL")
# fijado = Column(Boolean, nullable=False, default=False)
# activo = Column(Boolean, nullable=False, default=True)
# visible_desde = Column(DateTime, nullable=True)
# visible_hasta = Column(DateTime, nullable=True)
# targets = relationship("AnuncioTarget", back_populates="anuncio", cascade="all, delete-orphan")
