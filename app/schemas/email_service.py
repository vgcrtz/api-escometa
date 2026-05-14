from email.message import EmailMessage
import smtplib

from app.config import settings


class EmailNotConfiguredError(RuntimeError):
    pass


def enviar_codigo_verificacion(correo: str, codigo: str) -> None:
    """Envía el código de verificación por SMTP.

    En desarrollo, si no configuras SMTP_USER o SMTP_PASSWORD, no detiene el flujo:
    imprime el código en consola para que puedas probar la API sin correo real.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[DEV] Código de verificación para {correo}: {codigo}")
        return

    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    message["To"] = correo
    message["Subject"] = "Verificación de cuenta"
    message.set_content(
        f"Tu código de verificación es: {codigo}\n\n"
        "Este código expira en 10 minutos."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)
