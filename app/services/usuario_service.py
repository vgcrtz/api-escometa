from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.usuario import Administrativo, Alumno, Docente, TipoUsuario, Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.utils.security import hash_password


TIPOS_VALIDOS = {"ALUMNO", "DOCENTE", "ADMINISTRATIVO", "ADMIN"}
TIPOS_REGISTRABLES_POR_ADMIN = TIPOS_VALIDOS


def listar_usuarios(db: Session) -> list[Usuario]:
    return (
        db.query(Usuario)
        .filter(Usuario.activo.is_(True))
        .order_by(Usuario.id_usuario.asc())
        .all()
    )


def obtener_usuario(db: Session, id_usuario: int) -> Usuario | None:
    return (
        db.query(Usuario)
        .options(
            joinedload(Usuario.alumno),
            joinedload(Usuario.docente),
            joinedload(Usuario.administrativo),
        )
        .filter(Usuario.id_usuario == id_usuario)
        .first()
    )


def buscar_por_correo(db: Session, correo: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.correo == correo).first()


def buscar_por_nombre_usuario(db: Session, nombre_usuario: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()


def _crear_detalle_por_rol(db: Session, usuario: Usuario, data: UsuarioCreate | UsuarioUpdate) -> None:
    tipo = usuario.tipo_usuario.value if hasattr(usuario.tipo_usuario, "value") else usuario.tipo_usuario

    if tipo == "ALUMNO":
        db.add(
            Alumno(
                id_usuario=usuario.id_usuario,
                boleta=getattr(data, "boleta", None),
                carrera=getattr(data, "carrera", None),
                semestre=getattr(data, "semestre", None),
                creditos=getattr(data, "creditos", None),
                carga=getattr(data, "carga", None),
            )
        )
    elif tipo == "DOCENTE":
        db.add(
            Docente(
                id_usuario=usuario.id_usuario,
                grado_academico=getattr(data, "grado_academico", None),
                departamento=getattr(data, "departamento", None),
            )
        )
    elif tipo == "ADMINISTRATIVO":
        db.add(
            Administrativo(
                id_usuario=usuario.id_usuario,
                area=getattr(data, "area", None),
                puesto=getattr(data, "puesto", None),
            )
        )


def crear_usuario(db: Session, payload: UsuarioCreate) -> Usuario:
    if payload.tipo_usuario not in TIPOS_REGISTRABLES_POR_ADMIN:
        raise ValueError("Tipo de usuario inválido")

    usuario = Usuario(
        correo=str(payload.correo),
        nombre=payload.nombre,
        nombre_usuario=payload.nombre_usuario,
        contraseña=hash_password(payload.contrasena),
        tipo_usuario=TipoUsuario(payload.tipo_usuario),
        activo=True,
        verificado=True if payload.tipo_usuario == "ADMIN" else False,
    )

    db.add(usuario)
    db.flush()
    _crear_detalle_por_rol(db, usuario, payload)
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_usuario(db: Session, usuario: Usuario, payload: UsuarioUpdate) -> Usuario:
    data = payload.model_dump(exclude_unset=True, by_alias=False)

    if "correo" in data and data["correo"] is not None:
        usuario.correo = str(data["correo"])
    if "nombre" in data and data["nombre"] is not None:
        usuario.nombre = data["nombre"]
    if "nombre_usuario" in data and data["nombre_usuario"] is not None:
        usuario.nombre_usuario = data["nombre_usuario"]
    if "contrasena" in data and data["contrasena"] is not None:
        usuario.contraseña = hash_password(data["contrasena"])
    if "tipo_usuario" in data and data["tipo_usuario"] is not None:
        if data["tipo_usuario"] not in TIPOS_VALIDOS:
            raise ValueError("Tipo de usuario inválido")
        usuario.tipo_usuario = TipoUsuario(data["tipo_usuario"])
    if "activo" in data and data["activo"] is not None:
        usuario.activo = data["activo"]
    if "verificado" in data and data["verificado"] is not None:
        usuario.verificado = data["verificado"]

    if usuario.alumno:
        for campo in ["boleta", "carrera", "semestre", "creditos", "carga"]:
            if campo in data and data[campo] is not None:
                setattr(usuario.alumno, campo, data[campo])

    if usuario.docente:
        for campo in ["grado_academico", "departamento"]:
            if campo in data and data[campo] is not None:
                setattr(usuario.docente, campo, data[campo])

    if usuario.administrativo:
        for campo in ["area", "puesto"]:
            if campo in data and data[campo] is not None:
                setattr(usuario.administrativo, campo, data[campo])

    db.commit()
    db.refresh(usuario)
    return usuario


def desactivar_usuario(db: Session, usuario: Usuario) -> Usuario:
    usuario.activo = False
    db.commit()
    db.refresh(usuario)
    return usuario


def eliminar_usuario(db: Session, usuario: Usuario) -> None:
    db.delete(usuario)
    db.commit()
