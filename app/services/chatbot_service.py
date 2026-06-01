from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.academico import AlumnoMateriaGrupo, EstadoInscripcion, GrupoMateria, SesionClase
from app.models.comunicacion import Anuncio, AnuncioUsuario
from app.models.usuario import Usuario
from app.schemas.chatbot import ChatbotFuente, ChatbotMessage, ChatbotPreguntaRequest, ChatbotRespuestaData
from app.services.chatbot_knowledge import ESCOMETA_SYSTEM_CONTEXT

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - permite arrancar sin dependencia instalada hasta configurar IA
    OpenAI = None  # type: ignore[assignment]


SYSTEM_PROMPT = """
Eres el asistente virtual de ESCOMETA para usuarios de la Escuela Superior de Cómputo del IPN.
Responde en español claro, amable y útil.

Tu público principal son alumnos, docentes, administrativos, invitados y administradores usando la interfaz del sistema.

Reglas de precisión y seguridad:
1. Prioriza, en este orden: datos de sesión del usuario, datos internos del sistema, anuncios recibidos y fuentes oficiales de internet.
2. No inventes fechas, trámites, requisitos, docentes, horarios ni convocatorias. Si no hay evidencia suficiente, dilo de forma clara.
3. Para trámites escolares, recomienda confirmar con fuentes oficiales de ESCOM/IPN o con el área correspondiente.
4. No reveles información privada de otros usuarios. Usa solo el contexto que se te entrega.
5. Si la pregunta pide ejecutar una acción del sistema, explica los pasos disponibles en la interfaz; no finjas haber cambiado datos.
6. Cuando uses internet, incluye referencias al final si están disponibles.
7. Cuando uses anuncios internos, menciona que la información proviene de anuncios del sistema, sin exponer destinatarios.

Reglas de estilo para usuario final:
8. No menciones endpoints, rutas de API, métodos HTTP, JSON, cookies, nombres de tablas, nombres de campos técnicos ni comandos como GET, POST, PUT, DELETE, PATCH.
9. No digas frases como "según el contexto del sistema", "el contexto indica", "en el contexto disponible" o "para tu usuario con rol".
10. Traduce información técnica a instrucciones de interfaz. Por ejemplo:
   - En vez de "consulta GET /anuncios/mis-anuncios", di "entra al módulo de Anuncios".
   - En vez de "consulta GET /notificaciones", di "revisa el módulo de Notificaciones".
   - En vez de "id_grupo_materia", di "materia dentro de tu grupo".
11. Si no hay anuncios, responde algo como: "No encontré anuncios recientes para tu cuenta. Puedes revisar el módulo de Anuncios o tus Notificaciones dentro de ESCOMETA."
12. Solo puedes dar detalles técnicos si el usuario pide explícitamente ayuda como desarrollador, API, endpoints, backend, FastAPI, Postman, curl, SQL, integración o depuración.
""".strip()


def _role(session_data: dict[str, Any]) -> str:
    return str(session_data.get("tipo_usuario") or "INVITADO")


def _safe_user_context(db: Session, session_data: dict[str, Any]) -> str:
    tipo = _role(session_data)
    partes = [f"Rol actual del usuario: {tipo}."]

    id_usuario = session_data.get("id_usuario")
    if id_usuario:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == int(id_usuario)).first()
        if usuario:
            partes.append(f"Nombre: {usuario.nombre}.")
            partes.append(f"Nombre de usuario: {usuario.nombre_usuario}.")
            partes.append(f"Correo institucional: {usuario.correo}.")

    if tipo == "ALUMNO" and id_usuario:
        inscripciones = (
            db.query(AlumnoMateriaGrupo)
            .join(GrupoMateria, AlumnoMateriaGrupo.id_grupo_materia == GrupoMateria.id_grupo_materia)
            .options(
                joinedload(AlumnoMateriaGrupo.grupo_materia).joinedload(GrupoMateria.grupo),
                joinedload(AlumnoMateriaGrupo.grupo_materia).joinedload(GrupoMateria.materia),
                joinedload(AlumnoMateriaGrupo.grupo_materia).joinedload(GrupoMateria.sesiones),
            )
            .filter(
                AlumnoMateriaGrupo.id_alumno == int(id_usuario),
                AlumnoMateriaGrupo.estado == EstadoInscripcion.INSCRITO,
            )
            .limit(20)
            .all()
        )
        if inscripciones:
            partes.append("Materias inscritas del alumno:")
            for inscripcion in inscripciones:
                gm = inscripcion.grupo_materia
                sesiones = sorted(gm.sesiones or [], key=lambda s: (str(s.dia.value if hasattr(s.dia, "value") else s.dia), s.hora_inicio))
                sesiones_txt = "; ".join(
                    f"{s.dia.value if hasattr(s.dia, 'value') else s.dia} {s.hora_inicio}-{s.hora_fin} aula {s.aula or 'sin aula'}"
                    for s in sesiones[:5]
                ) or "sin sesiones registradas"
                partes.append(
                    f"- {gm.materia.nombre} en {gm.grupo.clave}, id_grupo_materia={gm.id_grupo_materia}, sesiones: {sesiones_txt}."
                )

    return "\n".join(partes)


def _announcement_context(db: Session, session_data: dict[str, Any]) -> str:
    """Incluye solo anuncios que el usuario puede conocer."""
    tipo = _role(session_data)
    id_usuario = session_data.get("id_usuario")
    limite = max(0, int(settings.CHATBOT_MAX_ANNOUNCEMENTS))

    if limite == 0:
        return "No se incluyeron anuncios internos."

    query = db.query(Anuncio).order_by(Anuncio.fecha.desc())

    if tipo == "INVITADO" or not id_usuario:
        return "El usuario invitado no tiene anuncios internos disponibles."

    if tipo not in {"ADMIN", "DOCENTE", "ADMINISTRATIVO"}:
        query = query.join(AnuncioUsuario, Anuncio.id_anuncio == AnuncioUsuario.id_anuncio).filter(
            AnuncioUsuario.id_usuario == int(id_usuario)
        )

    anuncios = query.limit(limite).all()
    if not anuncios:
        return "No hay anuncios internos disponibles para este usuario."

    partes = [f"Últimos {len(anuncios)} anuncios internos disponibles para el usuario:"]
    for anuncio in anuncios:
        fecha = anuncio.fecha.isoformat() if anuncio.fecha else "sin fecha"
        contenido = (anuncio.contenido or "").strip().replace("\n", " ")
        if len(contenido) > 1200:
            contenido = contenido[:1200] + "..."
        partes.append(f"- [{fecha}] {contenido}")
    return "\n".join(partes)


def _recent_sessions_context(db: Session) -> str:
    sesiones = (
        db.query(SesionClase)
        .options(
            joinedload(SesionClase.grupo_materia).joinedload(GrupoMateria.grupo),
            joinedload(SesionClase.grupo_materia).joinedload(GrupoMateria.materia),
        )
        .limit(30)
        .all()
    )
    if not sesiones:
        return "No hay sesiones de clase registradas en el sistema."

    partes = ["Muestra de sesiones registradas en el sistema:"]
    for sesion in sesiones[:15]:
        gm = sesion.grupo_materia
        partes.append(
            f"- {gm.materia.nombre} / {gm.grupo.clave}: {sesion.dia.value if hasattr(sesion.dia, 'value') else sesion.dia} "
            f"{sesion.hora_inicio}-{sesion.hora_fin}, aula {sesion.aula or 'sin aula'}."
        )
    return "\n".join(partes)


def _build_context(db: Session, session_data: dict[str, Any]) -> str:
    bloques = [
        "BASE DEL SISTEMA ESCOMETA:\n" + ESCOMETA_SYSTEM_CONTEXT,
        "CONTEXTO DEL USUARIO:\n" + _safe_user_context(db, session_data),
        "ANUNCIOS INTERNOS:\n" + _announcement_context(db, session_data),
        "SESIONES / HORARIOS DISPONIBLES:\n" + _recent_sessions_context(db),
    ]
    return "\n\n".join(bloques)


def _history_to_text(historial: list[ChatbotMessage]) -> str:
    if not historial:
        return "Sin historial previo."
    return "\n".join(f"{m.role}: {m.content}" for m in historial[-12:])


def _allowed_domains() -> list[str]:
    raw = getattr(settings, "CHATBOT_ALLOWED_WEB_DOMAINS", "") or ""
    return [d.strip() for d in raw.split(",") if d.strip()]


def _response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return {}


def _collect_sources(value: Any) -> list[ChatbotFuente]:
    """Extrae URLs de anotaciones y de `web_search_call.action.sources` si existen."""
    fuentes: list[ChatbotFuente] = []
    vistos: set[str] = set()

    def add(url: str | None, titulo: str | None, tipo: str = "web") -> None:
        if not url or url in vistos:
            return
        vistos.add(url)
        fuentes.append(ChatbotFuente(titulo=titulo, url=url, tipo=tipo))

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            url = node.get("url") or node.get("uri")
            title = node.get("title") or node.get("titulo") or node.get("name")
            if url:
                add(str(url), str(title) if title else None)
            for item in node.values():
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(value)
    return fuentes[:8]


def responder_chatbot(db: Session, session_data: dict[str, Any], payload: ChatbotPreguntaRequest) -> ChatbotRespuestaData:
    if OpenAI is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falta instalar la dependencia `openai`. Ejecuta: pip install -r requirements.txt",
        )

    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY no está configurada en el backend.",
        )

    contexto = _build_context(db, session_data)
    historial = _history_to_text(payload.historial)

    input_text = f"""
Contexto disponible:
{contexto}

Historial reciente del chat:
{historial}

Pregunta del usuario:
{payload.pregunta}
""".strip()

    tools: list[dict[str, Any]] = []
    uso_internet = bool(payload.usar_internet and settings.CHATBOT_ENABLE_WEB_SEARCH)
    if uso_internet:
        web_tool: dict[str, Any] = {
            "type": "web_search",
            "user_location": {
                "type": "approximate",
                "country": "MX",
                "city": "Ciudad de México",
                "region": "CDMX",
            },
        }
        domains = _allowed_domains()
        if domains:
            web_tool["filters"] = {"allowed_domains": domains}
        tools.append(web_tool)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        request_params = {
            "model": settings.OPENAI_MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": input_text,
            "max_output_tokens": 1400,
            "reasoning": {"effort": "low"},
            "text": {"verbosity": "medium"},
        }

        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"
            request_params["include"] = ["web_search_call.action.sources"]

        response = client.responses.create(**request_params)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo consultar el modelo de IA: {exc}",
        )

    data = _response_to_dict(response)
    texto = getattr(response, "output_text", None)
    if not texto:
        # Respaldo por si la versión del SDK no expone output_text.
        textos: list[str] = []
        for item in data.get("output", []) or []:
            if item.get("type") == "message":
                for content in item.get("content", []) or []:
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        textos.append(str(content["text"]))
        texto = "\n".join(textos).strip()

    if not texto:
        texto = "No pude generar una respuesta con la información disponible. Intenta reformular la pregunta."

    fuentes = _collect_sources(data)
    return ChatbotRespuestaData(
        respuesta=texto,
        fuentes=fuentes,
        modelo=settings.OPENAI_MODEL,
        uso_internet=uso_internet,
    )
