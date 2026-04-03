"""Sembrar artículos de tienda: Avatares y Marcos."""
from app import crear_app, bd
from app.modelos import ArticuloTienda

app = crear_app('desarrollo')
with app.app_context():
    # Limpiar catálogo anterior (opcional)
    ArticuloTienda.query.delete()
    
    articulos = [
        # ===== AVATARES =====
        # Comunes (baratos)
        ArticuloTienda(nombre='Gato Estudioso', descripcion='Un minino enfocado en las matemáticas', tipo='avatar', precio=100, icono='🐱', rareza='comun'),
        ArticuloTienda(nombre='Robot Calculador', descripcion='Procesa ecuaciones a toda velocidad', tipo='avatar', precio=100, icono='🤖', rareza='comun'),
        ArticuloTienda(nombre='Búho Sabio', descripcion='El más sabio de la clase nocturna', tipo='avatar', precio=150, icono='🦉', rareza='comun'),
        ArticuloTienda(nombre='Cerebrito', descripcion='Pura materia gris sin parar', tipo='avatar', precio=150, icono='🧠', rareza='comun'),
        
        # Raros
        ArticuloTienda(nombre='Ninja del Cálculo', descripcion='Resuelve problemas en las sombras', tipo='avatar', precio=350, icono='🥷', rareza='raro'),
        ArticuloTienda(nombre='Mago Matemático', descripcion='Los números obedecen a su varita', tipo='avatar', precio=350, icono='🧙', rareza='raro'),
        ArticuloTienda(nombre='Científica Loca', descripcion='Experimenta con fórmulas explosivas', tipo='avatar', precio=400, icono='🧪', rareza='raro'),
        
        # Épicos
        ArticuloTienda(nombre='Astronauta Estelar', descripcion='Explora las matemáticas del cosmos', tipo='avatar', precio=750, icono='🧑‍🚀', rareza='epico'),
        ArticuloTienda(nombre='Dragón del Álgebra', descripcion='Escupe ecuaciones de fuego', tipo='avatar', precio=800, icono='🐉', rareza='epico'),
        
        # Legendarios
        ArticuloTienda(nombre='Unicornio Cósmico', descripcion='Criatura legendaria. Pocos lo han visto.', tipo='avatar', precio=1500, icono='🦄', rareza='legendario'),
        ArticuloTienda(nombre='Fénix Infinito', descripcion='Renace con cada examen reprobado. Nunca se rinde.', tipo='avatar', precio=2000, icono='🔥', rareza='legendario'),

        # ===== MARCOS =====
        # Comunes
        ArticuloTienda(nombre='Marco Bronce', descripcion='Un borde clásico de bronce', tipo='marco', precio=200, icono='🥉', css_clase='marco-bronce', rareza='comun'),
        ArticuloTienda(nombre='Marco Plata', descripcion='Elegante borde plateado', tipo='marco', precio=300, icono='🥈', css_clase='marco-plata', rareza='comun'),
        
        # Raros
        ArticuloTienda(nombre='Marco Oro', descripcion='Reluce con un aura dorada', tipo='marco', precio=500, icono='🥇', css_clase='marco-oro', rareza='raro'),
        
        # Épicos
        ArticuloTienda(nombre='Marco de Fuego', descripcion='Tu avatar arde en llamas épicas', tipo='marco', precio=800, icono='🔥', css_clase='marco-fuego', rareza='epico'),
        ArticuloTienda(nombre='Marco Neón', descripcion='Brilla con energía cibernética', tipo='marco', precio=900, icono='💎', css_clase='marco-neon', rareza='epico'),

        # Legendarios
        ArticuloTienda(nombre='Marco Diamante', descripcion='Refracta la luz en un arcoíris cambiante', tipo='marco', precio=1500, icono='💠', css_clase='marco-diamante', rareza='legendario'),
        ArticuloTienda(nombre='Marco Cósmico', descripcion='Los colores del universo giran a tu alrededor', tipo='marco', precio=2500, icono='🌌', css_clase='marco-cosmico', rareza='legendario'),
    ]
    
    bd.session.add_all(articulos)
    bd.session.commit()
    print(f"✅ {len(articulos)} artículos sembrados en la tienda.")
