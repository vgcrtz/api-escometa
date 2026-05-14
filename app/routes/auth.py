import json
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import optional_auth
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.verification import ResendCodeRequest, VerifyEmailRequest
from app.services.auth_service import (
    DOMINIOS_PERMITIDOS,
    authenticate_user,
    create_user_with_role,
    find_user_by_email,
    find_user_by_username,
    get_email_domain,
)
from app.services.email_service import enviar_codigo_verificacion
from app.services.verification_service import (
    buscar_codigo_valido,
    crear_y_guardar_codigo,
    marcar_codigo_usado,
    marcar_usuario_verificado,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

COOKIE_NAME = "session"
COOKIE_MAX_AGE = 60 * 60 * 24
GUEST_COOKIE_MAX_AGE = 60 * 60


def build_session_data(usuario) -> dict:
    return {
        "id_usuario": usuario.id_usuario,
        "correo": usuario.correo,
        "nombre": usuario.nombre,
        "nombre_usuario": usuario.nombre_usuario,
        "tipo_usuario": usuario.tipo_usuario.value if hasattr(usuario.tipo_usuario, "value") else usuario.tipo_usuario,
        "verificado": bool(usuario.verificado),
    }


def set_session_cookie(response: Response, session_data: dict, max_age: int = COOKIE_MAX_AGE) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=json.dumps(session_data, ensure_ascii=False),
        max_age=max_age,
        httponly=True,
        secure=False,  # en producción usar True con HTTPS
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=False,  # en producción usar True con HTTPS
        samesite="lax",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if payload.tipo_usuario == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes registrarte como administrador",
        )

    dominio = get_email_domain(str(payload.correo))
    if dominio not in DOMINIOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dominio de correo no permitido",
        )

    if find_user_by_email(db, str(payload.correo)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado",
        )

    if find_user_by_username(db, payload.nombre_usuario):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está registrado",
        )

    try:
        usuario = create_user_with_role(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo o nombre de usuario ya está registrado",
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar: {exc}",
        )

    # Envía el último código activo generado durante el registro.
    codigo_activo = usuario.verificacion_codigos[-1].codigo if usuario.verificacion_codigos else None
    if codigo_activo:
        enviar_codigo_verificacion(usuario.correo, codigo_activo)

    session_data = build_session_data(usuario)
    set_session_cookie(response, session_data)

    return {
        "status": "success",
        "message": "Usuario registrado correctamente. Código de verificación enviado.",
        "data": session_data,
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    usuario = authenticate_user(db, str(payload.correo), payload.contrasena)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    if not usuario.verificado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta no verificada. Verifica tu correo antes de iniciar sesión",
        )

    session_data = build_session_data(usuario)
    set_session_cookie(response, session_data)

    return {
        "status": "success",
        "message": "Login exitoso",
        "data": session_data,
    }


@router.post("/guest")
def guest(response: Response):
    session_data = {
        "id_usuario": None,
        "guest_id": "guest_" + secrets.token_hex(8),
        "tipo_usuario": "INVITADO",
    }

    set_session_cookie(response, session_data, max_age=GUEST_COOKIE_MAX_AGE)

    return {
        "status": "success",
        "message": "Sesión como invitado creada",
        "data": session_data,
    }


@router.get("/me")
def me(session_data: dict | None = Depends(optional_auth)):
    if not session_data:
        return {
            "status": "success",
            "authenticated": False,
            "data": None,
        }

    if session_data.get("tipo_usuario") == "INVITADO":
        return {
            "status": "success",
            "authenticated": True,
            "isGuest": True,
            "data": {
                "guest_id": session_data.get("guest_id"),
                "tipo_usuario": "INVITADO",
            },
        }

    return {
        "status": "success",
        "authenticated": True,
        "isGuest": False,
        "data": {
            "id_usuario": session_data.get("id_usuario"),
            "correo": session_data.get("correo"),
            "nombre": session_data.get("nombre"),
            "nombre_usuario": session_data.get("nombre_usuario"),
            "tipo_usuario": session_data.get("tipo_usuario"),
        },
    }


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    usuario = find_user_by_email(db, str(payload.correo))

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if usuario.verificado:
        return {
            "status": "success",
            "message": "La cuenta ya estaba verificada",
        }

    registro = buscar_codigo_valido(db, usuario.id_usuario, payload.codigo)

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o expirado",
        )

    marcar_codigo_usado(db, registro)
    marcar_usuario_verificado(db, usuario)
    db.commit()

    return {
        "status": "success",
        "message": "Cuenta verificada",
    }


@router.post("/resend-code")
def resend_code(payload: ResendCodeRequest, db: Session = Depends(get_db)):
    usuario = find_user_by_email(db, str(payload.correo))

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if usuario.verificado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya está verificado",
        )

    registro = crear_y_guardar_codigo(db, usuario.id_usuario)
    enviar_codigo_verificacion(usuario.correo, registro.codigo)

    return {
        "status": "success",
        "message": "Código reenviado",
    }


@router.post("/logout")
def logout(response: Response):
    clear_session_cookie(response)

    return {
        "status": "success",
        "message": "Sesión cerrada correctamente",
    }
