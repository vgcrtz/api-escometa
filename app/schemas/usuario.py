from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    correo: EmailStr
    nombre: str = Field(min_length=1, max_length=30)
    nombre_usuario: str = Field(min_length=1, max_length=30)
    tipo_usuario: str


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correo: EmailStr
    nombre: str = Field(min_length=1, max_length=30)
    nombre_usuario: str = Field(min_length=1, max_length=30)
    contrasena: str = Field(alias="contraseña", min_length=6, max_length=255)
    tipo_usuario: str

    boleta: Optional[str] = None
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    grado_academico: Optional[str] = None
    departamento: Optional[str] = None
    area: Optional[str] = None
    puesto: Optional[str] = None


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correo: Optional[EmailStr] = None
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=30)
    nombre_usuario: Optional[str] = Field(default=None, min_length=1, max_length=30)
    contrasena: Optional[str] = Field(default=None, alias="contraseña", min_length=6, max_length=255)
    tipo_usuario: Optional[str] = None
    activo: Optional[bool] = None
    verificado: Optional[bool] = None

    boleta: Optional[str] = None
    carrera: Optional[str] = None
    semestre: Optional[int] = None
    creditos: Optional[int] = None
    carga: Optional[int] = None
    grado_academico: Optional[str] = None
    departamento: Optional[str] = None
    area: Optional[str] = None
    puesto: Optional[str] = None


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    correo: EmailStr
    nombre: str
    nombre_usuario: str
    tipo_usuario: str
    activo: bool
    verificado: bool
