from sqlalchemy.orm import Session

from app.models.usuario import Administrativo, Alumno, Docente, TipoUsuario, Usuario
from app.schemas.auth import RegisterRequest
from app.services.verification_service import crear_codigo_verificacion
from app.utils.security import hash_password, verify_password

DOMINIOS_PERMITIDOS = {"ipn.mx", "alumno.ipn.mx", "egresado.ipn.mx"}


def get_email_domain(correo: str) -> str:
    return correo.split("@", 1)[1].lower() if "@" in correo else ""


def find_user_by_email(db: Session, correo: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.correo == correo).first()

def find_user_by_username(db: Session, nombre_usuario: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()


def create_user_with_role(db: Session, payload: RegisterRequest) -> Usuario:
    usuario = Usuario(
        correo=str(payload.correo),
        nombre=payload.nombre,
        nombre_usuario=payload.nombre_usuario,
        contraseña=hash_password(payload.contrasena),
        tipo_usuario=TipoUsuario(payload.tipo_usuario),
    )

    db.add(usuario)
    db.flush()  # obtiene id_usuario sin cerrar la transacción

    if payload.tipo_usuario == "ALUMNO":
        db.add(
            Alumno(
                id_usuario=usuario.id_usuario,
                boleta=payload.boleta,
                carrera=payload.carrera,
                semestre=payload.semestre,
            )
        )
    elif payload.tipo_usuario == "DOCENTE":
        db.add(
            Docente(
                id_usuario=usuario.id_usuario,
                grado_academico=payload.grado_academico,
                departamento=payload.departamento,
            )
        )
    elif payload.tipo_usuario == "ADMINISTRATIVO":
        db.add(
            Administrativo(
                id_usuario=usuario.id_usuario,
                area=payload.area,
                puesto=payload.puesto,
            )
        )

    # Genera el primer código de verificación durante el registro.
    crear_codigo_verificacion(db, usuario.id_usuario)

    db.commit()
    db.refresh(usuario)
    return usuario


def authenticate_user(db: Session, correo: str, password: str) -> Usuario | None:
    usuario = find_user_by_email(db, correo)
    if not usuario:
          return None
    if not verify_password(password, usuario.contraseña):
        return None
    return usuario
