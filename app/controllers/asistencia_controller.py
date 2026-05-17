from sqlalchemy.orm import Session

from app.services import asistencia_service


def registrar_asistencia(db: Session, id_usuario: int, latitud: float, longitud: float):
    return asistencia_service.registrar_asistencia(db, id_usuario, latitud, longitud)


def listar_asistencias_usuario(db: Session, id_usuario: int):
    return asistencia_service.listar_asistencias_usuario(db, id_usuario)


def listar_asistencias(db: Session):
    return asistencia_service.listar_asistencias(db)
