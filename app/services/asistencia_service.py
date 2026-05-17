from datetime import datetime
from math import atan2, cos, radians, sin, sqrt

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.archivo_asistencia import Asistencia


def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia entre dos puntos geográficos usando Haversine."""
    radio_tierra_m = 6_371_000

    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = (
        sin(delta_phi / 2) ** 2
        + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return radio_tierra_m * c


def registrar_asistencia(db: Session, id_usuario: int, latitud: float, longitud: float) -> tuple[Asistencia, float]:
    distancia = calcular_distancia_metros(
        latitud,
        longitud,
        settings.SCHOOL_LATITUDE,
        settings.SCHOOL_LONGITUDE,
    )

    if distancia > settings.ATTENDANCE_RADIUS_METERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "No estás dentro de la zona permitida",
                "distancia_metros": round(distancia, 2),
                "radio_permitido_metros": settings.ATTENDANCE_RADIUS_METERS,
            },
        )

    ahora = datetime.now()

    asistencia = Asistencia(
        id_usuario=id_usuario,
        fecha=ahora.date(),
        hora=ahora.time().replace(microsecond=0),
        coordenadas=f"{latitud},{longitud}",
    )

    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)

    return asistencia, distancia


def listar_asistencias_usuario(db: Session, id_usuario: int):
    return (
        db.query(Asistencia)
        .filter(Asistencia.id_usuario == id_usuario)
        .order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())
        .all()
    )


def listar_asistencias(db: Session):
    return (
        db.query(Asistencia)
        .order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())
        .all()
    )
