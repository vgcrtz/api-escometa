from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers import chatbot_controller
from app.database import get_db
from app.middleware.auth import require_auth
from app.schemas.chatbot import ChatbotPreguntaRequest

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/preguntar")
def preguntar_chatbot(
    payload: ChatbotPreguntaRequest,
    db: Session = Depends(get_db),
    session_data: dict = Depends(require_auth),
):
    data = chatbot_controller.preguntar(db, session_data, payload)
    return {
        "status": "success",
        "message": "Respuesta generada",
        "data": data.model_dump(),
    }
