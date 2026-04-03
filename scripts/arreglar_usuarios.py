from app import crear_app, bd
from app.modelos import Usuario, Docente
from werkzeug.security import generate_password_hash

app = crear_app()

def arreglar_admin_y_docentes():
    with app.app_context():
        print("Iniciando reparación de usuarios...")
        
        # 1. Asegurar Admin
        email = 'admin@mathai.com'
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            print("Creando Admin...")
            usuario = Usuario(
                email=email,
                nombre='Administrador Sistema',
                password_hash=generate_password_hash('admin123', method='scrypt'),
                rol='administrador',
                numero_control='ADM001'
            )
            bd.session.add(usuario)
            bd.session.commit()
        
        # Asegurar que Admin esté en tabla Docentes (para poder crear cursos)
        docente_admin = Docente.query.filter_by(id_usuario=usuario.id).first()
        if not docente_admin:
            print("Añadiendo Admin a tabla Docentes...")
            docente_admin = Docente(id_usuario=usuario.id, especialidad='Administración')
            bd.session.add(docente_admin)
            bd.session.commit()
            
        print("¡Admin reparado!")

        # 2. Reparar otros docentes que existan solo en usuarios
        usuarios_docentes = Usuario.query.filter_by(rol='docente').all()
        count = 0
        for u in usuarios_docentes:
            d = Docente.query.filter_by(id_usuario=u.id).first()
            if not d:
                print(f"Reparando docente: {u.email}")
                nuevo_docente = Docente(id_usuario=u.id, especialidad='Matemáticas General')
                bd.session.add(nuevo_docente)
                count += 1
        
        if count > 0:
            bd.session.commit()
            print(f"Se repararon {count} docentes inconsistentes.")
        else:
            print("No se encontraron docentes inconsistentes.")

if __name__ == '__main__':
    arreglar_admin_y_docentes()
