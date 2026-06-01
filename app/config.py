from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "escometa"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    MAIL_FROM: str = "no-reply@escometa.local"
    MAIL_FROM_NAME: str = "Sistema ESCOMETA"

    SCHOOL_LATITUDE: float = 19.5048
    SCHOOL_LONGITUDE: float = -99.1463
    ATTENDANCE_RADIUS_METERS: float = 150.0

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.5"
    CHATBOT_ENABLE_WEB_SEARCH: bool = True
    CHATBOT_MAX_ANNOUNCEMENTS: int = 8
    CHATBOT_ALLOWED_WEB_DOMAINS: str = "ipn.mx,escom.ipn.mx,www.ipn.mx"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()
