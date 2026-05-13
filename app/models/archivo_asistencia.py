from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Archivo(Base):
    __tablename__ = "Archivo"

    id_archivo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(ForeignKey("Usuario.id_usuario"))
    nombre: Mapped[Optional[str]] = mapped_column(String(100))
    tipo: Mapped[Optional[str]] = mapped_column(String(50))
    acceso: Mapped[Optional[str]] = mapped_column(String(50))


class Asistencia(Base):
    __tablename__ = "Asistencia"

    id_asistencia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(ForeignKey("Usuario.id_usuario"))
    fecha: Mapped[Optional[date]] = mapped_column(Date)
    hora: Mapped[Optional[time]] = mapped_column(Time)
    coordenadas: Mapped[Optional[str]] = mapped_column(String(100))


class Notificacion(Base):
    __tablename__ = "Notificacion"

    id_notificacion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(ForeignKey("Usuario.id_usuario"))
    contenido: Mapped[Optional[str]] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
