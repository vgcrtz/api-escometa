CREATE DATABASE IF NOT EXISTS escometa;
USE escometa;

DROP TABLE IF EXISTS Usuario, Alumno, Docente, Administrativo, Materia, GrupoAcademico, Usuario_Grupo, SesionClase, Conversacion, Participante, Mensaje, Anuncio, Anuncio_Usuario, Archivo, Asistencia, Notificacion;

#Parte correspondiente al usuario
CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    correo VARCHAR(100) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    tipo_usuario ENUM('ALUMNO','DOCENTE','ADMINISTRATIVO') NOT NULL,
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
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Docente (
    id_usuario INT PRIMARY KEY,
    grado_academico VARCHAR(100),
    departamento VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Administrativo (
    id_usuario INT PRIMARY KEY,
    area VARCHAR(100),
    puesto VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

#Parte referente a las materias

CREATE TABLE Materia (
    id_materia INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

CREATE TABLE GrupoAcademico (
    id_grupo INT AUTO_INCREMENT PRIMARY KEY,
    id_materia INT NOT NULL,
    id_docente INT NOT NULL,
    FOREIGN KEY (id_materia) REFERENCES Materia(id_materia),
    FOREIGN KEY (id_docente) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Usuario_Grupo (
    id_usuario INT,
    id_grupo INT,
    PRIMARY KEY (id_usuario, id_grupo),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_grupo) REFERENCES GrupoAcademico(id_grupo)
);

CREATE TABLE SesionClase (
    id_sesion INT AUTO_INCREMENT PRIMARY KEY,
    id_grupo INT NOT NULL,
    dia ENUM('LUNES','MARTES','MIERCOLES','JUEVES','VIERNES','SABADO') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    aula VARCHAR(50),
    FOREIGN KEY (id_grupo) REFERENCES GrupoAcademico(id_grupo)
);

#Parte correspondiente al chatsito

CREATE TABLE Conversacion (
    id_conversacion INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE Participante (
    id_usuario INT,
    id_conversacion INT,
    PRIMARY KEY (id_usuario, id_conversacion),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_conversacion) REFERENCES Conversacion(id_conversacion)
);

CREATE TABLE Mensaje (
    id_mensaje INT AUTO_INCREMENT PRIMARY KEY,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL,
    id_conversacion INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_conversacion) REFERENCES Conversacion(id_conversacion)
);

#Parte correspondiente al anuncio

CREATE TABLE Anuncio (
    id_anuncio INT AUTO_INCREMENT PRIMARY KEY,
    contenido TEXT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_emisor INT NOT NULL,
    FOREIGN KEY (id_emisor) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Anuncio_Usuario (
    id_anuncio INT,
    id_usuario INT,
    PRIMARY KEY (id_anuncio, id_usuario),
    FOREIGN KEY (id_anuncio) REFERENCES Anuncio(id_anuncio),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Archivo (
    id_archivo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    nombre VARCHAR(100),
    tipo VARCHAR(50),
    acceso VARCHAR(50),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Asistencia (
    id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    fecha DATE,
    hora TIME,
    coordenadas VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

CREATE TABLE Notificacion (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT,
    contenido TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);