from datetime import datetime, timedelta
import random

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.verificacion import VerificacionCorreo


def generar_codigo() -> str:
    return str(random.randint(100000, 999999))


def invalidar_codigos_previos(db: Session, id_usuario: int) -> None:
    db.query(VerificacionCorreo).filter(
        VerificacionCorreo.id_usuario == id_usuario,
        VerificacionCorreo.usado == False,  # noqa: E712
    ).update({"usado": True}, synchronize_session=False)


def crear_codigo_verificacion(db: Session, id_usuario: int) -> VerificacionCorreo:
    codigo = generar_codigo()
    registro = VerificacionCorreo(
        id_usuario=id_usuario,
        codigo=codigo,
        expiracion=datetime.now() + timedelta(minutes=10),
        usado=False,
    )
    db.add(registro)
    db.flush()
    return registro


def crear_y_guardar_codigo(db: Session, id_usuario: int) -> VerificacionCorreo:
    invalidar_codigos_previos(db, id_usuario)
    registro = crear_codigo_verificacion(db, id_usuario)
    db.commit()
    db.refresh(registro)
    return registro


def buscar_codigo_valido(db: Session, id_usuario: int, codigo: str) -> VerificacionCorreo | None:
    return (
        db.query(VerificacionCorreo)
        .filter(
            VerificacionCorreo.id_usuario == id_usuario,
            VerificacionCorreo.codigo == codigo,
            VerificacionCorreo.usado == False,  # noqa: E712
            VerificacionCorreo.expiracion > datetime.now(),
        )
        .first()
    )


def marcar_codigo_usado(db: Session, registro: VerificacionCorreo) -> None:
    registro.usado = True
    db.add(registro)


def marcar_usuario_verificado(db: Session, usuario: Usuario) -> None:
    usuario.verificado = True
    db.add(usuario)
