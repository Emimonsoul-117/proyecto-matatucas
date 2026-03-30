-- Script de migración para agregar soporte Microsoft SSO
-- Ejecutar en la base de datos Matatucas_db existente

USE Matatucas_db;

-- Hacer password_hash nullable (ya no se requiere para login con Microsoft)
ALTER TABLE usuarios MODIFY COLUMN password_hash VARCHAR(256) NULL;

-- Agregar columna microsoft_id para vincular con Azure AD
ALTER TABLE usuarios ADD COLUMN microsoft_id VARCHAR(100) UNIQUE NULL AFTER numero_control;
