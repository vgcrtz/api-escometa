from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services import usuario_service


def index(db: Session):
    return usuario_service.listar_usuarios(db)


def show(db: Session, id_usuario: int):
    usuario = usuario_service.obtener_usuario(db, id_usuario)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def store(db: Session, payload: UsuarioCreate):
    if usuario_service.buscar_por_correo(db, str(payload.correo)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    if usuario_service.buscar_por_nombre_usuario(db, payload.nombre_usuario):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya está registrado")

    try:
        return usuario_service.crear_usuario(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo o nombre de usuario ya está registrado")
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear usuario: {exc}")


def update(db: Session, id_usuario: int, payload: UsuarioUpdate):
    usuario = show(db, id_usuario)

    try:
        return usuario_service.actualizar_usuario(db, usuario, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo o nombre de usuario ya está registrado")
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar usuario: {exc}")


def destroy(db: Session, id_usuario: int):
    usuario = show(db, id_usuario)
    return usuario_service.desactivar_usuario(db, usuario)


def delete(db: Session, id_usuario: int):
    usuario = show(db, id_usuario)
    usuario_service.eliminar_usuario(db, usuario)
