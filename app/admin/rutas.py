from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import admin
from .. import bd
from ..modelos import Usuario, Estudiante, Docente
from werkzeug.security import generate_password_hash

# Decorador personalizado (si no está global, lo definimos o importamos)
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            flash('Acceso no autorizado. Se requieren privilegios de administrador.', 'peligro')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    # Obtener parámetros de filtro
    rol = request.args.get('rol')
    busqueda = request.args.get('q')
    
    query = Usuario.query
    
    if rol:
        query = query.filter_by(rol=rol)
    
    if busqueda:
        # Búsqueda simple por nombre o email
        query = query.filter(
            (Usuario.nombre.ilike(f'%{busqueda}%')) | 
            (Usuario.email.ilike(f'%{busqueda}%'))
        )
        
    usuarios = query.order_by(Usuario.nombre).all()
    return render_template('admin/lista_usuarios.html', usuarios=usuarios, rol_filtro=rol)

@admin.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        password = request.form.get('password')
        rol = request.form.get('rol')
        numero_control = request.form.get('numero_control')
        especialidad = request.form.get('especialidad') # Solo para docentes
        
        # Validar si existe email
        if Usuario.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'peligro')
            return redirect(url_for('admin.crear_usuario'))
            
        # Validar si existe número de control (si se proporciona)
        if numero_control:
            if Usuario.query.filter_by(numero_control=numero_control).first():
                flash(f'El número de control o matrícula "{numero_control}" ya está registrado.', 'peligro')
                return redirect(url_for('admin.crear_usuario'))
            
        nuevo_usuario = Usuario(
            email=email,
            nombre=nombre,
            password_hash=generate_password_hash(password, method='scrypt'),
            rol=rol,
            numero_control=numero_control
        )
        
        bd.session.add(nuevo_usuario)
        bd.session.commit()
        
        # Crear perfil específico
        if rol == 'estudiante':
            perfil = Estudiante(id_usuario=nuevo_usuario.id)
            bd.session.add(perfil)
        elif rol == 'docente':
            perfil = Docente(id_usuario=nuevo_usuario.id, especialidad=especialidad or 'General')
            bd.session.add(perfil)
        elif rol == 'administrador':
            # Opcional: admin también puede ser docente para gestionar cursos
            perfil = Docente(id_usuario=nuevo_usuario.id, especialidad='Administración')
            bd.session.add(perfil)
            
        bd.session.commit()
        flash(f'Usuario {nombre} ({rol}) creado exitosamente.', 'exito')
        return redirect(url_for('admin.lista_usuarios'))
        
    return render_template('admin/formulario_usuario.html', titulo="Crear Usuario")

@admin.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        usuario.email = request.form.get('email')
        usuario.nombre = request.form.get('nombre')
        usuario.numero_control = request.form.get('numero_control')
        
        # Contraseña solo si se escribe algo nuevo
        password = request.form.get('password')
        if password:
            usuario.password_hash = generate_password_hash(password, method='scrypt')
            
        # Actualizar datos específicos del rol actual
        if usuario.rol == 'docente':
            especialidad = request.form.get('especialidad')
            docente = Docente.query.get(usuario.id)
            if docente:
                docente.especialidad = especialidad
        
        try:
            bd.session.commit()
            flash('Usuario actualizado correctamente.', 'exito')
            return redirect(url_for('admin.lista_usuarios'))
        except Exception as e:
            bd.session.rollback()
            flash(f'Error al actualizar: {e}', 'peligro')
            
    return render_template('admin/formulario_usuario.html', titulo="Editar Usuario", usuario=usuario)

@admin.route('/usuarios/<int:id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'peligro')
        return redirect(url_for('admin.lista_usuarios'))
        
    # Al eliminar usuario, SQLAlchemy manejo cascada si está configurado, 
    # si no, habría que borrar dependencias manual. 
    # Por ahora asumimos borrado básico.
    
    # Borrar perfil asociado manualmente para asegurar
    if usuario.rol == 'estudiante':
        est = Estudiante.query.get(id)
        if est: bd.session.delete(est)
    elif usuario.rol == 'docente' or usuario.rol == 'administrador':
        doc = Docente.query.get(id)
        if doc: bd.session.delete(doc)
        
    bd.session.delete(usuario)
    bd.session.commit()
    flash('Usuario eliminado permanentemente.', 'exito')
    return redirect(url_for('admin.lista_usuarios'))
