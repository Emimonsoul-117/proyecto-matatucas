-- Ejecutar una vez si la base ya existía sin esta columna (MySQL / MariaDB)
USE Matatucas_db;
ALTER TABLE cursos ADD COLUMN codigo_curso VARCHAR(16) NULL UNIQUE AFTER id;
