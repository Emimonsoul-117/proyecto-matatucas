from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'administrador':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def docente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.rol != 'docente' and current_user.rol != 'administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def curso_owner_required(f):
    """Verifica que el usuario actual sea el dueño del curso o administrador.
    
    La función decorada DEBE recibir `id_curso` o `id` como argumento de ruta.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        
        from .modelos import Curso
        curso_id = kwargs.get('id_curso') or kwargs.get('id')
        if not curso_id:
            abort(400)
        
        curso = Curso.query.get_or_404(curso_id)
        if curso.id_docente != current_user.id and current_user.rol != 'administrador':
            flash('No tienes permiso para realizar esta acción en este curso.', 'peligro')
            return redirect(url_for('cursos.ver_curso', id=curso_id))
        
        # Inyectar el curso en kwargs para evitar query duplicada
        kwargs['_curso'] = curso
        return f(*args, **kwargs)
    return decorated_function
