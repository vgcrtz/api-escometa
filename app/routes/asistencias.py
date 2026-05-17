from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers import asistencia_controller
from app.database import get_db
from app.middleware.auth import require_auth, require_role
from app.schemas.asistencia import AsistenciaCreate

router = APIRouter(tags=["Asistencias"])


def _asistencia_to_dict(asistencia, distancia_metros: float | None = None):
    data = {
        "id_asistencia": asistencia.id_asistencia,
        "id_usuario": asistencia.id_usuario,
        "fecha": asistencia.fecha.isoformat() if asistencia.fecha else None,
        "hora": asistencia.hora.isoformat() if asistencia.hora else None,
        "coordenadas": asistencia.coordenadas,
    }

    if distancia_metros is not None:
        data["distancia_metros"] = round(distancia_metros, 2)
        data["dentro_zona"] = True

    return data


@router.post("/asistencias/registrar", status_code=status.HTTP_201_CREATED)
def registrar_asistencia(
    payload: AsistenciaCreate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])

    asistencia, distancia = asistencia_controller.registrar_asistencia(
        db,
        int(session_data["id_usuario"]),
        payload.latitud,
        payload.longitud,
    )

    return {
        "status": "success",
        "message": "Asistencia registrada",
        "data": _asistencia_to_dict(asistencia, distancia),
    }


@router.get("/asistencias/mis-asistencias")
def mis_asistencias(
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"])

    asistencias = asistencia_controller.listar_asistencias_usuario(
        db,
        int(session_data["id_usuario"]),
    )

    return {
        "status": "success",
        "data": [_asistencia_to_dict(a) for a in asistencias],
    }


@router.get("/asistencias")
def listar_asistencias(
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])

    asistencias = asistencia_controller.listar_asistencias(db)

    return {
        "status": "success",
        "data": [_asistencia_to_dict(a) for a in asistencias],
    }
