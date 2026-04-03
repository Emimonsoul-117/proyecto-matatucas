from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from config import configuracion

# Inicialización de extensiones
bd = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login_page'
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."


def _ensure_codigo_curso_column(app):
    """Si la tabla cursos no tiene codigo_curso (BD creada antes del cambio de modelo), la añade."""
    with app.app_context():
        try:
            with bd.engine.begin() as conn:
                n = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'cursos'
                          AND COLUMN_NAME = 'codigo_curso'
                        """
                    )
                ).scalar()
                if n == 0:
                    conn.execute(
                        text(
                            "ALTER TABLE cursos ADD COLUMN codigo_curso VARCHAR(16) NULL UNIQUE AFTER id"
                        )
                    )
        except Exception as exc:
            app.logger.warning(
                "No se pudo asegurar la columna codigo_curso: %s. "
                "Si ves error 1054, ejecuta sql_alter_codigo_curso.sql en MySQL.",
                exc,
            )


def _ensure_bloqueado_inscripciones_column(app):
    """Si la tabla inscripciones no tiene bloqueado (BD antigua), la añade."""
    with app.app_context():
        try:
            with bd.engine.begin() as conn:
                n = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'inscripciones'
                          AND COLUMN_NAME = 'bloqueado'
                        """
                    )
                ).scalar()
                if n == 0:
                    conn.execute(
                        text(
                            "ALTER TABLE inscripciones "
                            "ADD COLUMN bloqueado BOOLEAN NOT NULL DEFAULT FALSE AFTER progreso"
                        )
                    )
        except Exception as exc:
            app.logger.warning(
                "No se pudo asegurar la columna inscripciones.bloqueado: %s. "
                "Si ves error de esquema, revisa el ALTER manualmente.",
                exc,
            )
def _ensure_estado_cursos_column(app):
    """Añade la columna estado a cursos si falta (necesario para Matatucas Pro)."""
    with app.app_context():
        try:
            with bd.engine.begin() as conn:
                n = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'cursos'
                          AND COLUMN_NAME = 'estado'
                        """
                    )
                ).scalar()
                if n == 0:
                    conn.execute(
                        text(
                            "ALTER TABLE cursos ADD COLUMN estado ENUM('borrador', 'revision', 'publicado') NOT NULL DEFAULT 'borrador' AFTER fecha_creacion"
                        )
                    )
        except Exception as exc:
            app.logger.warning("No se pudo asegurar la columna cursos.estado: %s", exc)


def crear_app(nombre_config='por_defecto'):
    app = Flask(__name__)
    app.config.from_object(configuracion[nombre_config])

    # Inicializar extensiones
    bd.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    _ensure_codigo_curso_column(app)

    _ensure_bloqueado_inscripciones_column(app)
    _ensure_estado_cursos_column(app)

    # Crea tablas nuevas faltantes (no altera tablas existentes).
    # Esto permite que nuevas entidades (p. ej. intentos_ejercicios) aparezcan
    # sin requerir migraciones completas mientras siga el esquema actual.
    with app.app_context():
        from . import modelos  # noqa: F401
        bd.create_all()

    # Registro de Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .cursos import cursos as cursos_blueprint
    app.register_blueprint(cursos_blueprint, url_prefix='/cursos')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    # Context processor: inyectar configuración del usuario en todos los templates
    @app.context_processor
    def inject_config_usuario():
        from flask_login import current_user as cu
        config = None
        falta_info = False
        if cu.is_authenticated:
            from .modelos import ConfiguracionUsuario, Estudiante
            config = ConfiguracionUsuario.query.get(cu.id)
            # Verificar si es estudiante y le falta info académica
            if cu.rol == 'estudiante':
                est = Estudiante.query.get(cu.id)
                if est and not est.carrera:
                    falta_info = True
        return dict(config_usuario=config, falta_info_academica=falta_info)

    return app

# Cargador de usuario para Flask-Login
from .modelos import Usuario

@login_manager.user_loader
def cargar_usuario(user_id):
    return Usuario.query.get(int(user_id))
