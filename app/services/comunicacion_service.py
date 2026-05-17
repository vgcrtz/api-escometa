from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.archivo_asistencia import Notificacion
from app.models.comunicacion import Anuncio, AnuncioUsuario
from app.models.usuario import Usuario
from app.schemas.comunicacion import AnuncioCreate, NotificacionCreate


def _obtener_usuario(db: Session, id_usuario: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def _destinatarios_para_anuncio(db: Session, id_emisor: int, destinatarios: list[int] | None) -> list[int]:
    if destinatarios:
        ids_unicos = sorted(set(destinatarios))
        usuarios = db.query(Usuario).filter(Usuario.id_usuario.in_(ids_unicos), Usuario.activo.is_(True)).all()
        encontrados = {u.id_usuario for u in usuarios}
        faltantes = [uid for uid in ids_unicos if uid not in encontrados]
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Uno o más destinatarios no existen o están inactivos", "ids": faltantes},
            )
        return ids_unicos

    usuarios = db.query(Usuario).filter(Usuario.activo.is_(True), Usuario.id_usuario != id_emisor).all()
    return [u.id_usuario for u in usuarios]


def crear_anuncio(db: Session, id_emisor: int, payload: AnuncioCreate) -> Anuncio:
    _obtener_usuario(db, id_emisor)

    destinatarios = _destinatarios_para_anuncio(db, id_emisor, payload.destinatarios)

    anuncio = Anuncio(contenido=payload.contenido, id_emisor=id_emisor)
    db.add(anuncio)
    db.flush()

    from app.models.anuncio_imagen import AnuncioImagen
    for imagen in payload.imagenes or []:
        db.add(AnuncioImagen(
            id_anuncio=anuncio.id_anuncio,
            url=str(imagen.url),
            path_storage=imagen.path_storage,
            nombre_original=imagen.nombre_original
        ))

    for id_usuario in destinatarios:
        db.add(AnuncioUsuario(id_anuncio=anuncio.id_anuncio, id_usuario=id_usuario))
        db.add(Notificacion(id_usuario=id_usuario, contenido=f"Nuevo anuncio: {payload.contenido}"))

    db.commit()
    db.refresh(anuncio)
    return anuncio


def listar_anuncios(db: Session) -> list[Anuncio]:
    return db.query(Anuncio).order_by(Anuncio.fecha.desc()).all()


def obtener_anuncio(db: Session, id_anuncio: int) -> Anuncio:
    anuncio = db.query(Anuncio).filter(Anuncio.id_anuncio == id_anuncio).first()
    if not anuncio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anuncio no encontrado")
    return anuncio


def listar_mis_anuncios(db: Session, id_usuario: int) -> list[Anuncio]:
    return (
        db.query(Anuncio)
        .join(AnuncioUsuario, AnuncioUsuario.id_anuncio == Anuncio.id_anuncio)
        .filter(AnuncioUsuario.id_usuario == id_usuario)
        .order_by(Anuncio.fecha.desc())
        .all()
    )


def listar_destinatarios_anuncio(db: Session, id_anuncio: int) -> list[int]:
    return [
        r.id_usuario
        for r in db.query(AnuncioUsuario).filter(AnuncioUsuario.id_anuncio == id_anuncio).all()
    ]


def eliminar_anuncio(db: Session, id_anuncio: int) -> None:
    anuncio = obtener_anuncio(db, id_anuncio)
    db.query(AnuncioUsuario).filter(AnuncioUsuario.id_anuncio == id_anuncio).delete()
    db.delete(anuncio)
    db.commit()


def crear_notificacion(db: Session, payload: NotificacionCreate) -> Notificacion:
    _obtener_usuario(db, payload.id_usuario)
    notificacion = Notificacion(id_usuario=payload.id_usuario, contenido=payload.contenido, leida=False)
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def listar_notificaciones_usuario(db: Session, id_usuario: int) -> list[Notificacion]:
    return (
        db.query(Notificacion)
        .filter(Notificacion.id_usuario == id_usuario)
        .order_by(Notificacion.fecha.desc())
        .all()
    )


def listar_notificaciones(db: Session) -> list[Notificacion]:
    return db.query(Notificacion).order_by(Notificacion.fecha.desc()).all()


def marcar_notificacion_leida(db: Session, id_notificacion: int, id_usuario: int | None = None) -> Notificacion:
    query = db.query(Notificacion).filter(Notificacion.id_notificacion == id_notificacion)
    if id_usuario is not None:
        query = query.filter(Notificacion.id_usuario == id_usuario)

    notificacion = query.first()
    if not notificacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")

    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)
    return notificacion


def marcar_todas_leidas(db: Session, id_usuario: int) -> int:
    actualizadas = (
        db.query(Notificacion)
        .filter(Notificacion.id_usuario == id_usuario, Notificacion.leida.is_(False))
        .update({"leida": True}, synchronize_session=False)
    )
    db.commit()
    return int(actualizadas)
