from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
import app.models  # noqa: F401 - registra todos los modelos en Base.metadata
from app.routes.auth import router as auth_router

app = FastAPI(title="ESCOMETA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
def startup() -> None:
    # Útil en desarrollo. En producción es mejor usar Alembic para migraciones.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "success", "message": "API funcionando"}
