from collections.abc import Mapping

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers import academico_controller
from app.database import get_db
from app.middleware.auth import require_auth, require_role
from app.schemas.academico import (
    GrupoCreate,
    GrupoMateriaCreate,
    GrupoMateriaUpdate,
    GrupoUpdate,
    InscripcionPayload,
    MateriaCreate,
    MateriaUpdate,
    SesionCreate,
    SesionUpdate,
)

router = APIRouter(tags=["Académico"])


def _tipo(valor):
    return valor.value if hasattr(valor, "value") else valor


def _get(obj, key, default=None):
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _materia_to_dict(materia):
    return {
        "id_materia": _get(materia, "id_materia"),
        "nombre": _get(materia, "nombre") or _get(materia, "materia"),
    }


def _grupo_to_dict(grupo):
    return {
        "id_grupo": _get(grupo, "id_grupo"),
        "clave": _get(grupo, "clave") or _get(grupo, "grupo"),
        "carrera": _get(grupo, "carrera"),
        "semestre": _get(grupo, "semestre"),
        "turno": _tipo(_get(grupo, "turno")),
    }


def _grupo_materia_to_dict(grupo_materia):
    grupo_obj = _get(grupo_materia, "grupo")
    materia_obj = _get(grupo_materia, "materia")

    grupo_nombre = grupo_obj if isinstance(grupo_obj, str) else _get(grupo_obj, "clave")
    materia_nombre = materia_obj if isinstance(materia_obj, str) else _get(materia_obj, "nombre")

    return {
        "id_grupo_materia": _get(grupo_materia, "id_grupo_materia"),
        "id_grupo": _get(grupo_materia, "id_grupo"),
        "grupo": grupo_nombre,
        "carrera": _get(grupo_materia, "carrera") or _get(grupo_obj, "carrera"),
        "semestre": _get(grupo_materia, "semestre") or _get(grupo_obj, "semestre"),
        "turno": _tipo(_get(grupo_materia, "turno") or _get(grupo_obj, "turno")),
        "id_materia": _get(grupo_materia, "id_materia"),
        "materia": materia_nombre,
        "id_docente": _get(grupo_materia, "id_docente"),
        "docente": _get(grupo_materia, "docente"),
        "cupo": _get(grupo_materia, "cupo"),
    }


def _usuario_to_dict(usuario):
    return {
        "id_usuario": _get(usuario, "id_usuario"),
        "correo": _get(usuario, "correo"),
        "nombre": _get(usuario, "nombre"),
        "nombre_usuario": _get(usuario, "nombre_usuario"),
        "tipo_usuario": _tipo(_get(usuario, "tipo_usuario")),
        "activo": _get(usuario, "activo"),
        "verificado": _get(usuario, "verificado"),
        "fecha_inscripcion": str(_get(usuario, "fecha_inscripcion")) if _get(usuario, "fecha_inscripcion") else None,
        "estado": _tipo(_get(usuario, "estado")),
    }


def _alumno_materia_to_dict(item):
    return {
        "id_alumno": _get(item, "id_alumno"),
        "alumno": _get(item, "alumno"),
        "correo": _get(item, "correo"),
        "id_grupo_materia": _get(item, "id_grupo_materia"),
        "id_grupo": _get(item, "id_grupo"),
        "grupo": _get(item, "grupo"),
        "id_materia": _get(item, "id_materia"),
        "materia": _get(item, "materia"),
        "id_docente": _get(item, "id_docente"),
        "docente": _get(item, "docente"),
        "fecha_inscripcion": str(_get(item, "fecha_inscripcion")) if _get(item, "fecha_inscripcion") else None,
        "estado": _tipo(_get(item, "estado")),
    }


def _sesion_to_dict(sesion):
    return {
        "id_sesion": _get(sesion, "id_sesion"),
        "id_grupo_materia": _get(sesion, "id_grupo_materia"),
        "grupo_materia": _grupo_materia_to_dict(_get(sesion, "grupo_materia")) if _get(sesion, "grupo_materia") else None,
        "dia": _tipo(_get(sesion, "dia")),
        "hora_inicio": _get(sesion, "hora_inicio").isoformat() if _get(sesion, "hora_inicio") else None,
        "hora_fin": _get(sesion, "hora_fin").isoformat() if _get(sesion, "hora_fin") else None,
        "aula": _get(sesion, "aula"),
    }


def _require_admin(session_data: dict):
    require_role(session_data, ["ADMIN"])


def _require_academic_creator(session_data: dict):
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])


def _session_user_id(session_data: dict):
    for key in ("id_usuario", "user_id"):
        if session_data.get(key) is not None:
            return int(session_data[key])
    data = session_data.get("data")
    if isinstance(data, dict) and data.get("id_usuario") is not None:
        return int(data["id_usuario"])
    return None


def _require_self_or_academic_creator(session_data: dict, id_usuario: int):
    if _session_user_id(session_data) == id_usuario:
        return
    try:
        _require_academic_creator(session_data)
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta acción")


@router.get("/materias")
def listar_materias(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_materia_to_dict(m) for m in academico_controller.listar_materias(db)]}


@router.get("/materias/{id_materia}")
def obtener_materia(id_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": _materia_to_dict(academico_controller.obtener_materia(db, id_materia))}


@router.post("/materias", status_code=status.HTTP_201_CREATED)
def crear_materia(payload: MateriaCreate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    materia = academico_controller.crear_materia(db, payload)
    return {"status": "success", "message": "Materia creada", "data": _materia_to_dict(materia)}


@router.put("/materias/{id_materia}")
def actualizar_materia(id_materia: int, payload: MateriaUpdate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    materia = academico_controller.actualizar_materia(db, id_materia, payload)
    return {"status": "success", "message": "Materia actualizada", "data": _materia_to_dict(materia)}


@router.delete("/materias/{id_materia}")
def eliminar_materia(id_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    academico_controller.eliminar_materia(db, id_materia)
    return {"status": "success", "message": "Materia eliminada"}


@router.get("/materias/{id_materia}/grupos")
def listar_grupos_de_materia(id_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    grupos = academico_controller.listar_grupos_de_materia(db, id_materia)
    return {"status": "success", "data": [_grupo_materia_to_dict(gm) for gm in grupos]}


@router.get("/grupos")
def listar_grupos(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_grupo_to_dict(g) for g in academico_controller.listar_grupos(db)]}


@router.get("/grupos/{id_grupo}")
def obtener_grupo(id_grupo: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": _grupo_to_dict(academico_controller.obtener_grupo(db, id_grupo))}


@router.post("/grupos", status_code=status.HTTP_201_CREATED)
def crear_grupo(payload: GrupoCreate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    grupo = academico_controller.crear_grupo(db, payload)
    return {"status": "success", "message": "Grupo creado", "data": _grupo_to_dict(grupo)}


@router.put("/grupos/{id_grupo}")
def actualizar_grupo(id_grupo: int, payload: GrupoUpdate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    grupo = academico_controller.actualizar_grupo(db, id_grupo, payload)
    return {"status": "success", "message": "Grupo actualizado", "data": _grupo_to_dict(grupo)}


@router.delete("/grupos/{id_grupo}")
def eliminar_grupo(id_grupo: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    academico_controller.eliminar_grupo(db, id_grupo)
    return {"status": "success", "message": "Grupo eliminado"}


@router.get("/grupos/{id_grupo}/materias")
def listar_materias_de_grupo(id_grupo: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    materias = academico_controller.listar_materias_de_grupo(db, id_grupo)
    return {"status": "success", "data": [_grupo_materia_to_dict(gm) for gm in materias]}


@router.get("/grupos-materia")
def listar_grupos_materia(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_grupo_materia_to_dict(gm) for gm in academico_controller.listar_grupos_materia(db)]}


@router.get("/grupos-materia/{id_grupo_materia}")
def obtener_grupo_materia(id_grupo_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": _grupo_materia_to_dict(academico_controller.obtener_grupo_materia(db, id_grupo_materia))}


@router.post("/grupos-materia", status_code=status.HTTP_201_CREATED)
def crear_grupo_materia(payload: GrupoMateriaCreate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    grupo_materia = academico_controller.crear_grupo_materia(db, payload)
    return {"status": "success", "message": "Materia-grupo creada", "data": _grupo_materia_to_dict(grupo_materia)}


@router.put("/grupos-materia/{id_grupo_materia}")
def actualizar_grupo_materia(id_grupo_materia: int, payload: GrupoMateriaUpdate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    grupo_materia = academico_controller.actualizar_grupo_materia(db, id_grupo_materia, payload)
    return {"status": "success", "message": "Materia-grupo actualizada", "data": _grupo_materia_to_dict(grupo_materia)}


@router.delete("/grupos-materia/{id_grupo_materia}")
def eliminar_grupo_materia(id_grupo_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    academico_controller.eliminar_grupo_materia(db, id_grupo_materia)
    return {"status": "success", "message": "Materia-grupo eliminada"}


@router.get("/grupos-materia/{id_grupo_materia}/alumnos")
def listar_alumnos_grupo_materia(id_grupo_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    usuarios = academico_controller.listar_alumnos_grupo_materia(db, id_grupo_materia)
    return {"status": "success", "data": [_usuario_to_dict(u) for u in usuarios]}


@router.post("/grupos-materia/{id_grupo_materia}/inscribir")
def inscribir_usuario_grupo_materia(id_grupo_materia: int, payload: InscripcionPayload, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    academico_controller.inscribir_usuario_grupo_materia(db, id_grupo_materia, payload.id_usuario)
    return {"status": "success", "message": "Alumno inscrito en la materia-grupo"}


@router.post("/grupos-materia/{id_grupo_materia}/expulsar")
def expulsar_usuario_grupo_materia(id_grupo_materia: int, payload: InscripcionPayload, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    academico_controller.expulsar_usuario_grupo_materia(db, id_grupo_materia, payload.id_usuario)
    return {"status": "success", "message": "Alumno removido de la materia-grupo"}


@router.get("/alumnos/me/materias")
def listar_mis_materias(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    id_usuario = _session_user_id(session_data)
    if id_usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    materias = academico_controller.listar_materias_alumno(db, id_usuario)
    return {"status": "success", "data": [_alumno_materia_to_dict(m) for m in materias]}


@router.get("/alumnos/{id_usuario}/materias")
def listar_materias_alumno(id_usuario: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_self_or_academic_creator(session_data, id_usuario)
    materias = academico_controller.listar_materias_alumno(db, id_usuario)
    return {"status": "success", "data": [_alumno_materia_to_dict(m) for m in materias]}


@router.get("/sesiones")
def listar_sesiones(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_sesion_to_dict(s) for s in academico_controller.listar_sesiones(db)]}


@router.get("/sesiones/grupo-materia/{id_grupo_materia}")
def listar_sesiones_grupo_materia(id_grupo_materia: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    sesiones = academico_controller.listar_sesiones_grupo_materia(db, id_grupo_materia)
    return {"status": "success", "data": [_sesion_to_dict(s) for s in sesiones]}


@router.post("/sesiones", status_code=status.HTTP_201_CREATED)
def crear_sesion(payload: SesionCreate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    sesion = academico_controller.crear_sesion(db, payload)
    return {"status": "success", "message": "Sesión creada", "data": _sesion_to_dict(sesion)}


@router.put("/sesiones/{id_sesion}")
def actualizar_sesion(id_sesion: int, payload: SesionUpdate, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    sesion = academico_controller.actualizar_sesion(db, id_sesion, payload)
    return {"status": "success", "message": "Sesión actualizada", "data": _sesion_to_dict(sesion)}


@router.delete("/sesiones/{id_sesion}")
def eliminar_sesion(id_sesion: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_admin(session_data)
    academico_controller.eliminar_sesion(db, id_sesion)
    return {"status": "success", "message": "Sesión eliminada"}
