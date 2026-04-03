-- Script de creación de base de datos para MathAI LMS
-- Ejecutar en phpMyAdmin o consola MySQL

DROP DATABASE IF EXISTS Matatucas_db;
CREATE DATABASE Matatucas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE Matatucas_db;

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NULL,
    nombre VARCHAR(100) NOT NULL,
    numero_control VARCHAR(20) UNIQUE,
    microsoft_id VARCHAR(100) UNIQUE NULL,
    rol ENUM('administrador', 'docente', 'estudiante') NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Estudiantes
CREATE TABLE estudiantes (
    id_usuario INT PRIMARY KEY,
    puntos_totales INT DEFAULT 0,
    racha_dias INT DEFAULT 0,
    ultimo_login DATETIME NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de Docentes
CREATE TABLE docentes (
    id_usuario INT PRIMARY KEY,
    especialidad VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de Cursos
CREATE TABLE cursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_curso VARCHAR(16) NULL UNIQUE,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    nivel ENUM('basico', 'intermedio', 'avanzado') NOT NULL,
    id_docente INT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_docente) REFERENCES docentes(id_usuario) ON DELETE SET NULL
);

-- Tabla de Lecciones
CREATE TABLE lecciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_curso INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    orden INT NOT NULL,
    contenido_teoria TEXT,
    FOREIGN KEY (id_curso) REFERENCES cursos(id) ON DELETE CASCADE
);

-- Tabla de Videos
CREATE TABLE videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_leccion INT NOT NULL,
    url_youtube VARCHAR(255) NOT NULL,
    titulo VARCHAR(150),
    FOREIGN KEY (id_leccion) REFERENCES lecciones(id) ON DELETE CASCADE
);

-- Tabla de Ejercicios
CREATE TABLE ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_leccion INT NOT NULL,
    enunciado TEXT NOT NULL,
    tipo ENUM('opcion_multiple', 'verdadero_falso', 'numerico') NOT NULL,
    opciones JSON, -- Para guardar opciones múltiples
    respuesta_correcta VARCHAR(255) NOT NULL,
    dificultad INT DEFAULT 1,
    FOREIGN KEY (id_leccion) REFERENCES lecciones(id) ON DELETE CASCADE
);

-- Tabla de Intentos de Ejercicios (persistir respuestas y calificación)
CREATE TABLE intentos_ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_ejercicio INT NOT NULL,
    intento_num INT NOT NULL DEFAULT 1,
    respuesta_usuario VARCHAR(255),
    es_correcta BOOLEAN NOT NULL DEFAULT FALSE,
    puntaje FLOAT NOT NULL DEFAULT 0.0,
    fecha_intento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_ejercicio) REFERENCES ejercicios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_intento (id_estudiante, id_ejercicio, intento_num)
);

-- Tabla de Inscripciones
CREATE TABLE inscripciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_curso INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    progreso FLOAT DEFAULT 0.0,
    bloqueado BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_curso) REFERENCES cursos(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inscription (id_estudiante, id_curso)
);

-- Tabla de Lecciones Completadas (para seguimiento de progreso real)
CREATE TABLE lecciones_completadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_leccion INT NOT NULL,
    fecha_completada DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_completion (id_estudiante, id_leccion),
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_leccion) REFERENCES lecciones(id) ON DELETE CASCADE
);

-- Tabla de Insignias
CREATE TABLE insignias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    icono VARCHAR(50),
    criterio VARCHAR(50),
    nivel_requerido INT DEFAULT 1
);

-- Tabla de Insignias por Estudiante
CREATE TABLE insignias_estudiantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_insignia INT NOT NULL,
    fecha_obtencion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_insignia) REFERENCES insignias(id) ON DELETE CASCADE
);

