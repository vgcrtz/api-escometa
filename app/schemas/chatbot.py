from pydantic import BaseModel, Field


class ChatbotMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=8000)


class ChatbotPreguntaRequest(BaseModel):
    pregunta: str = Field(..., min_length=1, max_length=2000)
    historial: list[ChatbotMessage] = Field(default_factory=list, max_length=12)
    usar_internet: bool = True


class ChatbotFuente(BaseModel):
    titulo: str | None = None
    url: str | None = None
    tipo: str = "web"


class ChatbotRespuestaData(BaseModel):
    respuesta: str
    fuentes: list[ChatbotFuente] = Field(default_factory=list)
    modelo: str | None = None
    uso_internet: bool = False
