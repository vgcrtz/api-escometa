from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academico import GrupoAcademico, Materia, SesionClase, UsuarioGrupo
from app.models.usuario import Usuario
from app.schemas.academico import (
    GrupoCreate,
    GrupoUpdate,
    MateriaCreate,
    MateriaUpdate,
    SesionCreate,
    SesionUpdate,
)


def _tipo(usuario: Usuario) -> str:
    return usuario.tipo_usuario.value if hasattr(usuario.tipo_usuario, "value") else str(usuario.tipo_usuario)


# Materias

def listar_materias(db: Session):
    return db.query(Materia).order_by(Materia.id_materia.asc()).all()


def obtener_materia(db: Session, id_materia: int) -> Materia:
    materia = db.query(Materia).filter(Materia.id_materia == id_materia).first()
    if not materia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    return materia


def crear_materia(db: Session, payload: MateriaCreate) -> Materia:
    materia = Materia(nombre=payload.nombre)
    db.add(materia)
    db.commit()
    db.refresh(materia)
    return materia


def actualizar_materia(db: Session, id_materia: int, payload: MateriaUpdate) -> Materia:
    materia = obtener_materia(db, id_materia)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(materia, key, value)
    db.commit()
    db.refresh(materia)
    return materia


def eliminar_materia(db: Session, id_materia: int) -> None:
    materia = obtener_materia(db, id_materia)
    db.delete(materia)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar la materia porque tiene grupos asociados",
        )


# Grupos

def listar_grupos(db: Session):
    return db.query(GrupoAcademico).order_by(GrupoAcademico.id_grupo.asc()).all()


def obtener_grupo(db: Session, id_grupo: int) -> GrupoAcademico:
    grupo = db.query(GrupoAcademico).filter(GrupoAcademico.id_grupo == id_grupo).first()
    if not grupo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    return grupo


def _validar_materia_y_docente(db: Session, id_materia: int, id_docente: int) -> None:
    obtener_materia(db, id_materia)
    docente = db.query(Usuario).filter(Usuario.id_usuario == id_docente).first()
    if not docente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Docente no encontrado")
    if _tipo(docente) != "DOCENTE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El id_docente debe pertenecer a un usuario DOCENTE")
    if not docente.activo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El docente está desactivado")


def crear_grupo(db: Session, payload: GrupoCreate) -> GrupoAcademico:
    _validar_materia_y_docente(db, payload.id_materia, payload.id_docente)
    grupo = GrupoAcademico(id_materia=payload.id_materia, id_docente=payload.id_docente)
    db.add(grupo)
    db.commit()
    db.refresh(grupo)
    return grupo


def actualizar_grupo(db: Session, id_grupo: int, payload: GrupoUpdate) -> GrupoAcademico:
    grupo = obtener_grupo(db, id_grupo)
    data = payload.model_dump(exclude_unset=True)
    id_materia = data.get("id_materia", grupo.id_materia)
    id_docente = data.get("id_docente", grupo.id_docente)
    _validar_materia_y_docente(db, id_materia, id_docente)
    for key, value in data.items():
        setattr(grupo, key, value)
    db.commit()
    db.refresh(grupo)
    return grupo


def eliminar_grupo(db: Session, id_grupo: int) -> None:
    grupo = obtener_grupo(db, id_grupo)
    db.delete(grupo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar el grupo porque tiene usuarios o sesiones asociadas",
        )


def listar_alumnos_grupo(db: Session, id_grupo: int):
    obtener_grupo(db, id_grupo)
    return (
        db.query(Usuario)
        .join(UsuarioGrupo, Usuario.id_usuario == UsuarioGrupo.id_usuario)
        .filter(UsuarioGrupo.id_grupo == id_grupo)
        .order_by(Usuario.id_usuario.asc())
        .all()
    )


def inscribir_usuario(db: Session, id_grupo: int, id_usuario: int) -> UsuarioGrupo:
    obtener_grupo(db, id_grupo)
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if _tipo(usuario) == "INVITADO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pueden inscribir invitados")

    existente = db.query(UsuarioGrupo).filter(
        UsuarioGrupo.id_grupo == id_grupo,
        UsuarioGrupo.id_usuario == id_usuario,
    ).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya está inscrito en el grupo")

    relacion = UsuarioGrupo(id_usuario=id_usuario, id_grupo=id_grupo)
    db.add(relacion)
    db.commit()
    return relacion


def expulsar_usuario(db: Session, id_grupo: int, id_usuario: int) -> None:
    relacion = db.query(UsuarioGrupo).filter(
        UsuarioGrupo.id_grupo == id_grupo,
        UsuarioGrupo.id_usuario == id_usuario,
    ).first()
    if not relacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no está inscrito en el grupo")
    db.delete(relacion)
    db.commit()


# Sesiones

def listar_sesiones(db: Session):
    return db.query(SesionClase).order_by(SesionClase.id_sesion.asc()).all()


def listar_sesiones_grupo(db: Session, id_grupo: int):
    obtener_grupo(db, id_grupo)
    return db.query(SesionClase).filter(SesionClase.id_grupo == id_grupo).order_by(SesionClase.id_sesion.asc()).all()


def obtener_sesion(db: Session, id_sesion: int) -> SesionClase:
    sesion = db.query(SesionClase).filter(SesionClase.id_sesion == id_sesion).first()
    if not sesion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")
    return sesion


def crear_sesion(db: Session, payload: SesionCreate) -> SesionClase:
    obtener_grupo(db, payload.id_grupo)
    if payload.hora_fin <= payload.hora_inicio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hora_fin debe ser mayor a hora_inicio")
    sesion = SesionClase(**payload.model_dump())
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


def actualizar_sesion(db: Session, id_sesion: int, payload: SesionUpdate) -> SesionClase:
    sesion = obtener_sesion(db, id_sesion)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(sesion, key, value)
    if sesion.hora_fin <= sesion.hora_inicio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hora_fin debe ser mayor a hora_inicio")
    db.commit()
    db.refresh(sesion)
    return sesion


def eliminar_sesion(db: Session, id_sesion: int) -> None:
    sesion = obtener_sesion(db, id_sesion)
    db.delete(sesion)
    db.commit()
