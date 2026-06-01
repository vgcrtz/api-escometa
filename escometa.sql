CREATE DATABASE IF NOT EXISTS escometa;
USE escometa;

SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW IF EXISTS VistaAlumnoMaterias;
DROP VIEW IF EXISTS VistaGrupoMateriaDetalle;
DROP TABLE IF EXISTS VerificacionCorreo;
DROP TABLE IF EXISTS Alumno_MateriaGrupo;
DROP TABLE IF EXISTS Usuario_Grupo;
DROP TABLE IF EXISTS Alumno_Grupo;
DROP TABLE IF EXISTS SesionClase;
DROP TABLE IF EXISTS GrupoMateria;
DROP TABLE IF EXISTS GrupoAcademico;
DROP TABLE IF EXISTS Materia;
DROP TABLE IF EXISTS Participante;
DROP TABLE IF EXISTS Mensaje;
DROP TABLE IF EXISTS Conversacion;
DROP TABLE IF EXISTS AnuncioImagen;
DROP TABLE IF EXISTS Anuncio_Usuario;
DROP TABLE IF EXISTS Anuncio;
DROP TABLE IF EXISTS Archivo;
DROP TABLE IF EXISTS Asistencia;
DROP TABLE IF EXISTS Notificacion;
DROP TABLE IF EXISTS Administrativo;
DROP TABLE IF EXISTS Docente;
DROP TABLE IF EXISTS Alumno;
DROP TABLE IF EXISTS Usuario;
SET FOREIGN_KEY_CHECKS = 1;

# Parte correspondiente al usuario
CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL,
    nombre_usuario VARCHAR(30) UNIQUE NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    tipo_usuario ENUM('ALUMNO','DOCENTE','ADMINISTRATIVO','ADMIN') NOT NULL,
    foto_perfil_url VARCHAR(500) NULL,
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Alumno (
    id_usuario INT PRIMARY KEY,
    boleta VARCHAR(20),
    carrera VARCHAR(100),
    semestre INT,
    creditos INT,
    carga INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE Docente (
    id_usuario INT PRIMARY KEY,
    grado_academico VARCHAR(100),
    departamento VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE Administrativo (
    id_usuario INT PRIMARY KEY,
    area VARCHAR(100),
    puesto VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE VerificacionCorreo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    codigo VARCHAR(10) NOT NULL,
    expiracion DATETIME NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

# Catálogo de materias
CREATE TABLE Materia (
    id_materia INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

# Grupo académico general: por ejemplo 2CV1, 4CM2, 6IM1.
# Esta tabla NO inscribe materias al alumno por sí sola.
CREATE TABLE GrupoAcademico (
    id_grupo INT AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(30) NOT NULL,
    carrera VARCHAR(100) NULL,
    semestre INT NULL,
    turno ENUM('MATUTINO','VESPERTINO','MIXTO') DEFAULT 'MIXTO',
    UNIQUE KEY uq_grupo_academico (clave, carrera, semestre)
);

# Oferta concreta de una materia dentro de un grupo académico.
# Una fila representa una sola materia con su docente, no todo el paquete del grupo.
CREATE TABLE GrupoMateria (
    id_grupo_materia INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo INT NOT NULL,
    id_materia INT NOT NULL,
    id_docente INT NOT NULL,
    cupo INT NULL,
    FOREIGN KEY (id_grupo) REFERENCES GrupoAcademico(id_grupo) ON DELETE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES Materia(id_materia) ON DELETE CASCADE,
    FOREIGN KEY (id_docente) REFERENCES Docente(id_usuario) ON DELETE CASCADE,
    UNIQUE KEY uq_grupo_materia_docente (id_grupo, id_materia, id_docente),
    UNIQUE KEY uq_grupo_materia_materia (id_grupo_materia, id_materia),
    INDEX idx_grupo_materia_grupo (id_grupo),
    INDEX idx_grupo_materia_materia (id_materia),
    INDEX idx_grupo_materia_docente (id_docente)
);

# Inscripción real del alumno.
# El alumno se inscribe a una materia específica ofertada en un grupo específico.
# Por eso puede tomar materias de diferentes grupos sin quedar inscrito a todas las materias de un grupo.
CREATE TABLE Alumno_MateriaGrupo (
    id_alumno INT NOT NULL,
    id_grupo_materia INT NOT NULL,
    id_materia INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('INSCRITO','BAJA') DEFAULT 'INSCRITO',
    PRIMARY KEY (id_alumno, id_grupo_materia),
    UNIQUE KEY uq_alumno_materia (id_alumno, id_materia),
    FOREIGN KEY (id_alumno) REFERENCES Alumno(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_grupo_materia, id_materia) REFERENCES GrupoMateria(id_grupo_materia, id_materia) ON DELETE CASCADE,
    INDEX idx_alumno_materia_grupo (id_grupo_materia),
    INDEX idx_alumno_materia (id_materia)
);

# Sesiones/horarios de una materia concreta dentro de un grupo.
CREATE TABLE SesionClase (
    id_sesion INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo_materia INT NOT NULL,
    dia ENUM('LUNES','MARTES','MIERCOLES','JUEVES','VIERNES','SABADO') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    aula VARCHAR(50),
    FOREIGN KEY (id_grupo_materia) REFERENCES GrupoMateria(id_grupo_materia) ON DELETE CASCADE,
    INDEX idx_sesion_grupo_materia (id_grupo_materia)
);

# Parte correspondiente al chatsito
CREATE TABLE Conversacion (
    id_conversacion INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE Participante (
    id_usuario INT,
    id_conversacion INT,
    PRIMARY KEY (id_usuario, id_conversacion),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_conversacion) REFERENCES Conversacion(id_conversacion) ON DELETE CASCADE
);

CREATE TABLE Mensaje (
    id_mensaje INT AUTO_INCREMENT PRIMARY KEY,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    id_conversacion INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_conversacion) REFERENCES Conversacion(id_conversacion) ON DELETE CASCADE
);

# Parte correspondiente al anuncio
CREATE TABLE Anuncio (
    id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_emisor INT NOT NULL,
    FOREIGN KEY (id_emisor) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE Anuncio_Usuario (
    id_anuncio INT,
    id_usuario INT,
    PRIMARY KEY (id_anuncio, id_usuario),
    FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE AnuncioImagen (
    id_imagen INT AUTO_INCREMENT PRIMARY KEY,
    id_anuncio INT NOT NULL,
    url VARCHAR(500) NOT NULL,
    path_storage VARCHAR(500),
    nombre_original VARCHAR(255),
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio) ON DELETE CASCADE
);

CREATE TABLE Archivo (
    id_archivo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    nombre VARCHAR(100),
    tipo VARCHAR(50),
    acceso VARCHAR(50),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE Asistencia (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    fecha DATE,
    hora TIME,
    coordenadas VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE Notificacion (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    contenido TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

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
    gm.cupo
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

-- drop database escometa;
