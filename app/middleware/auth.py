import json
from typing import Any

from fastapi import Cookie, HTTPException, status

COOKIE_NAME = "session"


def _decode_session_cookie(session: str | None) -> dict[str, Any] | None:
    if not session:
        return None

    try:
        data = json.loads(session)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    return data


def optional_auth(session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict[str, Any] | None:
    return _decode_session_cookie(session)


def require_auth(session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict[str, Any]:
    data = _decode_session_cookie(session)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    return data


def require_user(session_data: dict[str, Any] = None) -> dict[str, Any]:
    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    if session_data.get("tipo_usuario") == "INVITADO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para usuarios registrados",
        )

    return session_data


def require_guest(session_data: dict[str, Any]) -> dict[str, Any]:
    if session_data.get("tipo_usuario") != "INVITADO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para invitados",
        )

    return session_data


def require_role(session_data: dict[str, Any], roles: list[str]) -> dict[str, Any]:
    require_user(session_data)

    if session_data.get("tipo_usuario") not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para esta acción",
        )

    return session_data


def require_admin(session_data: dict[str, Any]) -> dict[str, Any]:
    return require_role(session_data, ["ADMIN"])


def require_ownership(session_data: dict[str, Any], resource_user_id: int) -> dict[str, Any]:
    require_user(session_data)

    if int(session_data.get("id_usuario", -1)) != int(resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este recurso",
        )

    return session_data
