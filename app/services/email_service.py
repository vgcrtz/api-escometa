from email.message import EmailMessage
import smtplib

from app.config import settings


class EmailNotConfiguredError(RuntimeError):
    pass

def enviar_codigo_verificacion(correo: str, codigo: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[DEV] Código de verificación para {correo}: {codigo}")
        return

    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    message["To"] = correo
    message["Subject"] = f"Código ESCOMETA: {codigo}"

    message.set_content(
        f"""
    ESCOMETA
    Verificación de cuenta

    Tu código de verificación es:

        {codigo}

    Este código expirará en 10 minutos.

    Si no solicitaste este código, puedes ignorar este correo.
    """.strip()
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)
