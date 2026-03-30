"""
Script de migración: Agrega la columna 'secciones' (JSON) a la tabla lecciones.
Compatible con base de datos ya existente.

Ejecutar con: python migrar_secciones.py
"""
import sys
import os

# Asegurarse de estar en el directorio del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import crear_app, bd

def migrar():
    app = crear_app()
    with app.app_context():
        # Verificar si la columna ya existe
        from sqlalchemy import text, inspect
        inspector = inspect(bd.engine)
        cols = [c['name'] for c in inspector.get_columns('lecciones')]
        
        if 'secciones' not in cols:
            print("➕ Agregando columna 'secciones' a la tabla lecciones...")
            with bd.engine.connect() as conn:
                conn.execute(text("ALTER TABLE lecciones ADD COLUMN secciones JSON NULL;"))
                conn.commit()
            print("✅ Columna 'secciones' agregada exitosamente.")
        else:
            print("ℹ️  La columna 'secciones' ya existe. No se realizaron cambios.")

        print("✅ Migración completada.")

if __name__ == '__main__':
    migrar()
