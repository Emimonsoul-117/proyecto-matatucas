from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import admin
from .. import bd
from ..modelos import Usuario, Estudiante, Docente, Curso, Inscripcion, RegistroAuditoria, ConfiguracionGlobal
from werkzeug.security import generate_password_hash
from ..servicios.auditoria_servicio import registrar_accion
from ..servicios.reportes_servicio import generar_reporte_docente_pdf
from flask import send_file
import io

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

@admin.route('/')
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Métricas de resumen
    total_estudiantes = Usuario.query.filter_by(rol='estudiante').count()
    total_docentes = Usuario.query.filter_by(rol='docente').count()
    total_cursos = Curso.query.count()
    total_inscripciones = Inscripcion.query.count()
    
    # Cursos en revisión
    cursos_pendientes = Curso.query.filter_by(estado='revision').all()
    
    # Últimas acciones de auditoría
    ultimas_acciones = RegistroAuditoria.query.order_by(RegistroAuditoria.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard_admin.html', 
                           total_estudiantes=total_estudiantes,
                           total_docentes=total_docentes,
                           total_cursos=total_cursos,
                           total_inscripciones=total_inscripciones,
                           cursos_pendientes=cursos_pendientes,
                           ultimas_acciones=ultimas_acciones)

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
    
    registrar_accion('ELIMINAR_USUARIO', {'id_eliminado': id, 'nombre': usuario.nombre})
    
    flash('Usuario eliminado permanentemente.', 'exito')
    return redirect(url_for('admin.lista_usuarios'))

@admin.route('/docentes')
@login_required
@admin_required
def lista_docentes():
    docentes = Docente.query.all()
    docentes_metricas = []
    
    for d in docentes:
        usuario = Usuario.query.get(d.id_usuario)
        cursos = Curso.query.filter_by(id_docente=d.id_usuario).all()
        total_estudiantes = 0
        progreso_acumulado = 0
        total_inscripciones = 0
        
        for c in cursos:
            inscs = Inscripcion.query.filter_by(id_curso=c.id).all()
            count = len(inscs)
            total_estudiantes += count
            total_inscripciones += count
            for i in inscs:
                progreso_acumulado += i.progreso
        
        avg_progreso = round(progreso_acumulado / total_inscripciones, 1) if total_inscripciones > 0 else 0
        
        docentes_metricas.append({
            'id': d.id_usuario,
            'nombre': usuario.nombre,
            'especialidad': d.especialidad,
            'num_cursos': len(cursos),
            'total_estudiantes': total_estudiantes,
            'avg_progreso': avg_progreso
        })
        
    return render_template('admin/lista_docentes.html', docentes=docentes_metricas)

@admin.route('/docentes/<int:id>/reporte')
@login_required
@admin_required
def descargar_reporte_docente(id):
    usuario = Usuario.query.get_or_404(id)
    docente = Docente.query.get_or_404(id)
    cursos = Curso.query.filter_by(id_docente=id).all()
    
    cursos_data = []
    for c in cursos:
        inscs = Inscripcion.query.filter_by(id_curso=c.id).all()
        avg = round(sum([i.progreso for i in inscs]) / len(inscs), 1) if inscs else 0
        cursos_data.append({
            'titulo': c.titulo,
            'estudiantes': len(inscs),
            'progreso_promedio': avg
        })
    
    pdf_buffer = generar_reporte_docente_pdf(usuario.nombre, cursos_data)
    
    registrar_accion('GENERAR_REPORTE_PDF', {'docente': usuario.nombre})
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'Reporte_{usuario.nombre.replace(" ", "_")}.pdf',
        mimetype='application/pdf'
    )

@admin.route('/auditoria')
@login_required
@admin_required
def lista_auditoria():
    registros = RegistroAuditoria.query.order_by(RegistroAuditoria.timestamp.desc()).all()
    return render_template('admin/lista_auditoria.html', registros=registros)

@admin.route('/cursos/revision')
@login_required
@admin_required
def lista_revision_cursos():
    cursos = Curso.query.filter_by(estado='revision').all()
    return render_template('admin/revision_cursos.html', cursos=cursos)

@admin.route('/metricas')
@login_required
@admin_required
def metricas():
    # Top 5 Cursos populares
    cursos_top = bd.session.query(
        Curso, 
        bd.func.count(Inscripcion.id).label('total_alumnos')
    ).outerjoin(Inscripcion, Curso.id == Inscripcion.id_curso)\
     .group_by(Curso.id)\
     .order_by(bd.desc('total_alumnos'))\
     .limit(5).all()

    # Dificultad de ejercicios (ejercicios con más fallos)
    from ..modelos import Ejercicio, IntentoEjercicio
    peores_ejercicios = bd.session.query(
        Ejercicio,
        bd.func.count(IntentoEjercicio.id).label('fallos')
    ).join(IntentoEjercicio, Ejercicio.id == IntentoEjercicio.id_ejercicio)\
     .filter(IntentoEjercicio.es_correcta == False)\
     .group_by(Ejercicio.id)\
     .order_by(bd.desc('fallos'))\
     .limit(5).all()

    # Demografía por carreras
    carreras = bd.session.query(
        Estudiante.carrera,
        bd.func.count(Estudiante.id_usuario).label('total')
    ).group_by(Estudiante.carrera).all()
    
    # Preparar datos para Chart.js
    carreras_labels = [c[0] if c[0] else "Sin Especificar" for c in carreras]
    carreras_datos = [c[1] for c in carreras]

    # Distribución de insignias
    from ..modelos import InsigniaEstudiante, Insignia
    insignias = bd.session.query(
        Insignia.nombre,
        bd.func.count(InsigniaEstudiante.id).label('total')
    ).outerjoin(InsigniaEstudiante, Insignia.id == InsigniaEstudiante.id_insignia)\
     .group_by(Insignia.id).all()

    insignias_labels = [i[0] for i in insignias]
    insignias_datos = [i[1] for i in insignias]

    return render_template('admin/metricas.html',
                           cursos_top=cursos_top,
                           peores_ejercicios=peores_ejercicios,
                           carreras_labels=carreras_labels,
                           carreras_datos=carreras_datos,
                           insignias_labels=insignias_labels,
                           insignias_datos=insignias_datos)

@admin.route('/cursos/<int:id>/cambiar-estado', methods=['POST'])
@login_required
@admin_required
def cambiar_estado_curso(id):
    curso = Curso.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    
    if nuevo_estado in ['borrador', 'revision', 'publicado']:
        estado_anterior = curso.estado
        curso.estado = nuevo_estado
        bd.session.commit()
        
        registrar_accion('CAMBIO_ESTADO_CURSO', {
            'id_curso': curso.id,
            'titulo': curso.titulo,
            'nuevo_estado': nuevo_estado,
            'estado_anterior': estado_anterior
        })
        
        flash(f'Estado del curso "{curso.titulo}" actualizado a {nuevo_estado}.', 'exito')
    
    return redirect(url_for('admin.dashboard'))
