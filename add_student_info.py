from app import crear_app, bd
from sqlalchemy import text

app = crear_app('desarrollo')
with app.app_context():
    with bd.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE estudiantes ADD COLUMN carrera VARCHAR(100);"))
        except Exception as e:
            print(f"Error con carrera: {e}")
            
        try:
            conn.execute(text("ALTER TABLE estudiantes ADD COLUMN semestre INT;"))
        except Exception as e:
            print(f"Error con semestre: {e}")
            
        try:
            conn.execute(text("ALTER TABLE estudiantes ADD COLUMN grupo VARCHAR(10);"))
        except Exception as e:
            print(f"Error con grupo: {e}")

        conn.commit()
    print("Migración completada.")
