from sqlalchemy.orm import Session

from app.schemas.chatbot import ChatbotPreguntaRequest
from app.services import chatbot_service


def preguntar(db: Session, session_data: dict, payload: ChatbotPreguntaRequest):
    return chatbot_service.responder_chatbot(db, session_data, payload)
