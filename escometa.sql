# drop database escometa;

CREATE DATABASE IF NOT EXISTS escometa
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE escometa;
SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS VistaNoticiasImportantes;
DROP VIEW IF EXISTS VistaAlumnoMaterias;
DROP VIEW IF EXISTS VistaGrupoMateriaDetalle;

DROP TABLE IF EXISTS forum_attachments;
DROP TABLE IF EXISTS forum_messages;
DROP TABLE IF EXISTS forum_communities;

DROP TABLE IF EXISTS mensaje_notificaciones;
DROP TABLE IF EXISTS mensaje_lecturas;
DROP TABLE IF EXISTS mensaje_adjuntos;
DROP TABLE IF EXISTS mensaje_archivos;
DROP TABLE IF EXISTS mensajes;
DROP TABLE IF EXISTS conversacion_participantes;
DROP TABLE IF EXISTS participantes;
DROP TABLE IF EXISTS conversaciones;
DROP TABLE IF EXISTS MensajeLectura;
DROP TABLE IF EXISTS MensajeArchivo;
DROP TABLE IF EXISTS Mensaje;
DROP TABLE IF EXISTS Participante;
DROP TABLE IF EXISTS Conversacion;

DROP TABLE IF EXISTS Anuncio_Target;
DROP TABLE IF EXISTS AnuncioTarget;
DROP TABLE IF EXISTS AnuncioImagen;
DROP TABLE IF EXISTS Anuncio_Usuario;
DROP TABLE IF EXISTS Notificacion;
DROP TABLE IF EXISTS Anuncio;

DROP TABLE IF EXISTS Archivo;
DROP TABLE IF EXISTS Asistencia;

DROP TABLE IF EXISTS VerificacionCorreo;
DROP TABLE IF EXISTS Alumno_MateriaGrupo;
DROP TABLE IF EXISTS SesionClase;
DROP TABLE IF EXISTS GrupoMateria;
DROP TABLE IF EXISTS GrupoAcademico;
DROP TABLE IF EXISTS Materia;

DROP TABLE IF EXISTS Administrativo;
DROP TABLE IF EXISTS Docente;
DROP TABLE IF EXISTS Alumno;
DROP TABLE IF EXISTS Usuario;

DROP TABLE IF EXISTS Usuario_Grupo;
DROP TABLE IF EXISTS Alumno_Grupo;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Usuario (
  id_usuario INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
  correo VARCHAR(120) UNIQUE NOT NULL,
  `contraseña` VARCHAR(255) NOT NULL,
  tipo_usuario ENUM('ALUMNO','DOCENTE','ADMINISTRATIVO','ADMIN') NOT NULL,
  foto_perfil_url VARCHAR(700) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  verificado BOOLEAN NOT NULL DEFAULT FALSE,
  fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_usuario_tipo (tipo_usuario),
  INDEX ix_usuario_activo (activo),
  INDEX ix_usuario_verificado (verificado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Alumno (
  id_usuario INT PRIMARY KEY,
  boleta VARCHAR(20) UNIQUE NULL,
  carrera VARCHAR(120) NULL,
  semestre INT NULL,
  creditos INT NOT NULL DEFAULT 0,
  carga INT NOT NULL DEFAULT 0,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_alumno_carrera_semestre (carrera, semestre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Docente (
  id_usuario INT PRIMARY KEY,
  grado_academico VARCHAR(120) NULL,
  departamento VARCHAR(120) NULL,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_docente_departamento (departamento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Administrativo (
  id_usuario INT PRIMARY KEY,
  area VARCHAR(120) NULL,
  puesto VARCHAR(120) NULL,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE VerificacionCorreo (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL,
  codigo VARCHAR(10) NOT NULL,
  expiracion DATETIME NOT NULL,
  usado BOOLEAN NOT NULL DEFAULT FALSE,
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_verificacion_usuario_usado (id_usuario, usado),
  INDEX ix_verificacion_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Materia (
  id_materia INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE KEY uq_materia_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE GrupoAcademico (
  id_grupo INT AUTO_INCREMENT PRIMARY KEY,
  clave VARCHAR(30) NOT NULL,
  carrera VARCHAR(120) NULL,
  semestre INT NULL,
  turno ENUM('MATUTINO','VESPERTINO','MIXTO') NOT NULL DEFAULT 'MIXTO',
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE KEY uq_grupo_clave (clave),
  INDEX ix_grupo_carrera_semestre (carrera, semestre),
  INDEX ix_grupo_turno (turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE GrupoMateria (
  id_grupo_materia INT AUTO_INCREMENT PRIMARY KEY,
  id_grupo INT NOT NULL,
  id_materia INT NOT NULL,
  id_docente INT NOT NULL,
  cupo INT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_grupo) REFERENCES GrupoAcademico(id_grupo) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_materia) REFERENCES Materia(id_materia) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_docente) REFERENCES Docente(id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  UNIQUE KEY uq_grupo_materia_docente (id_grupo, id_materia, id_docente),
  UNIQUE KEY uq_grupo_materia_materia (id_grupo_materia, id_materia),
  INDEX ix_grupo_materia_grupo (id_grupo),
  INDEX ix_grupo_materia_materia (id_materia),
  INDEX ix_grupo_materia_docente (id_docente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Alumno_MateriaGrupo (
  id_alumno INT NOT NULL,
  id_grupo_materia INT NOT NULL,
  id_materia INT NOT NULL,
  fecha_inscripcion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('INSCRITO','BAJA','FINALIZADO') NOT NULL DEFAULT 'INSCRITO',
  PRIMARY KEY (id_alumno, id_grupo_materia),
  UNIQUE KEY uq_alumno_materia_activa (id_alumno, id_materia),
  FOREIGN KEY (id_alumno) REFERENCES Alumno(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_grupo_materia, id_materia) REFERENCES GrupoMateria(id_grupo_materia, id_materia) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_alumno_materia_grupo (id_grupo_materia),
  INDEX ix_alumno_materia (id_materia),
  INDEX ix_alumno_materia_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE SesionClase (
  id_sesion INT AUTO_INCREMENT PRIMARY KEY,
  id_grupo_materia INT NOT NULL,
  dia ENUM('LUNES','MARTES','MIERCOLES','JUEVES','VIERNES','SABADO') NOT NULL,
  hora_inicio TIME NOT NULL,
  hora_fin TIME NOT NULL,
  aula VARCHAR(80) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  FOREIGN KEY (id_grupo_materia) REFERENCES GrupoMateria(id_grupo_materia) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_sesion_grupo_materia (id_grupo_materia),
  INDEX ix_sesion_dia_hora (dia, hora_inicio, hora_fin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversaciones (
  id_conversacion INT AUTO_INCREMENT PRIMARY KEY,

  tipo ENUM('DIRECTO', 'GRUPO') NOT NULL DEFAULT 'DIRECTO',
  titulo VARCHAR(150) NULL,

  creado_por INT NOT NULL,
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  activo BOOLEAN NOT NULL DEFAULT TRUE,

  CONSTRAINT fk_conversaciones_creado_por
    FOREIGN KEY (creado_por)
    REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  INDEX idx_conversaciones_actualizado (actualizado_en),
  INDEX idx_conversaciones_creado_por (creado_por),
  INDEX idx_conversaciones_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversacion_participantes (
  id_conversacion INT NOT NULL,
  id_usuario INT NOT NULL,

  rol ENUM('MIEMBRO', 'ADMIN') NOT NULL DEFAULT 'MIEMBRO',

  fecha_union DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_salida DATETIME NULL,

  silenciado BOOLEAN NOT NULL DEFAULT FALSE,
  archivado BOOLEAN NOT NULL DEFAULT FALSE,

  PRIMARY KEY (id_conversacion, id_usuario),

  CONSTRAINT fk_participantes_conversacion
    FOREIGN KEY (id_conversacion)
    REFERENCES conversaciones(id_conversacion)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_participantes_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  INDEX idx_participantes_usuario (id_usuario),
  INDEX idx_participantes_conversacion (id_conversacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mensajes (
  id_mensaje INT AUTO_INCREMENT PRIMARY KEY,

  id_conversacion INT NOT NULL,
  id_emisor INT NOT NULL,

  contenido TEXT NULL,

  tipo ENUM('TEXTO', 'IMAGEN', 'ARCHIVO', 'SISTEMA') NOT NULL DEFAULT 'TEXTO',

  fecha_envio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_edicion DATETIME NULL,

  editado BOOLEAN NOT NULL DEFAULT FALSE,
  eliminado BOOLEAN NOT NULL DEFAULT FALSE,

  id_mensaje_respuesta INT NULL,

  CONSTRAINT fk_mensajes_conversacion
    FOREIGN KEY (id_conversacion)
    REFERENCES conversaciones(id_conversacion)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_mensajes_emisor
    FOREIGN KEY (id_emisor)
    REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_mensajes_respuesta
    FOREIGN KEY (id_mensaje_respuesta)
    REFERENCES mensajes(id_mensaje)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  INDEX idx_mensajes_conversacion_fecha (id_conversacion, fecha_envio),
  INDEX idx_mensajes_emisor (id_emisor),
  INDEX idx_mensajes_respuesta (id_mensaje_respuesta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mensaje_lecturas (
  id_mensaje INT NOT NULL,
  id_usuario INT NOT NULL,

  leido_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id_mensaje, id_usuario),

  CONSTRAINT fk_lecturas_mensaje
    FOREIGN KEY (id_mensaje)
    REFERENCES mensajes(id_mensaje)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_lecturas_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  INDEX idx_lecturas_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mensaje_adjuntos (
  id_adjunto INT AUTO_INCREMENT PRIMARY KEY,

  id_mensaje INT NOT NULL,

  url TEXT NOT NULL,
  path_storage VARCHAR(255) NULL,
  nombre_original VARCHAR(255) NULL,
  tipo_mime VARCHAR(100) NULL,
  tamano_bytes BIGINT NULL,

  fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_adjuntos_mensaje
    FOREIGN KEY (id_mensaje)
    REFERENCES mensajes(id_mensaje)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  INDEX idx_adjuntos_mensaje (id_mensaje)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mensaje_notificaciones (
  id_notificacion_chat INT AUTO_INCREMENT PRIMARY KEY,

  id_mensaje INT NOT NULL,
  id_usuario INT NOT NULL,

  entregada BOOLEAN NOT NULL DEFAULT FALSE,
  leida BOOLEAN NOT NULL DEFAULT FALSE,

  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_entrega DATETIME NULL,
  fecha_lectura DATETIME NULL,

  CONSTRAINT fk_notificacion_chat_mensaje
    FOREIGN KEY (id_mensaje)
    REFERENCES mensajes(id_mensaje)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_notificacion_chat_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  UNIQUE KEY uq_notificacion_chat_mensaje_usuario (id_mensaje, id_usuario),
  INDEX idx_notificacion_chat_usuario (id_usuario),
  INDEX idx_notificacion_chat_leida (id_usuario, leida),
  INDEX idx_notificacion_chat_entregada (id_usuario, entregada)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE forum_communities (
  id_community INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  description TEXT NULL,
  image_url TEXT NULL,
  created_by INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE KEY uq_forum_communities_name (name),
  INDEX ix_forum_communities_created_by (created_by),
  CONSTRAINT fk_forum_communities_created_by
    FOREIGN KEY (created_by) REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE forum_messages (
  id_message INT AUTO_INCREMENT PRIMARY KEY,
  id_community INT NOT NULL,
  id_sender INT NOT NULL,
  content TEXT NULL,
  message_type ENUM('TEXT','IMAGE','FILE','SYSTEM') NOT NULL DEFAULT 'TEXT',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  edited_at DATETIME NULL,
  edited BOOLEAN NOT NULL DEFAULT FALSE,
  deleted BOOLEAN NOT NULL DEFAULT FALSE,
  pinned BOOLEAN NOT NULL DEFAULT FALSE,
  reply_message_id INT NULL,
  INDEX ix_forum_messages_community_created (id_community, created_at),
  INDEX ix_forum_messages_sender (id_sender),
  INDEX ix_forum_messages_pinned (pinned),
  CONSTRAINT fk_forum_messages_community
    FOREIGN KEY (id_community) REFERENCES forum_communities(id_community)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_forum_messages_sender
    FOREIGN KEY (id_sender) REFERENCES Usuario(id_usuario)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_forum_messages_reply
    FOREIGN KEY (reply_message_id) REFERENCES forum_messages(id_message)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE forum_attachments (
  id_attachment INT AUTO_INCREMENT PRIMARY KEY,
  id_message INT NOT NULL,
  url TEXT NOT NULL,
  storage_path VARCHAR(500) NULL,
  original_name VARCHAR(255) NULL,
  mime_type VARCHAR(120) NULL,
  size_bytes BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_forum_attachments_message (id_message),
  CONSTRAINT fk_forum_attachments_message
    FOREIGN KEY (id_message) REFERENCES forum_messages(id_message)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================================================
-- Comunicación: anuncios, noticias importantes y notificaciones
-- Anuncio vive en este módulo. Anuncio_Target permite filtrar por rol, carrera, semestre, grupo y materia-grupo.
-- =========================================================

CREATE TABLE Anuncio (
  id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(160) NULL,
  contenido TEXT NOT NULL,
  categoria ENUM('GENERAL','ACADEMICA','TRAMITES','EVENTO','EMERGENCIA','SISTEMA') NOT NULL DEFAULT 'GENERAL',
  prioridad ENUM('BAJA','NORMAL','ALTA','URGENTE') NOT NULL DEFAULT 'NORMAL',
  fijado BOOLEAN NOT NULL DEFAULT FALSE,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  visible_desde DATETIME NULL,
  visible_hasta DATETIME NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  id_emisor INT NOT NULL,
  FOREIGN KEY (id_emisor) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX ix_anuncio_emisor (id_emisor),
  INDEX ix_anuncio_activo (activo),
  INDEX ix_anuncio_visible (visible_desde, visible_hasta),
  INDEX ix_anuncio_fijado (fijado),
  INDEX ix_anuncio_fecha (fecha),
  INDEX ix_anuncio_prioridad (prioridad),
  INDEX ix_anuncio_categoria (categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Anuncio_Usuario (
  id_anuncio INT NOT NULL,
  id_usuario INT NOT NULL,
  PRIMARY KEY (id_anuncio, id_usuario),
  FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_anuncio_usuario_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE AnuncioImagen (
  id_imagen INT AUTO_INCREMENT PRIMARY KEY,
  id_anuncio INT NOT NULL,
  url VARCHAR(700) NOT NULL,
  path_storage VARCHAR(500) NULL,
  nombre_original VARCHAR(255) NULL,
  fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_anuncio_imagen_anuncio (id_anuncio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Anuncio_Target (
  id_target INT AUTO_INCREMENT PRIMARY KEY,
  id_anuncio INT NOT NULL,
  tipo_usuario ENUM('ALUMNO','DOCENTE','ADMINISTRATIVO','ADMIN','INVITADO') NULL,
  carrera VARCHAR(120) NULL,
  semestre INT NULL,
  id_grupo INT NULL,
  id_grupo_materia INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_grupo) REFERENCES GrupoAcademico(id_grupo) ON UPDATE CASCADE ON DELETE SET NULL,
  FOREIGN KEY (id_grupo_materia) REFERENCES GrupoMateria(id_grupo_materia) ON UPDATE CASCADE ON DELETE SET NULL,
  INDEX ix_anuncio_target_anuncio (id_anuncio),
  INDEX ix_anuncio_target_tipo (tipo_usuario),
  INDEX ix_anuncio_target_carrera_semestre (carrera, semestre),
  INDEX ix_anuncio_target_grupo (id_grupo),
  INDEX ix_anuncio_target_grupo_materia (id_grupo_materia)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Notificacion (
  id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL,
  contenido TEXT NOT NULL,
  tipo VARCHAR(60) NOT NULL DEFAULT 'GENERAL',
  id_anuncio INT NULL,
  url_accion VARCHAR(500) NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  leida BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON UPDATE CASCADE ON DELETE SET NULL,
  INDEX ix_notificacion_usuario_leida (id_usuario, leida),
  INDEX ix_notificacion_fecha (fecha),
  INDEX ix_notificacion_anuncio (id_anuncio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Archivo (
  id_archivo INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NULL,
  nombre VARCHAR(255) NULL,
  tipo VARCHAR(120) NULL,
  url TEXT NULL,
  path_storage VARCHAR(500) NULL,
  acceso ENUM('PUBLICO','PRIVADO') NOT NULL DEFAULT 'PRIVADO',
  fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE SET NULL,
  INDEX ix_archivo_usuario (id_usuario),
  INDEX ix_archivo_acceso (acceso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Asistencia (
  id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NOT NULL,
  fecha DATE NOT NULL,
  hora TIME NOT NULL,
  coordenadas VARCHAR(100) NULL,
  latitud DECIMAL(10, 7) NULL,
  longitud DECIMAL(10, 7) NULL,
  distancia_metros DECIMAL(10, 2) NULL,
  dentro_zona BOOLEAN NOT NULL DEFAULT TRUE,
  fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
  INDEX ix_asistencia_usuario_fecha (id_usuario, fecha),
  INDEX ix_asistencia_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW VistaGrupoMateriaDetalle AS
SELECT
  gm.id_grupo_materia,
  ga.id_grupo,
  ga.clave AS grupo,
  ga.carrera,
  ga.semestre,
  ga.turno,
  m.id_materia,
  m.nombre AS materia,
  d.id_usuario AS id_docente,
  ud.nombre AS docente,
  gm.cupo,
  gm.activo
FROM GrupoMateria gm
INNER JOIN GrupoAcademico ga ON ga.id_grupo = gm.id_grupo
INNER JOIN Materia m ON m.id_materia = gm.id_materia
INNER JOIN Docente d ON d.id_usuario = gm.id_docente
INNER JOIN Usuario ud ON ud.id_usuario = d.id_usuario;

CREATE OR REPLACE VIEW VistaAlumnoMaterias AS
SELECT
  amg.id_alumno,
  ua.nombre AS alumno,
  ua.correo,
  amg.id_grupo_materia,
  ga.id_grupo,
  ga.clave AS grupo,
  ga.carrera,
  ga.semestre,
  ga.turno,
  m.id_materia,
  m.nombre AS materia,
  gm.id_docente,
  ud.nombre AS docente,
  amg.fecha_inscripcion,
  amg.estado
FROM Alumno_MateriaGrupo amg
INNER JOIN Alumno a ON a.id_usuario = amg.id_alumno
INNER JOIN Usuario ua ON ua.id_usuario = a.id_usuario
INNER JOIN GrupoMateria gm ON gm.id_grupo_materia = amg.id_grupo_materia
INNER JOIN GrupoAcademico ga ON ga.id_grupo = gm.id_grupo
INNER JOIN Materia m ON m.id_materia = gm.id_materia
INNER JOIN Usuario ud ON ud.id_usuario = gm.id_docente;

CREATE OR REPLACE VIEW VistaNoticiasImportantes AS
SELECT
  a.id_anuncio,
  a.titulo,
  a.contenido,
  a.categoria,
  a.prioridad,
  a.fijado,
  a.activo,
  a.fecha,
  a.visible_desde,
  a.visible_hasta,
  a.id_emisor,
  ue.nombre AS emisor,
  atg.id_target,
  atg.tipo_usuario,
  atg.carrera,
  atg.semestre,
  atg.id_grupo,
  ga.clave AS grupo,
  atg.id_grupo_materia
FROM Anuncio a
INNER JOIN Usuario ue ON ue.id_usuario = a.id_emisor
LEFT JOIN Anuncio_Target atg ON atg.id_anuncio = a.id_anuncio
LEFT JOIN GrupoAcademico ga ON ga.id_grupo = atg.id_grupo
WHERE a.activo = TRUE
  AND (a.visible_desde IS NULL OR a.visible_desde <= NOW())
  AND (a.visible_hasta IS NULL OR a.visible_hasta >= NOW());

INSERT INTO Usuario (id_usuario, nombre, nombre_usuario, correo, `contraseña`, tipo_usuario, foto_perfil_url, activo, verificado, fecha_registro) VALUES
(2, 'Omar Jesus Vazquez Sanchez', 'Boring', 'ovazquezs2000@alumno.ipn.mx', '$2b$12$LLRmVwHzX2UNCTMdR9CsgOVy.qQxrL61Kvt/yUII4JjCpfS/glCVm', 'ALUMNO', NULL, 1, 1, '2026-05-31 10:27:56'),
(3, 'Jose Ange Kind Dick', 'Stailz', 'jvegac2001@alumno.ipn.mx', '$2b$12$K1mk0otiAqV86oHU3L33CuB9nNKKFkeqfs0rPqT/gZDmgxmKPwJyS', 'ALUMNO', 'https://ftakkxavowfmoroupeao.supabase.co/storage/v1/object/public/imagenes/avatar_Stailz.png', 1, 1, '2026-05-31 10:42:24'),
(4, 'Super Administrador ESCOMETA', 'superadmin', 'superadmin@ipn.mx', '$2b$12$CvskMKW5Vzn0UVA47xa.feZwkA8na01B/Qtik/4HDoOB6Dlcsqy1W', 'ADMIN', NULL, 1, 1, '2026-05-31 16:27:17'),
(13, 'Docente Dummy 1', 'dummy_docente_1', 'dummy1@ipn.mx', '$2b$12$jXih3oyhBaPC7y2vxzOuFOZ/Ad32GhzHKmCwhInL1nTiC3SUs93Sm', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:31:34'),
(14, 'Docente Dummy 2', 'dummy_docente_2', 'dummy2@ipn.mx', '$2b$12$TWvsBKcgzuiW6RMV/YctNeckT6hmt0ze6Dtsic2NnpGYW6H/6Dafa', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:31:46'),
(15, 'Docente Dummy 3', 'dummy_docente_3', 'dummy3@ipn.mx', '$2b$12$y5riDXiItOyOMEIn2I9IF.BbspZEpJibYwIpj6AJ7W7YiZ.8tSJQC', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:42:27'),
(16, 'Docente Dummy 4', 'dummy_docente_4', 'dummy4@ipn.mx', '$2b$12$R4386szHH7pIDaXx/aaUiuGJj4LrKIsYAdhdCfUAGfIpAlA3nyIge', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:42:42'),
(17, 'Docente Dummy 5', 'dummy_docente_5', 'dummy5@ipn.mx', '$2b$12$9OH4.3f3sSDpB4Ud/KY36.EKkOQXViScBaX07yUKudoVi9toF0cFK', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:42:53'),
(18, 'Docente Dummy 6', 'dummy_docente_6', 'dummy6@ipn.mx', '$2b$12$FpQH.mV0J/KUucO1NAXcoOOQaU185YUvLIaZY7jsi84Ks1FF06LRq', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:43:03'),
(19, 'Docente Dummy 7', 'dummy_docente_7', 'dummy7@ipn.mx', '$2b$12$FPPWayG3c8aJOBXTrSceCefOf39McsXMfLklOKSdUPiud8kdj/Yru', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:43:11'),
(20, 'Docente Dummy 8', 'dummy_docente_8', 'dummy8@ipn.mx', '$2b$12$xsR.TXqdkQ7inUpVCky19.5.zgvCepZjLgRt7gchuWkPuoQcl3Sjy', 'DOCENTE', NULL, 1, 1, '2026-05-31 17:43:15');

INSERT INTO Alumno (id_usuario, boleta, carrera, semestre, creditos, carga) VALUES
(2, '2024000002', 'Ingeniería en Sistemas Computacionales', 6, 0, 0),
(3, '2024000003', 'Ingeniería en Inteligencia Artificial', 6, 0, 0);

INSERT INTO Docente (id_usuario, grado_academico, departamento) VALUES
(13, 'Maestría', 'Sistemas Computacionales'),
(14, 'Doctorado', 'Inteligencia Artificial'),
(15, 'Maestría', 'Ciencia de Datos'),
(16, 'Doctorado', 'Matemáticas'),
(17, 'Licenciatura', 'Redes y Seguridad'),
(18, 'Maestría', 'Ingeniería de Software'),
(19, 'Doctorado', 'Bases de Datos'),
(20, 'Maestría', 'Sistemas Distribuidos');

INSERT INTO Materia (id_materia, nombre, activo) VALUES
(1, 'Programación Avanzada', 1),
(2, 'Ingeniería de Software', 1),
(3, 'Inteligencia Artificial', 1),
(4, 'Bases de Datos', 1),
(5, 'Matemáticas Discretas', 1),
(6, 'Sistemas Distribuidos', 1);

INSERT INTO GrupoAcademico (id_grupo, clave, carrera, semestre, turno, activo) VALUES
(1, '6CM1', 'Ingeniería en Sistemas Computacionales', 6, 'MATUTINO', 1),
(2, '6CV1', 'Ingeniería en Sistemas Computacionales', 6, 'VESPERTINO', 1),
(3, '6BM1', 'Ingeniería en Inteligencia Artificial', 6, 'MATUTINO', 1);

INSERT INTO GrupoMateria (id_grupo_materia, id_grupo, id_materia, id_docente, cupo, activo) VALUES
(1, 1, 1, 13, 35, 1),
(2, 1, 2, 18, 35, 1),
(3, 1, 3, 14, 35, 1),
(4, 2, 4, 19, 35, 1),
(5, 3, 3, 15, 35, 1),
(6, 3, 5, 16, 35, 1);

INSERT INTO Alumno_MateriaGrupo (id_alumno, id_grupo_materia, id_materia, fecha_inscripcion, estado) VALUES
(2, 1, 1, '2026-05-31 18:00:00', 'INSCRITO'),
(2, 3, 3, '2026-05-31 18:00:00', 'INSCRITO'),
(3, 2, 2, '2026-05-31 18:05:00', 'INSCRITO'),
(3, 5, 3, '2026-05-31 18:05:00', 'INSCRITO');

INSERT INTO SesionClase (id_sesion, id_grupo_materia, dia, hora_inicio, hora_fin, aula, activo) VALUES
(1, 1, 'LUNES', '07:00:00', '08:30:00', 'A-101', 1),
(2, 1, 'MIERCOLES', '07:00:00', '08:30:00', 'A-101', 1),
(3, 2, 'MARTES', '09:00:00', '10:30:00', 'B-202', 1),
(4, 3, 'JUEVES', '11:00:00', '12:30:00', 'C-303', 1),
(5, 5, 'VIERNES', '13:00:00', '14:30:00', 'IA-1', 1);

INSERT INTO conversaciones (id_conversacion, tipo, titulo, creado_por, fecha_creacion, activo) VALUES
(1, 'DIRECTO', NULL, 2, '2026-05-31 19:00:00', 1),
(2, 'GRUPO', 'Equipo ESCOMETA', 4, '2026-05-31 19:05:00', 1);

INSERT INTO conversacion_participantes (id_conversacion, id_usuario, rol, fecha_union, fecha_salida, silenciado, archivado) VALUES
(1, 2, 'MIEMBRO', '2026-05-31 19:00:00', NULL, 0, 0),
(1, 3, 'MIEMBRO', '2026-05-31 19:00:00', NULL, 0, 0),
(2, 2, 'MIEMBRO', '2026-05-31 19:05:00', NULL, 0, 0),
(2, 3, 'MIEMBRO', '2026-05-31 19:05:00', NULL, 0, 0),
(2, 4, 'ADMIN', '2026-05-31 19:05:00', NULL, 0, 0);

INSERT INTO forum_communities (id_community, name, description, created_by, created_at, active) VALUES
(1, 'General ESCOMETA', 'Comunidad general para preguntas y avisos de ESCOMETA.', 4, '2026-05-31 19:10:00', 1),
(2, 'Ayuda con materias', 'Espacio para resolver dudas de materias, grupos y horarios.', 2, '2026-05-31 19:15:00', 1);

INSERT INTO forum_messages (id_message, id_community, id_sender, content, message_type, created_at, pinned) VALUES
(1, 1, 4, 'Bienvenido a la comunidad general de ESCOMETA.', 'TEXT', '2026-05-31 19:12:00', 1),
(2, 2, 2, 'Usa esta comunidad para preguntar sobre materias y profesores.', 'TEXT', '2026-05-31 19:16:00', 1);

INSERT INTO Anuncio (id_anuncio, titulo, contenido, categoria, prioridad, fijado, activo, visible_desde, visible_hasta, fecha, id_emisor) VALUES
(1, 'Bienvenida a ESCOMETA', 'Ya puedes explorar los módulos principales de la plataforma.', 'GENERAL', 'NORMAL', 1, 1, NULL, NULL, '2026-05-31 19:20:00', 4),
(2, 'Aviso para sexto semestre ISC', 'Revisa tus materias inscritas y confirma que tu horario sea correcto.', 'ACADEMICA', 'ALTA', 1, 1, NULL, NULL, '2026-05-31 19:25:00', 4);

INSERT INTO Anuncio_Target (id_target, id_anuncio, tipo_usuario, carrera, semestre, id_grupo, id_grupo_materia) VALUES
(1, 1, NULL, NULL, NULL, NULL, NULL),
(2, 2, 'ALUMNO', 'Ingeniería en Sistemas Computacionales', 6, NULL, NULL);

INSERT INTO Anuncio_Usuario (id_anuncio, id_usuario) VALUES
(1, 2),
(1, 3),
(1, 13),
(2, 2);

INSERT INTO Notificacion (id_notificacion, id_usuario, contenido, tipo, id_anuncio, fecha, leida) VALUES
(1, 2, 'Nuevo anuncio: Bienvenida a ESCOMETA', 'ANUNCIO', 1, '2026-05-31 19:20:00', 0),
(2, 3, 'Nuevo anuncio: Bienvenida a ESCOMETA', 'ANUNCIO', 1, '2026-05-31 19:20:00', 0),
(3, 2, 'Nuevo anuncio: Aviso para sexto semestre ISC', 'ANUNCIO', 2, '2026-05-31 19:25:00', 0);

ALTER TABLE Usuario AUTO_INCREMENT = 21;
ALTER TABLE Materia AUTO_INCREMENT = 7;
ALTER TABLE GrupoAcademico AUTO_INCREMENT = 4;
ALTER TABLE GrupoMateria AUTO_INCREMENT = 7;
ALTER TABLE SesionClase AUTO_INCREMENT = 6;
ALTER TABLE conversaciones AUTO_INCREMENT = 3;
ALTER TABLE forum_communities AUTO_INCREMENT = 3;
ALTER TABLE forum_messages AUTO_INCREMENT = 3;
ALTER TABLE Anuncio AUTO_INCREMENT = 3;
ALTER TABLE Anuncio_Target AUTO_INCREMENT = 3;
ALTER TABLE Notificacion AUTO_INCREMENT = 4;
