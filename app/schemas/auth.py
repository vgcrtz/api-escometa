from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

TipoRegistro = Literal["ALUMNO", "DOCENTE", "ADMINISTRATIVO"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correo: EmailStr
    nombre: str = Field(min_length=1, max_length=30)
    nombre_usuario: str = Field(min_length=1, max_length=30)
    contrasena: str = Field(alias="contraseña", min_length=6, max_length=255)
    tipo_usuario: TipoRegistro

    foto_perfil_url: str | None = None

    # Datos opcionales según rol
    boleta: Optional[str] = None
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    grado_academico: Optional[str] = None
    departamento: Optional[str] = None
    area: Optional[str] = None
    puesto: Optional[str] = None


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correo: EmailStr
    contrasena: str = Field(alias="contraseña", min_length=1)


class AuthSession(BaseModel):
    id_usuario: int
    correo: EmailStr
    tipo_usuario: str
    nombre: Optional[str] = None
    nombre_usuario: Optional[str] = None
    foto_perfil_url: str | None = None


class ApiResponse(BaseModel):
    status: str
    message: str | None = None
    data: dict | None = None
