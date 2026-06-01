from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
import app.models  # noqa: F401 - registra todos los modelos en Base.metadata
from app.routes.auth import router as auth_router
from app.routes.usuarios import router as usuarios_router
from app.routes.academico import router as academico_router
from app.routes.asistencias import router as asistencias_router
from app.routes.comunicacion import router as comunicacion_router
from app.routes.chatbot import router as chatbot_router
from app.routes.chat import router as chat_router

app = FastAPI(title="ESCOMETA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(academico_router)
app.include_router(asistencias_router)
app.include_router(comunicacion_router)
app.include_router(chat_router)
app.include_router(chatbot_router)


@app.on_event("startup")
def startup() -> None:
    # Útil en desarrollo. En producción es mejor usar Alembic para migraciones.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "success", "message": "API funcionando"}