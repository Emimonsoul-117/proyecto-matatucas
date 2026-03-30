"""Migración: Configuración de usuario + Tienda de recompensas."""
from app import crear_app, bd
from sqlalchemy import text

app = crear_app('desarrollo')
with app.app_context():
    with bd.engine.connect() as conn:
        stmts = [
            # --- Tabla configuracion_usuario ---
            """
            CREATE TABLE IF NOT EXISTS configuracion_usuario (
                id_usuario INT PRIMARY KEY,
                tema VARCHAR(10) NOT NULL DEFAULT 'claro',
                ocultar_ranking TINYINT(1) NOT NULL DEFAULT 0,
                tamano_fuente VARCHAR(10) NOT NULL DEFAULT 'normal',
                notif_nuevos_cursos TINYINT(1) NOT NULL DEFAULT 1,
                notif_racha TINYINT(1) NOT NULL DEFAULT 1,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
            )
            """,
            # --- Tabla articulos_tienda ---
            """
            CREATE TABLE IF NOT EXISTS articulos_tienda (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion VARCHAR(255),
                tipo ENUM('avatar','marco') NOT NULL,
                precio INT NOT NULL DEFAULT 0,
                icono VARCHAR(255),
                css_clase VARCHAR(255),
                rareza ENUM('comun','raro','epico','legendario') NOT NULL DEFAULT 'comun',
                activo TINYINT(1) NOT NULL DEFAULT 1
            )
            """,
            # --- Tabla inventario_estudiante ---
            """
            CREATE TABLE IF NOT EXISTS inventario_estudiante (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_estudiante INT NOT NULL,
                id_articulo INT NOT NULL,
                fecha_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_usuario),
                FOREIGN KEY (id_articulo) REFERENCES articulos_tienda(id),
                UNIQUE KEY unique_inv (id_estudiante, id_articulo)
            )
            """,
            # --- Columnas extra en estudiantes ---
            "ALTER TABLE estudiantes ADD COLUMN monedas INT NOT NULL DEFAULT 0",
            "ALTER TABLE estudiantes ADD COLUMN avatar_activo VARCHAR(255) DEFAULT NULL",
            "ALTER TABLE estudiantes ADD COLUMN marco_activo VARCHAR(255) DEFAULT NULL",
        ]

        for sql in stmts:
            try:
                conn.execute(text(sql))
            except Exception as e:
                msg = str(e)
                if 'Duplicate column' in msg or 'already exists' in msg:
                    pass
                else:
                    print(f"  ⚠ {msg[:120]}")
        conn.commit()
    print("✅ Migración de Configuración y Tienda completada.")
