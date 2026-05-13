from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.usuario import Usuario


class VerificacionCorreo(Base):
    __tablename__ = "VerificacionCorreo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("Usuario.id_usuario"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False)
    expiracion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False)

    usuario: Mapped[Usuario] = relationship()
