from app import crear_app, bd
from app.modelos import Insignia

app = crear_app()

def sembrar_insignias():
    with app.app_context():
        # Crear tablas si no existen (Insignias, InsigniaEstudiante)
        print("Verificando tablas de base de datos...")
        bd.create_all()
        
        insignias = [
            # Nivel: Constancia
            {
                'nombre': 'Estudiante Diligente',
                'descripcion': 'Mantén una racha de estudio de 3 días seguidos.',
                'icono': 'bi-calendar-check',
                'criterio': 'racha_3',
                'nivel': 1
            },
            {
                'nombre': 'Hábito de Acero',
                'descripcion': 'Mantén una racha inquebrantable de 7 días. ¡Solo para los comprometidos!',
                'icono': 'bi-fire',
                'criterio': 'racha_7',
                'nivel': 2
            },
            {
                'nombre': 'Leyenda de la Constancia',
                'descripcion': '¡30 días seguidos de estudio! Eres imparable.',
                'icono': 'bi-trophy-fill',
                'criterio': 'racha_30',
                'nivel': 3
            },
            
            # Nivel: Puntos / Experiencia
            {
                'nombre': 'Aprendiz Matemático',
                'descripcion': 'Acumula tus primeros 1000 puntos de experiencia.',
                'icono': 'bi-star',
                'criterio': 'puntos_1000',
                'nivel': 1
            },
            {
                'nombre': 'Genio en Potencia',
                'descripcion': 'Alcanza los 5000 puntos. Demuestra tu dominio.',
                'icono': 'bi-lightning-charge-fill',
                'criterio': 'puntos_5000',
                'nivel': 2
            },

            # Nivel: Logros Específicos
            {
                'nombre': 'Explorador del Conocimiento',
                'descripcion': 'Inscríbete en al menos 3 cursos diferentes.',
                'icono': 'bi-compass',
                'criterio': 'explorador',
                'nivel': 1
            },
            {
                'nombre': 'Maestría Total',
                'descripcion': 'Completa un curso al 100%. La perfección es posible.',
                'icono': 'bi-award-fill',
                'criterio': 'maestro',
                'nivel': 3
            }
        ]

        print("Creando insignias...")
        for data in insignias:
            existe = Insignia.query.filter_by(criterio=data['criterio']).first()
            if not existe:
                nueva = Insignia(
                    nombre=data['nombre'], 
                    descripcion=data['descripcion'],
                    icono=data['icono'],
                    criterio=data['criterio'],
                    nivel_requerido=data['nivel']
                )
                bd.session.add(nueva)
                print(f"Creada: {data['nombre']}")
            else:
                print(f"Existente: {data['nombre']}")
        
        bd.session.commit()
        print("¡Insignias sembradas exitosamente!")

if __name__ == '__main__':
    sembrar_insignias()
