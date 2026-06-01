from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.academico import AlumnoMateriaGrupo, EstadoInscripcion, GrupoAcademico, GrupoMateria, Materia, SesionClase
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


def _not_found(message: str):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _conflict(message: str):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _bad_request(message: str):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def _exists(db: Session, table: str, field: str, value: int) -> bool:
    result = db.execute(text(f"SELECT 1 FROM {table} WHERE {field} = :value LIMIT 1"), {"value": value}).first()
    return result is not None


def _get_grupo_materia_model(db: Session, id_grupo_materia: int) -> GrupoMateria:
    grupo_materia = db.get(GrupoMateria, id_grupo_materia)
    if not grupo_materia:
        _not_found("Materia-grupo no encontrada")
    return grupo_materia


def _grupo_materia_detalle(db: Session, where_sql: str = "", params: dict | None = None):
    query = """
        SELECT
            id_grupo_materia,
            id_grupo,
            grupo,
            carrera,
            semestre,
            turno,
            id_materia,
            materia,
            id_docente,
            docente,
            cupo
        FROM VistaGrupoMateriaDetalle
    """
    if where_sql:
        query += f" WHERE {where_sql}"
    query += " ORDER BY grupo, materia, docente"
    return db.execute(text(query), params or {}).mappings().all()


def listar_materias(db: Session):
    return db.query(Materia).order_by(Materia.nombre).all()


def obtener_materia(db: Session, id_materia: int):
    materia = db.get(Materia, id_materia)
    if not materia:
        _not_found("Materia no encontrada")
    return materia


def crear_materia(db: Session, payload: MateriaCreate):
    materia = Materia(nombre=payload.nombre)
    db.add(materia)
    db.commit()
    db.refresh(materia)
    return materia


def actualizar_materia(db: Session, id_materia: int, payload: MateriaUpdate):
    materia = obtener_materia(db, id_materia)
    if payload.nombre is not None:
        materia.nombre = payload.nombre
    db.commit()
    db.refresh(materia)
    return materia


def eliminar_materia(db: Session, id_materia: int):
    materia = obtener_materia(db, id_materia)
    total_grupos = db.query(GrupoMateria).filter(GrupoMateria.id_materia == id_materia).count()
    if total_grupos:
        _conflict("No se puede eliminar la materia porque está ofertada en uno o más grupos")
    db.delete(materia)
    db.commit()


def listar_grupos(db: Session):
    return db.query(GrupoAcademico).order_by(GrupoAcademico.clave).all()


def obtener_grupo(db: Session, id_grupo: int):
    grupo = db.get(GrupoAcademico, id_grupo)
    if not grupo:
        _not_found("Grupo académico no encontrado")
    return grupo


def crear_grupo(db: Session, payload: GrupoCreate):
    grupo = GrupoAcademico(
        clave=payload.clave,
        carrera=payload.carrera,
        semestre=payload.semestre,
        turno=payload.turno,
    )
    db.add(grupo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _conflict("Ya existe un grupo académico con esa clave, carrera y semestre")
    db.refresh(grupo)
    return grupo


def actualizar_grupo(db: Session, id_grupo: int, payload: GrupoUpdate):
    grupo = obtener_grupo(db, id_grupo)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(grupo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _conflict("Ya existe un grupo académico con esa clave, carrera y semestre")
    db.refresh(grupo)
    return grupo


def eliminar_grupo(db: Session, id_grupo: int):
    grupo = obtener_grupo(db, id_grupo)
    total_materias = db.query(GrupoMateria).filter(GrupoMateria.id_grupo == id_grupo).count()
    if total_materias:
        _conflict("No se puede eliminar el grupo porque tiene materias ofertadas")
    db.delete(grupo)
    db.commit()


def listar_grupos_materia(db: Session):
    return _grupo_materia_detalle(db)


def obtener_grupo_materia(db: Session, id_grupo_materia: int):
    filas = _grupo_materia_detalle(db, "id_grupo_materia = :id_grupo_materia", {"id_grupo_materia": id_grupo_materia})
    if not filas:
        _not_found("Materia-grupo no encontrada")
    return filas[0]


def listar_materias_de_grupo(db: Session, id_grupo: int):
    obtener_grupo(db, id_grupo)
    return _grupo_materia_detalle(db, "id_grupo = :id_grupo", {"id_grupo": id_grupo})


def listar_grupos_de_materia(db: Session, id_materia: int):
    obtener_materia(db, id_materia)
    return _grupo_materia_detalle(db, "id_materia = :id_materia", {"id_materia": id_materia})


def crear_grupo_materia(db: Session, payload: GrupoMateriaCreate):
    obtener_grupo(db, payload.id_grupo)
    obtener_materia(db, payload.id_materia)
    if not _exists(db, "Docente", "id_usuario", payload.id_docente):
        _bad_request("El id_docente debe pertenecer a un usuario DOCENTE")

    grupo_materia = GrupoMateria(
        id_grupo=payload.id_grupo,
        id_materia=payload.id_materia,
        id_docente=payload.id_docente,
        cupo=payload.cupo,
    )
    db.add(grupo_materia)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _conflict("La materia ya está ofertada en ese grupo con ese docente")
    return obtener_grupo_materia(db, grupo_materia.id_grupo_materia)


def actualizar_grupo_materia(db: Session, id_grupo_materia: int, payload: GrupoMateriaUpdate):
    grupo_materia = _get_grupo_materia_model(db, id_grupo_materia)
    data = payload.model_dump(exclude_unset=True)

    if "id_grupo" in data and data["id_grupo"] is not None:
        obtener_grupo(db, data["id_grupo"])
    if "id_materia" in data and data["id_materia"] is not None:
        obtener_materia(db, data["id_materia"])
        if data["id_materia"] != grupo_materia.id_materia:
            total_inscritos = db.query(AlumnoMateriaGrupo).filter(
                AlumnoMateriaGrupo.id_grupo_materia == id_grupo_materia
            ).count()
            if total_inscritos:
                _conflict("No se puede cambiar la materia porque ya tiene alumnos inscritos")
    if "id_docente" in data and data["id_docente"] is not None:
        if not _exists(db, "Docente", "id_usuario", data["id_docente"]):
            _bad_request("El id_docente debe pertenecer a un usuario DOCENTE")

    for campo, valor in data.items():
        setattr(grupo_materia, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _conflict("La materia ya está ofertada en ese grupo con ese docente")
    return obtener_grupo_materia(db, id_grupo_materia)


def eliminar_grupo_materia(db: Session, id_grupo_materia: int):
    grupo_materia = _get_grupo_materia_model(db, id_grupo_materia)
    total_alumnos = db.query(AlumnoMateriaGrupo).filter(AlumnoMateriaGrupo.id_grupo_materia == id_grupo_materia).count()
    total_sesiones = db.query(SesionClase).filter(SesionClase.id_grupo_materia == id_grupo_materia).count()
    if total_alumnos or total_sesiones:
        _conflict("No se puede eliminar la materia-grupo porque tiene alumnos o sesiones asociadas")
    db.delete(grupo_materia)
    db.commit()


def listar_alumnos_grupo_materia(db: Session, id_grupo_materia: int):
    _get_grupo_materia_model(db, id_grupo_materia)
    query = """
        SELECT
            u.id_usuario,
            u.correo,
            u.nombre,
            u.nombre_usuario,
            u.tipo_usuario,
            u.activo,
            u.verificado,
            amg.fecha_inscripcion,
            amg.estado
        FROM Alumno_MateriaGrupo amg
        INNER JOIN Usuario u ON u.id_usuario = amg.id_alumno
        WHERE amg.id_grupo_materia = :id_grupo_materia
        ORDER BY u.nombre
    """
    return db.execute(text(query), {"id_grupo_materia": id_grupo_materia}).mappings().all()


def inscribir_usuario_grupo_materia(db: Session, id_grupo_materia: int, id_usuario: int):
    grupo_materia = _get_grupo_materia_model(db, id_grupo_materia)
    if not _exists(db, "Alumno", "id_usuario", id_usuario):
        _bad_request("El id_usuario debe pertenecer a un usuario ALUMNO")

    existente_misma_materia = db.query(AlumnoMateriaGrupo).filter(
        AlumnoMateriaGrupo.id_alumno == id_usuario,
        AlumnoMateriaGrupo.id_materia == grupo_materia.id_materia,
    ).first()

    if existente_misma_materia:
        if existente_misma_materia.id_grupo_materia == id_grupo_materia:
            _conflict("El alumno ya está inscrito en esta materia-grupo")
        _conflict("El alumno ya está inscrito en esta materia dentro de otro grupo")

    inscripcion = AlumnoMateriaGrupo(
        id_alumno=id_usuario,
        id_grupo_materia=id_grupo_materia,
        id_materia=grupo_materia.id_materia,
        estado=EstadoInscripcion.INSCRITO,
    )
    db.add(inscripcion)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _conflict("No se pudo completar la inscripción por conflicto de datos")
    return inscripcion


def expulsar_usuario_grupo_materia(db: Session, id_grupo_materia: int, id_usuario: int):
    _get_grupo_materia_model(db, id_grupo_materia)
    inscripcion = db.query(AlumnoMateriaGrupo).filter(
        AlumnoMateriaGrupo.id_alumno == id_usuario,
        AlumnoMateriaGrupo.id_grupo_materia == id_grupo_materia,
    ).first()
    if not inscripcion:
        _not_found("El alumno no está inscrito en esta materia-grupo")
    db.delete(inscripcion)
    db.commit()


def listar_materias_alumno(db: Session, id_usuario: int):
    if not _exists(db, "Alumno", "id_usuario", id_usuario):
        _bad_request("El id_usuario debe pertenecer a un usuario ALUMNO")
    query = """
        SELECT
            id_alumno,
            alumno,
            correo,
            id_grupo_materia,
            id_grupo,
            grupo,
            id_materia,
            materia,
            id_docente,
            docente,
            fecha_inscripcion,
            estado
        FROM VistaAlumnoMaterias
        WHERE id_alumno = :id_usuario
        ORDER BY grupo, materia
    """
    return db.execute(text(query), {"id_usuario": id_usuario}).mappings().all()


def listar_sesiones(db: Session):
    return db.query(SesionClase).options(
        selectinload(SesionClase.grupo_materia).selectinload(GrupoMateria.grupo),
        selectinload(SesionClase.grupo_materia).selectinload(GrupoMateria.materia),
    ).order_by(SesionClase.dia, SesionClase.hora_inicio).all()


def listar_sesiones_grupo_materia(db: Session, id_grupo_materia: int):
    _get_grupo_materia_model(db, id_grupo_materia)
    return db.query(SesionClase).options(
        selectinload(SesionClase.grupo_materia).selectinload(GrupoMateria.grupo),
        selectinload(SesionClase.grupo_materia).selectinload(GrupoMateria.materia),
    ).filter(SesionClase.id_grupo_materia == id_grupo_materia).order_by(SesionClase.dia, SesionClase.hora_inicio).all()


def crear_sesion(db: Session, payload: SesionCreate):
    if payload.hora_fin <= payload.hora_inicio:
        _bad_request("hora_fin debe ser mayor a hora_inicio")
    _get_grupo_materia_model(db, payload.id_grupo_materia)
    sesion = SesionClase(
        id_grupo_materia=payload.id_grupo_materia,
        dia=payload.dia,
        hora_inicio=payload.hora_inicio,
        hora_fin=payload.hora_fin,
        aula=payload.aula,
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


def actualizar_sesion(db: Session, id_sesion: int, payload: SesionUpdate):
    sesion = db.get(SesionClase, id_sesion)
    if not sesion:
        _not_found("Sesión no encontrada")

    data = payload.model_dump(exclude_unset=True)
    if "id_grupo_materia" in data and data["id_grupo_materia"] is not None:
        _get_grupo_materia_model(db, data["id_grupo_materia"])

    hora_inicio = data.get("hora_inicio", sesion.hora_inicio)
    hora_fin = data.get("hora_fin", sesion.hora_fin)
    if hora_fin <= hora_inicio:
        _bad_request("hora_fin debe ser mayor a hora_inicio")

    for campo, valor in data.items():
        setattr(sesion, campo, valor)

    db.commit()
    db.refresh(sesion)
    return sesion


def eliminar_sesion(db: Session, id_sesion: int):
    sesion = db.get(SesionClase, id_sesion)
    if not sesion:
        _not_found("Sesión no encontrada")
    db.delete(sesion)
    db.commit()
