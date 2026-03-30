from app import crear_app, bd
from sqlalchemy import text

app = crear_app('desarrollo')
with app.app_context():
    with bd.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE estudiantes ADD COLUMN fecha_actualizacion_semestre DATETIME;"))
            conn.execute(text("UPDATE estudiantes SET fecha_actualizacion_semestre = CURRENT_TIMESTAMP WHERE fecha_actualizacion_semestre IS NULL;"))
            conn.commit()
            print("Columna fecha_actualizacion_semestre agregada.")
        except Exception as e:
            print(f"Error: {e}")
