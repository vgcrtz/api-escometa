from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.controllers import usuario_controller
from app.database import get_db
from app.middleware.auth import require_admin, require_auth
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.schemas.media import FotoPerfilUpdate
from app.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _usuario_to_dict(usuario):
    tipo = usuario.tipo_usuario.value if hasattr(usuario.tipo_usuario, "value") else usuario.tipo_usuario

    data = {
        "id_usuario": usuario.id_usuario,
        "correo": usuario.correo,
        "nombre": usuario.nombre,
        "nombre_usuario": usuario.nombre_usuario,
        "tipo_usuario": tipo,
        "activo": usuario.activo,
        "verificado": usuario.verificado,
        "fecha_registro": usuario.fecha_registro.isoformat() if usuario.fecha_registro else None,
    }

    if usuario.alumno:
        data["alumno"] = {
            "boleta": usuario.alumno.boleta,
            "carrera": usuario.alumno.carrera,
            "semestre": usuario.alumno.semestre,
            "creditos": usuario.alumno.creditos,
            "carga": usuario.alumno.carga,
        }
    if usuario.docente:
        data["docente"] = {
            "grado_academico": usuario.docente.grado_academico,
            "departamento": usuario.docente.departamento,
        }
    if usuario.administrativo:
        data["administrativo"] = {
            "area": usuario.administrativo.area,
            "puesto": usuario.administrativo.puesto,
        }

    return data


@router.get("")
def index(
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_admin(session_data)
    usuarios = usuario_controller.index(db)
    return {
        "status": "success",
        "data": [_usuario_to_dict(usuario) for usuario in usuarios],
    }


@router.get("/{id_usuario}")
def show(
    id_usuario: int,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    # Un usuario puede consultarse a sí mismo; ADMIN puede consultar a cualquiera.
    if session_data.get("tipo_usuario") != "ADMIN" and int(session_data.get("id_usuario", -1)) != id_usuario:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tienes acceso a este recurso")

    usuario = usuario_controller.show(db, id_usuario)
    return {"status": "success", "data": _usuario_to_dict(usuario)}


@router.post("", status_code=status.HTTP_201_CREATED)
def store(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_admin(session_data)
    usuario = usuario_controller.store(db, payload)
    return {
        "status": "success",
        "message": "Usuario creado correctamente",
        "data": _usuario_to_dict(usuario),
    }


@router.put("/{id_usuario}")
def update(
    id_usuario: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_admin(session_data)
    usuario = usuario_controller.update(db, id_usuario, payload)
    return {
        "status": "success",
        "message": "Usuario actualizado",
        "data": _usuario_to_dict(usuario),
    }


@router.delete("/{id_usuario}")
def destroy(
    id_usuario: int,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    require_admin(session_data)

    if force:
        usuario_controller.delete(db, id_usuario)
        return {"status": "success", "message": "Usuario eliminado"}

    usuario = usuario_controller.destroy(db, id_usuario)
    return {
        "status": "success",
        "message": "Usuario desactivado",
        "data": _usuario_to_dict(usuario),
    }

@router.put("/me/foto")
def actualizar_foto_perfil(
    payload: FotoPerfilUpdate,
    db: Session = Depends(get_db),
    session: dict = Depends(require_auth)
):
    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == session["id_usuario"]
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.foto_perfil_url = str(payload.foto_perfil_url)

    db.commit()
    db.refresh(usuario)

    return {
        "status": "success",
        "message": "Foto de perfil actualizada",
        "data": {
            "id_usuario": usuario.id_usuario,
            "foto_perfil_url": usuario.foto_perfil_url
        }
    }