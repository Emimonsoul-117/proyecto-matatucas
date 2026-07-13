# Matatucas LMS - Visión General del Proyecto

## Descripción
Matatucas es un LMS (Learning Management System) orientado al Tecnológico Nacional de México (TecNM) - Instituto Tecnológico Superior de Teziutlán. Permite gestión de cursos con lecciones por secciones (teoría, video, ejercicios), gamificación (puntos, rachas, insignias, tienda), y analíticas académicas.

## Stack Tecnológico
- **Backend**: Flask 3.0 (Python), SQLAlchemy 2.0, Flask-Login, Flask-WTF (CSRF)
- **Base de datos**: MySQL/MariaDB 10.4 vía XAMPP (conector: `mysql-connector-python`)
- **Autenticación**: Microsoft SSO (Azure AD / Entra ID) vía `msal`
- **IA**: Google Generative AI (`google-generativeai`) para generación de ejercicios
- **Frontend**: HTML/Jinja2, CSS vanilla (variables.css + estilos.css), Bootstrap Icons, KaTeX para ecuaciones
- **Exportación**: openpyxl (Excel), reportlab (PDF)
- **Servidor**: Flask dev server con HTTPS adhoc (`pyOpenSSL`), `host=0.0.0.0`

## Estructura de Directorios
```
proyecto Matatucas/
├── run.py                    # Entry point
├── config.py                 # Configuraciones (dev/prod)
├── esquema.sql               # Schema SQL completo
├── requirements.txt
├── .env                      # Credenciales Microsoft SSO + DB
├── app/
│   ├── __init__.py           # App factory (crear_app), migraciones auto
│   ├── modelos.py            # Todos los modelos SQLAlchemy
│   ├── decoradores.py        # admin_required, docente_required, curso_owner_required
│   ├── auth/                 # Blueprint: login Microsoft SSO
│   ├── main/                 # Blueprint: dashboard, perfil, leaderboard, tienda, config
│   ├── cursos/               # Blueprint: CRUD cursos, lecciones, ejercicios, inscripciones
│   ├── admin/                # Blueprint: gestión usuarios, métricas, auditoría
│   ├── docente/              # Blueprint: dashboard docente con métricas
│   ├── servicios/            # Capa de servicios
│   │   ├── ia_servicio.py
│   │   ├── gamificacion_servicio.py
│   │   ├── excel_servicio.py
│   │   ├── auditoria_servicio.py
│   │   └── reportes_servicio.py
│   ├── static/css/           # variables.css, estilos.css
│   └── templates/            # Jinja2 templates organizados por blueprint
└── scripts/                  # Scripts utilitarios
```

## Roles de Usuario
1. **Estudiante**: Se inscribe a cursos, completa lecciones, resuelve ejercicios, gana puntos/insignias
2. **Docente**: Crea/gestiona cursos, ve analíticas de alumnos, exporta Excel, duplica cursos
3. **Administrador**: Todo lo del docente + gestión de usuarios, métricas globales, auditoría

## Convenciones de Código
- **Idioma del código**: Variables, funciones, comentarios y templates en **español**
- **ORM**: SQLAlchemy con instancia llamada `bd` (no `db`)
- **Blueprints**: Registrados en `crear_app()` dentro de `app/__init__.py`
- **Templates**: Extienden `base.html`, usan `{% block contenido %}`
- **Flash messages**: Categorías: 'exito', 'peligro', 'advertencia', 'info'
- **CSRF**: Protegido globalmente por Flask-WTF, tokens en forms con `{{ csrf_token() }}`
- **Migraciones**: No usa Alembic; usa funciones `_ensure_*` en `__init__.py` + `bd.create_all()`
