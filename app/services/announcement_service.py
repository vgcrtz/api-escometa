from datetime import datetime
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.anuncio import Anuncio
from app.models.anuncio_imagen import AnuncioImagen
from app.models.announcement_target import AnuncioTarget
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario
from app.schemas.announcement import AnnouncementCreate, AnnouncementTargetCreate

try:
    from app.models.academico import AlumnoMateriaGrupo, GrupoMateria
except Exception:  # Keep import-safe while academic migration is being applied.
    AlumnoMateriaGrupo = None
    GrupoMateria = None

try:
    from app.models.anuncio_destinatario import AnuncioDestinatario
except Exception:
    AnuncioDestinatario = None


STAFF_ROLES = {"ADMIN", "DOCENTE", "ADMINISTRATIVO"}
IMPORTANT_PRIORITIES = {"ALTA", "URGENTE"}
IMPORTANT_CATEGORIES = {"ACADEMICA", "TRAMITES", "EVENTO", "EMERGENCIA", "SISTEMA"}
PRIORITY_ORDER = {
    "URGENTE": 4,
    "ALTA": 3,
    "NORMAL": 2,
    "BAJA": 1,
}


class AnnouncementService:
    @staticmethod
    def create_announcement(db: Session, payload: AnnouncementCreate, sender: Usuario) -> dict:
        AnnouncementService._ensure_staff(sender)

        notice = Anuncio(
            titulo=payload.titulo,
            contenido=payload.contenido,
            categoria=payload.categoria,
            prioridad=payload.prioridad,
            fijado=payload.fijado,
            activo=payload.activo,
            visible_desde=payload.visible_desde,
            visible_hasta=payload.visible_hasta,
            id_emisor=sender.id_usuario,
        )
        db.add(notice)
        db.flush()

        for image in payload.imagenes or []:
            db.add(
                AnuncioImagen(
                    id_anuncio=notice.id_anuncio,
                    url=image.url,
                    path_storage=image.path_storage,
                    nombre_original=image.nombre_original,
                )
            )

        for target in payload.filtros or []:
            db.add(
                AnuncioTarget(
                    id_anuncio=notice.id_anuncio,
                    tipo_usuario=target.tipo_usuario,
                    carrera=target.carrera,
                    semestre=target.semestre,
                    id_grupo=target.id_grupo,
                    id_grupo_materia=target.id_grupo_materia,
                )
            )

        recipients = AnnouncementService._resolve_recipients(
            db=db,
            sender=sender,
            explicit_ids=payload.destinatarios or [],
            targets=payload.filtros or [],
        )

        AnnouncementService._create_delivery_records(db, notice, recipients)
        db.commit()
        db.refresh(notice)

        return AnnouncementService.to_dict(notice, include_targets=True)

    @staticmethod
    def list_for_user(db: Session, user: Usuario, important_only: bool = False) -> list[dict]:
        now = datetime.utcnow()
        query = db.query(Anuncio).filter(
            Anuncio.activo.is_(True),
            or_(Anuncio.visible_desde.is_(None), Anuncio.visible_desde <= now),
            or_(Anuncio.visible_hasta.is_(None), Anuncio.visible_hasta >= now),
        )

        if important_only:
            query = query.filter(
                or_(
                    Anuncio.fijado.is_(True),
                    Anuncio.prioridad.in_(IMPORTANT_PRIORITIES),
                    Anuncio.categoria.in_(IMPORTANT_CATEGORIES),
                )
            )

        notices = query.order_by(desc(Anuncio.fijado), desc(Anuncio.fecha)).all()
        visible_notices = []

        for notice in notices:
            if AnnouncementService._is_visible_to_user(db, notice, user):
                visible_notices.append(notice)

        visible_notices.sort(
            key=lambda item: (
                1 if getattr(item, "fijado", False) else 0,
                PRIORITY_ORDER.get(getattr(item, "prioridad", "NORMAL"), 2),
                getattr(item, "fecha", datetime.min),
            ),
            reverse=True,
        )

        return [AnnouncementService.to_dict(notice) for notice in visible_notices]

    @staticmethod
    def list_all(db: Session) -> list[dict]:
        notices = db.query(Anuncio).order_by(desc(Anuncio.fecha)).all()
        return [AnnouncementService.to_dict(notice, include_targets=True) for notice in notices]

    @staticmethod
    def to_dict(notice: Anuncio, include_targets: bool = False) -> dict:
        data = {
            "id_anuncio": notice.id_anuncio,
            "titulo": getattr(notice, "titulo", None),
            "contenido": notice.contenido,
            "fecha": notice.fecha,
            "id_emisor": notice.id_emisor,
            "categoria": getattr(notice, "categoria", "GENERAL"),
            "prioridad": getattr(notice, "prioridad", "NORMAL"),
            "fijado": getattr(notice, "fijado", False),
            "activo": getattr(notice, "activo", True),
            "visible_desde": getattr(notice, "visible_desde", None),
            "visible_hasta": getattr(notice, "visible_hasta", None),
            "imagenes": [
                {
                    "url": image.url,
                    "path_storage": getattr(image, "path_storage", None),
                    "nombre_original": getattr(image, "nombre_original", None),
                }
                for image in getattr(notice, "imagenes", []) or []
            ],
        }

        if include_targets:
            data["filtros"] = [
                {
                    "tipo_usuario": target.tipo_usuario,
                    "carrera": target.carrera,
                    "semestre": target.semestre,
                    "id_grupo": target.id_grupo,
                    "id_grupo_materia": target.id_grupo_materia,
                }
                for target in getattr(notice, "targets", []) or []
            ]

        return data

    @staticmethod
    def _ensure_staff(user: Usuario) -> None:
        if getattr(user, "tipo_usuario", None) not in STAFF_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta acción",
            )

    @staticmethod
    def _resolve_recipients(
        db: Session,
        sender: Usuario,
        explicit_ids: list[int],
        targets: list[AnnouncementTargetCreate],
    ) -> list[Usuario]:
        base_query = db.query(Usuario).filter(Usuario.activo.is_(True), Usuario.id_usuario != sender.id_usuario)

        if explicit_ids:
            users = base_query.filter(Usuario.id_usuario.in_(explicit_ids)).all()
            found_ids = {user.id_usuario for user in users}
            missing_ids = sorted(set(explicit_ids) - found_ids)
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"message": "Uno o más destinatarios no existen o están inactivos", "ids": missing_ids},
                )
            return users

        if targets:
            users = base_query.all()
            return [user for user in users if AnnouncementService._matches_any_target(db, user, targets)]

        return base_query.all()

    @staticmethod
    def _create_delivery_records(db: Session, notice: Anuncio, recipients: Iterable[Usuario]) -> None:
        for user in recipients:
            if AnuncioDestinatario is not None:
                db.add(AnuncioDestinatario(id_anuncio=notice.id_anuncio, id_usuario=user.id_usuario))

            db.add(
                Notificacion(
                    id_usuario=user.id_usuario,
                    contenido=f"Nuevo anuncio: {notice.titulo or notice.contenido[:60]}",
                    id_anuncio=notice.id_anuncio,
                    leida=False,
                )
            )

    @staticmethod
    def _is_visible_to_user(db: Session, notice: Anuncio, user: Usuario) -> bool:
        if getattr(user, "tipo_usuario", None) == "ADMIN":
            return True

        if AnuncioDestinatario is not None:
            direct_delivery = db.query(AnuncioDestinatario).filter(
                AnuncioDestinatario.id_anuncio == notice.id_anuncio,
                AnuncioDestinatario.id_usuario == user.id_usuario,
            ).first()
            if direct_delivery:
                return True

        targets = getattr(notice, "targets", []) or []
        if targets:
            return AnnouncementService._matches_any_target(db, user, targets)

        return True

    @staticmethod
    def _matches_any_target(db: Session, user: Usuario, targets: Iterable) -> bool:
        return any(AnnouncementService._matches_target(db, user, target) for target in targets)

    @staticmethod
    def _matches_target(db: Session, user: Usuario, target) -> bool:
        target_role = getattr(target, "tipo_usuario", None)
        if target_role and getattr(user, "tipo_usuario", None) != target_role:
            return False

        target_career = getattr(target, "carrera", None)
        target_semester = getattr(target, "semestre", None)
        target_group_id = getattr(target, "id_grupo", None)
        target_group_subject_id = getattr(target, "id_grupo_materia", None)

        if not any([target_career, target_semester, target_group_id, target_group_subject_id]):
            return True

        student_profile = getattr(user, "alumno", None)
        if target_career and (not student_profile or getattr(student_profile, "carrera", None) != target_career):
            return False

        if target_semester and (not student_profile or getattr(student_profile, "semestre", None) != target_semester):
            return False

        if target_group_id or target_group_subject_id:
            if AlumnoMateriaGrupo is None or GrupoMateria is None:
                return False

            academic_query = db.query(AlumnoMateriaGrupo).join(
                GrupoMateria,
                AlumnoMateriaGrupo.id_grupo_materia == GrupoMateria.id_grupo_materia,
            ).filter(AlumnoMateriaGrupo.id_usuario == user.id_usuario)

            if target_group_subject_id:
                academic_query = academic_query.filter(AlumnoMateriaGrupo.id_grupo_materia == target_group_subject_id)

            if target_group_id:
                academic_query = academic_query.filter(GrupoMateria.id_grupo == target_group_id)

            return academic_query.first() is not None

        return True
