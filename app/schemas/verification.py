from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    correo: EmailStr
    codigo: str = Field(min_length=4, max_length=10)


class ResendCodeRequest(BaseModel):
    correo: EmailStr
