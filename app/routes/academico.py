from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers import academico_controller
from app.database import get_db
from app.middleware.auth import require_auth, require_role
from app.schemas.academico import GrupoCreate, GrupoUpdate, InscripcionPayload, MateriaCreate, MateriaUpdate, SesionCreate, SesionUpdate

router = APIRouter(tags=["Académico"])


def _tipo(valor):
    return valor.value if hasattr(valor, "value") else valor


def _materia_to_dict(materia):
    return {
        "id_materia": materia.id_materia,
        "nombre": materia.nombre,
    }


def _grupo_to_dict(grupo):
    return {
        "id_grupo": grupo.id_grupo,
        "id_materia": grupo.id_materia,
        "id_docente": grupo.id_docente,
        "materia": _materia_to_dict(grupo.materia) if grupo.materia else None,
    }


def _usuario_to_dict(usuario):
    return {
        "id_usuario": usuario.id_usuario,
        "correo": usuario.correo,
        "nombre": usuario.nombre,
        "nombre_usuario": usuario.nombre_usuario,
        "tipo_usuario": _tipo(usuario.tipo_usuario),
        "activo": usuario.activo,
        "verificado": usuario.verificado,
    }


def _sesion_to_dict(sesion):
    return {
        "id_sesion": sesion.id_sesion,
        "id_grupo": sesion.id_grupo,
        "dia": _tipo(sesion.dia),
        "hora_inicio": sesion.hora_inicio.isoformat() if sesion.hora_inicio else None,
        "hora_fin": sesion.hora_fin.isoformat() if sesion.hora_fin else None,
        "aula": sesion.aula,
    }


def _require_admin(session_data: dict):
    require_role(session_data, ["ADMIN"])


def _require_academic_creator(session_data: dict):
    # Regla solicitada: cualquiera menos ALUMNO o INVITADO.
    require_role(session_data, ["ADMIN", "DOCENTE", "ADMINISTRATIVO"])


# Materias
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


# Grupos académicos
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


@router.get("/grupos/{id_grupo}/alumnos")
def listar_alumnos_grupo(id_grupo: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    usuarios = academico_controller.listar_alumnos_grupo(db, id_grupo)
    return {"status": "success", "data": [_usuario_to_dict(u) for u in usuarios]}


@router.post("/grupos/{id_grupo}/inscribir")
def inscribir_usuario(id_grupo: int, payload: InscripcionPayload, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    academico_controller.inscribir_usuario(db, id_grupo, payload.id_usuario)
    return {"status": "success", "message": "Usuario inscrito en el grupo"}


@router.post("/grupos/{id_grupo}/expulsar")
def expulsar_usuario(id_grupo: int, payload: InscripcionPayload, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    _require_academic_creator(session_data)
    academico_controller.expulsar_usuario(db, id_grupo, payload.id_usuario)
    return {"status": "success", "message": "Usuario removido del grupo"}


# Sesiones de clase
@router.get("/sesiones")
def listar_sesiones(db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_sesion_to_dict(s) for s in academico_controller.listar_sesiones(db)]}


@router.get("/sesiones/grupo/{id_grupo}")
def listar_sesiones_grupo(id_grupo: int, db: Session = Depends(get_db), session_data: dict = Depends(require_auth)):
    return {"status": "success", "data": [_sesion_to_dict(s) for s in academico_controller.listar_sesiones_grupo(db, id_grupo)]}


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
