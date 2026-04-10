-- Script de creación de base de datos para Matatucas LMS (VERSION COMPLETA)
-- Matatucas_db
-- -----------------------------------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Tabla de Usuarios
DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(256) NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `numero_control` VARCHAR(20) UNIQUE,
  `microsoft_id` VARCHAR(100) UNIQUE NULL,
  `rol ENUM`('administrador', 'docente', 'estudiante') NOT NULL,
  `fecha_registro` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabla de Estudiantes
DROP TABLE IF EXISTS `estudiantes`;
CREATE TABLE `estudiantes` (
  `id_usuario` INT PRIMARY KEY,
  `puntos_totales` INT DEFAULT 0,
  `racha_dias` INT DEFAULT 0,
  `ultimo_login` DATETIME NULL,
  `carrera` VARCHAR(100) NULL,
  `semestre` INT NULL,
  `grupo` VARCHAR(10) NULL,
  `fecha_actualizacion_semestre` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `monedas` INT DEFAULT 0,
  `avatar_activo` VARCHAR(255) NULL,
  `marco_activo` VARCHAR(255) NULL,
  CONSTRAINT `fk_estudiante_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Tabla de Docentes
DROP TABLE IF EXISTS `docentes`;
CREATE TABLE `docentes` (
  `id_usuario` INT PRIMARY KEY,
  `especialidad` VARCHAR(100),
  CONSTRAINT `fk_docente_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Tabla de Configuración de Usuario
DROP TABLE IF EXISTS `configuracion_usuario`;
CREATE TABLE `configuracion_usuario` (
  `id_usuario` INT PRIMARY KEY,
  `tema` VARCHAR(10) DEFAULT 'claro' NOT NULL,
  `ocultar_ranking` BOOLEAN DEFAULT FALSE NOT NULL,
  `tamano_fuente` VARCHAR(10) DEFAULT 'normal' NOT NULL,
  `notif_nuevos_cursos` BOOLEAN DEFAULT TRUE NOT NULL,
  `notif_racha` BOOLEAN DEFAULT TRUE NOT NULL,
  CONSTRAINT `fk_config_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Tabla de Cursos
DROP TABLE IF EXISTS `cursos`;
CREATE TABLE `cursos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `codigo_curso` VARCHAR(16) UNIQUE NULL,
  `titulo` VARCHAR(150) NOT NULL,
  `descripcion` TEXT,
  `nivel` ENUM('basico', 'intermedio', 'avanzado') NOT NULL,
  `id_docente` INT,
  `fecha_creacion` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `estado` ENUM('borrador', 'publicado') DEFAULT 'borrador' NOT NULL,
  `visibilidad` ENUM('global', 'privado') DEFAULT 'privado' NOT NULL,
  CONSTRAINT `fk_curso_docente` FOREIGN KEY (`id_docente`) REFERENCES `docentes` (`id_usuario`) ON DELETE SET NULL,
  INDEX `idx_codigo` (`codigo_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Tabla de Lecciones
DROP TABLE IF EXISTS `lecciones`;
CREATE TABLE `lecciones` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_curso` INT NOT NULL,
  `titulo` VARCHAR(150) NOT NULL,
  `orden` INT NOT NULL,
  `contenido_teoria` TEXT NULL,
  `secciones` JSON NULL,
  CONSTRAINT `fk_leccion_curso` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Tabla de Videos
DROP TABLE IF EXISTS `videos`;
CREATE TABLE `videos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_leccion` INT NOT NULL,
  `url_youtube` VARCHAR(255) NOT NULL,
  `titulo` VARCHAR(150) NULL,
  CONSTRAINT `fk_video_leccion` FOREIGN KEY (`id_leccion`) REFERENCES `lecciones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Tabla de Ejercicios
DROP TABLE IF EXISTS `ejercicios`;
CREATE TABLE `ejercicios` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_leccion` INT NOT NULL,
  `enunciado` TEXT NOT NULL,
  `tipo` ENUM('opcion_multiple', 'verdadero_falso', 'numerico') NOT NULL,
  `opciones` JSON NULL,
  `respuesta_correcta` VARCHAR(255) NOT NULL,
  `dificultad` INT DEFAULT 1,
  CONSTRAINT `fk_ejercicio_leccion` FOREIGN KEY (`id_leccion`) REFERENCES `lecciones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Tabla de Intentos de Ejercicios
DROP TABLE IF EXISTS `intentos_ejercicios`;
CREATE TABLE `intentos_ejercicios` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_estudiante` INT NOT NULL,
  `id_ejercicio` INT NOT NULL,
  `intento_num` INT NOT NULL DEFAULT 1,
  `respuesta_usuario` VARCHAR(255) NULL,
  `es_correcta` BOOLEAN NOT NULL DEFAULT FALSE,
  `puntaje` FLOAT NOT NULL DEFAULT 0.0,
  `fecha_intento` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_intento_estudiante` FOREIGN KEY (`id_estudiante`) REFERENCES `estudiantes` (`id_usuario`) ON DELETE CASCADE,
  CONSTRAINT `fk_intento_ejercicio` FOREIGN KEY (`id_ejercicio`) REFERENCES `ejercicios` (`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_intento_ejercicio` (`id_estudiante`, `id_ejercicio`, `intento_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Tabla de Inscripciones
DROP TABLE IF EXISTS `inscripciones`;
CREATE TABLE `inscripciones` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_estudiante` INT NOT NULL,
  `id_curso` INT NOT NULL,
  `fecha_inscripcion` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `progreso` FLOAT DEFAULT 0.0,
  `bloqueado` BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT `fk_inscripcion_estudiante` FOREIGN KEY (`id_estudiante`) REFERENCES `estudiantes` (`id_usuario`) ON DELETE CASCADE,
  CONSTRAINT `fk_inscripcion_curso` FOREIGN KEY (`id_curso`) REFERENCES `cursos` (`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_inscription` (`id_estudiante`, `id_curso`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Tabla de Lecciones Completadas
DROP TABLE IF EXISTS `lecciones_completadas`;
CREATE TABLE `lecciones_completadas` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_estudiante` INT NOT NULL,
  `id_leccion` INT NOT NULL,
  `fecha_completada` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_comp_estudiante` FOREIGN KEY (`id_estudiante`) REFERENCES `estudiantes` (`id_usuario`) ON DELETE CASCADE,
  CONSTRAINT `fk_comp_leccion` FOREIGN KEY (`id_leccion`) REFERENCES `lecciones` (`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_completion` (`id_estudiante`, `id_leccion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Tabla de Insignias
DROP TABLE IF EXISTS `insignias`;
CREATE TABLE `insignias` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(255) NULL,
  `icono` VARCHAR(50) NULL,
  `criterio` VARCHAR(50) NULL,
  `nivel_requerido` INT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Tabla de Insignias por Estudiante
DROP TABLE IF EXISTS `insignias_estudiantes`;
CREATE TABLE `insignias_estudiantes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_estudiante` INT NOT NULL,
  `id_insignia` INT NOT NULL,
  `fecha_obtencion` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_ie_estudiante` FOREIGN KEY (`id_estudiante`) REFERENCES `estudiantes` (`id_usuario`) ON DELETE CASCADE,
  CONSTRAINT `fk_ie_insignia` FOREIGN KEY (`id_insignia`) REFERENCES `insignias` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. Tabla de Artículos de Tienda
DROP TABLE IF EXISTS `articulos_tienda`;
CREATE TABLE `articulos_tienda` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(255) NULL,
  `tipo` ENUM('avatar', 'marco') NOT NULL,
  `precio` INT NOT NULL DEFAULT 0,
  `icono` VARCHAR(255) NULL,
  `css_clase` VARCHAR(255) NULL,
  `rareza` ENUM('comun', 'raro', 'epico', 'legendario') DEFAULT 'comun' NOT NULL,
  `activo` BOOLEAN DEFAULT TRUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. Tabla de Inventario de Estudiante
DROP TABLE IF EXISTS `inventario_estudiante`;
CREATE TABLE `inventario_estudiante` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_estudiante` INT NOT NULL,
  `id_articulo` INT NOT NULL,
  `fecha_compra` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_inv_estudiante` FOREIGN KEY (`id_estudiante`) REFERENCES `estudiantes` (`id_usuario`) ON DELETE CASCADE,
  CONSTRAINT `fk_inv_articulo` FOREIGN KEY (`id_articulo`) REFERENCES `articulos_tienda` (`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_inv` (`id_estudiante`, `id_articulo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 16. Tabla de Registro de Auditoría
DROP TABLE IF EXISTS `registro_auditoria`;
CREATE TABLE `registro_auditoria` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_usuario` INT NOT NULL,
  `accion` VARCHAR(100) NOT NULL,
  `detalles` JSON NULL,
  `ip_address` VARCHAR(45) NULL,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_audit_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 17. Tabla de Configuración Global
DROP TABLE IF EXISTS `configuracion_global`;
CREATE TABLE `configuracion_global` (
  `clave` VARCHAR(50) PRIMARY KEY,
  `valor` TEXT NULL,
  `descripcion` VARCHAR(255) NULL,
  `ultima_actualizacion` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------------
-- SEED DATA (Opcional: Crear admin inicial)
-- INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES ('admin@matatucas.com', '...', 'Administrador', 'administrador');
-- -----------------------------------------------------------------------------------
