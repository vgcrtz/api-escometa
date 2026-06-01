from sqlalchemy.orm import Session

from app.schemas.academico import (
    GrupoCreate,
    GrupoMateriaCreate,
    GrupoMateriaUpdate,
    GrupoUpdate,
    MateriaCreate,
    MateriaUpdate,
    SesionCreate,
    SesionUpdate,
)
from app.services import academico_service


def listar_materias(db: Session):
    return academico_service.listar_materias(db)


def obtener_materia(db: Session, id_materia: int):
    return academico_service.obtener_materia(db, id_materia)


def crear_materia(db: Session, payload: MateriaCreate):
    return academico_service.crear_materia(db, payload)


def actualizar_materia(db: Session, id_materia: int, payload: MateriaUpdate):
    return academico_service.actualizar_materia(db, id_materia, payload)


def eliminar_materia(db: Session, id_materia: int):
    return academico_service.eliminar_materia(db, id_materia)


def listar_grupos(db: Session):
    return academico_service.listar_grupos(db)


def obtener_grupo(db: Session, id_grupo: int):
    return academico_service.obtener_grupo(db, id_grupo)


def crear_grupo(db: Session, payload: GrupoCreate):
    return academico_service.crear_grupo(db, payload)


def actualizar_grupo(db: Session, id_grupo: int, payload: GrupoUpdate):
    return academico_service.actualizar_grupo(db, id_grupo, payload)


def eliminar_grupo(db: Session, id_grupo: int):
    return academico_service.eliminar_grupo(db, id_grupo)


def listar_grupos_materia(db: Session):
    return academico_service.listar_grupos_materia(db)


def obtener_grupo_materia(db: Session, id_grupo_materia: int):
    return academico_service.obtener_grupo_materia(db, id_grupo_materia)


def listar_materias_de_grupo(db: Session, id_grupo: int):
    return academico_service.listar_materias_de_grupo(db, id_grupo)


def listar_grupos_de_materia(db: Session, id_materia: int):
    return academico_service.listar_grupos_de_materia(db, id_materia)


def crear_grupo_materia(db: Session, payload: GrupoMateriaCreate):
    return academico_service.crear_grupo_materia(db, payload)


def actualizar_grupo_materia(db: Session, id_grupo_materia: int, payload: GrupoMateriaUpdate):
    return academico_service.actualizar_grupo_materia(db, id_grupo_materia, payload)


def eliminar_grupo_materia(db: Session, id_grupo_materia: int):
    return academico_service.eliminar_grupo_materia(db, id_grupo_materia)


def listar_alumnos_grupo_materia(db: Session, id_grupo_materia: int):
    return academico_service.listar_alumnos_grupo_materia(db, id_grupo_materia)


def inscribir_usuario_grupo_materia(db: Session, id_grupo_materia: int, id_usuario: int):
    return academico_service.inscribir_usuario_grupo_materia(db, id_grupo_materia, id_usuario)


def expulsar_usuario_grupo_materia(db: Session, id_grupo_materia: int, id_usuario: int):
    return academico_service.expulsar_usuario_grupo_materia(db, id_grupo_materia, id_usuario)


def listar_materias_alumno(db: Session, id_usuario: int):
    return academico_service.listar_materias_alumno(db, id_usuario)


def listar_sesiones(db: Session):
    return academico_service.listar_sesiones(db)


def listar_sesiones_grupo_materia(db: Session, id_grupo_materia: int):
    return academico_service.listar_sesiones_grupo_materia(db, id_grupo_materia)


def crear_sesion(db: Session, payload: SesionCreate):
    return academico_service.crear_sesion(db, payload)


def actualizar_sesion(db: Session, id_sesion: int, payload: SesionUpdate):
    return academico_service.actualizar_sesion(db, id_sesion, payload)


def eliminar_sesion(db: Session, id_sesion: int):
    return academico_service.eliminar_sesion(db, id_sesion)
