# Matatucas LMS - Base de Datos

## Motor
MariaDB 10.4.32 (XAMPP local), conector `mysql-connector-python`

## Tablas Principales

### usuarios
| Columna | Tipo | Notas |
|---------|------|-------|
| id | INT PK | Auto-increment |
| email | VARCHAR(120) UNIQUE | Correo institucional |
| password_hash | VARCHAR(256) NULL | NULL para SSO |
| nombre | VARCHAR(100) | Nombre completo |
| numero_control | VARCHAR(20) UNIQUE | Matrícula (solo estudiantes) |
| microsoft_id | VARCHAR(100) UNIQUE | OID de Azure AD |
| rol | ENUM('administrador','docente','estudiante') | |
| fecha_registro | DATETIME | DEFAULT NOW() |

### estudiantes
| Columna | Tipo | Notas |
|---------|------|-------|
| id_usuario | INT PK FK→usuarios | 1:1 con usuarios |
| puntos_totales | INT DEFAULT 0 | Gamificación |
| racha_dias | INT DEFAULT 0 | Días consecutivos |
| ultimo_login | DATETIME NULL | |
| carrera | VARCHAR(100) NULL | Info académica |
| semestre | INT NULL | |
| grupo | VARCHAR(10) NULL | |
| monedas | INT DEFAULT 0 | Para tienda |
| avatar_activo | VARCHAR(255) NULL | |
| marco_activo | VARCHAR(255) NULL | |

### docentes
| Columna | Tipo |
|---------|------|
| id_usuario | INT PK FK→usuarios |
| especialidad | VARCHAR(100) |

### cursos
| Columna | Tipo | Notas |
|---------|------|-------|
| id | INT PK | |
| codigo_curso | VARCHAR(16) UNIQUE | Formato MTC-XXXXXXXX |
| titulo | VARCHAR(150) | |
| descripcion | TEXT | |
| nivel | ENUM('basico','intermedio','avanzado') | |
| id_docente | INT FK→docentes | |
| fecha_creacion | DATETIME | |
| estado | ENUM('borrador','publicado') | Sin 'revision' |
| visibilidad | ENUM('global','privado') | |

### lecciones
| Columna | Tipo | Notas |
|---------|------|-------|
| id | INT PK | |
| id_curso | INT FK→cursos | CASCADE delete |
| titulo | VARCHAR(150) | |
| orden | INT | Secuencia dentro del curso |
| contenido_teoria | TEXT | Legacy: HTML |
| secciones | JSON | Lista de bloques [{tipo, contenido, ...}] |

### Otras tablas
- **videos**: id, id_leccion FK, url_youtube, titulo
- **ejercicios**: id, id_leccion FK, enunciado, tipo (ENUM), opciones (JSON), respuesta_correcta, dificultad
- **intentos_ejercicios**: id, id_estudiante FK, id_ejercicio FK, intento_num, respuesta_usuario, es_correcta, puntaje, fecha
- **inscripciones**: id, id_estudiante FK, id_curso FK, fecha, progreso, bloqueado
- **insignias**: id, nombre, descripcion, icono, criterio, nivel_requerido
- **insignias_estudiantes**: id, id_estudiante FK, id_insignia FK, fecha
- **lecciones_completadas**: id, id_estudiante FK, id_leccion FK, fecha (UNIQUE constraint)
- **configuracion_usuario**: id_usuario PK FK, tema, ocultar_ranking, tamano_fuente, notifs
- **articulos_tienda**: id, nombre, tipo (avatar/marco), precio, icono, css_clase, rareza, activo
- **inventario_estudiante**: id, id_estudiante FK, id_articulo FK, fecha (UNIQUE constraint)
- **registro_auditoria**: id, id_usuario FK, accion, detalles (JSON), ip_address, timestamp
- **configuracion_global**: clave PK, valor, descripcion, ultima_actualizacion

## Convenciones de Migración
- Sin Alembic: migraciones inline en `app/__init__.py` con funciones `_ensure_*`
- Verifican existencia de columnas vía `information_schema.COLUMNS`
- Ejecutan `ALTER TABLE ADD COLUMN` si falta
- `bd.create_all()` crea tablas completamente nuevas
- `esquema.sql` en raíz contiene el schema completo para instalaciones limpias
