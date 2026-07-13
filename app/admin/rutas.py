from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from . import admin
from .. import bd
from ..modelos import Usuario, Estudiante, Docente, Curso, Inscripcion, RegistroAuditoria
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
    
    # Últimas acciones de auditoría
    ultimas_acciones = RegistroAuditoria.query.order_by(RegistroAuditoria.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard_admin.html', 
                           total_estudiantes=total_estudiantes,
                           total_docentes=total_docentes,
                           total_cursos=total_cursos,
                           total_inscripciones=total_inscripciones,
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
        else:
            from ..modelos import generar_numero_control_personalizado
            numero_control = generar_numero_control_personalizado(email)
            
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
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        numero_control = request.form.get('numero_control')
        nuevo_rol = request.form.get('rol')
        
        # Validar si existe el email en otro usuario
        existente_email = Usuario.query.filter_by(email=email).first()
        if existente_email and existente_email.id != usuario.id:
            flash('El correo electrónico ya está registrado por otro usuario.', 'peligro')
            return redirect(url_for('admin.editar_usuario', id=usuario.id))
            
        # Validar y procesar el número de control
        if numero_control:
            existente_nc = Usuario.query.filter_by(numero_control=numero_control).first()
            if existente_nc and existente_nc.id != usuario.id:
                flash(f'El número de control o matrícula "{numero_control}" ya está registrado.', 'peligro')
                return redirect(url_for('admin.editar_usuario', id=usuario.id))
            usuario.numero_control = numero_control
        else:
            # Si no se proporciona y no tiene uno, generarlo
            if not usuario.numero_control:
                from ..modelos import generar_numero_control_personalizado
                usuario.numero_control = generar_numero_control_personalizado(email)
        
        usuario.email = email
        usuario.nombre = nombre
        
        # Contraseña solo si se escribe algo nuevo
        password = request.form.get('password')
        if password:
            usuario.password_hash = generate_password_hash(password, method='scrypt')
            
        # Procesar cambio de rol
        if nuevo_rol and nuevo_rol != usuario.rol:
            rol_anterior = usuario.rol
            usuario.rol = nuevo_rol
            
            # De docente/admin a estudiante
            if nuevo_rol == 'estudiante':
                # Borrar perfil docente
                docente = Docente.query.get(usuario.id)
                if docente:
                    bd.session.delete(docente)
                # Asegurar perfil estudiante
                estudiante = Estudiante.query.get(usuario.id)
                if not estudiante:
                    estudiante = Estudiante(id_usuario=usuario.id)
                    bd.session.add(estudiante)
            
            # De estudiante a docente/administrador
            elif nuevo_rol in ('docente', 'administrador'):
                # Borrar perfil estudiante
                estudiante = Estudiante.query.get(usuario.id)
                if estudiante:
                    bd.session.delete(estudiante)
                # Asegurar perfil docente
                docente = Docente.query.get(usuario.id)
                if not docente:
                    especialidad = request.form.get('especialidad') or ('Administración' if nuevo_rol == 'administrador' else 'General')
                    docente = Docente(id_usuario=usuario.id, especialidad=especialidad)
                    bd.session.add(docente)
                    
            registrar_accion('CAMBIO_ROL', {
                'id_usuario': usuario.id,
                'nombre': usuario.nombre,
                'rol_anterior': rol_anterior,
                'nuevo_rol': nuevo_rol
            })
        else:
            # Si el rol sigue siendo docente/admin, actualizar especialidad si cambió
            if usuario.rol in ('docente', 'administrador'):
                especialidad = request.form.get('especialidad')
                docente = Docente.query.get(usuario.id)
                if docente:
                    docente.especialidad = especialidad or ('Administración' if usuario.rol == 'administrador' else 'General')
                else:
                    docente = Docente(id_usuario=usuario.id, especialidad=especialidad or ('Administración' if usuario.rol == 'administrador' else 'General'))
                    bd.session.add(docente)
        
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
    # Subquery: número de cursos por docente
    sub_cursos = (
        bd.session.query(Curso.id_docente, func.count(Curso.id).label('num_cursos'))
        .group_by(Curso.id_docente)
        .subquery()
    )

    # Subquery: total alumnos e inscripciones
    sub_inscritos_metricas = (
        bd.session.query(
            Curso.id_docente,
            func.count(Inscripcion.id).label('total_estudiantes'),
            func.avg(Inscripcion.progreso).label('avg_progreso')
        )
        .join(Inscripcion, Curso.id == Inscripcion.id_curso)
        .group_by(Curso.id_docente)
        .subquery()
    )

    # Query principal
    results = (
        bd.session.query(
            Usuario,
            Docente,
            func.coalesce(sub_cursos.c.num_cursos, 0).label('num_cursos'),
            func.coalesce(sub_inscritos_metricas.c.total_estudiantes, 0).label('total_estudiantes'),
            func.coalesce(sub_inscritos_metricas.c.avg_progreso, 0.0).label('avg_progreso')
        )
        .join(Docente, Usuario.id == Docente.id_usuario)
        .outerjoin(sub_cursos, Usuario.id == sub_cursos.c.id_docente)
        .outerjoin(sub_inscritos_metricas, Usuario.id == sub_inscritos_metricas.c.id_docente)
        .order_by(Usuario.nombre)
        .all()
    )

    docentes_metricas = []
    for usuario, docente, num_cursos, total_estudiantes, avg_progreso in results:
        docentes_metricas.append({
            'id': usuario.id,
            'nombre': usuario.nombre,
            'especialidad': docente.especialidad,
            'num_cursos': num_cursos,
            'total_estudiantes': total_estudiantes,
            'avg_progreso': round(float(avg_progreso), 1)
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
    
    if nuevo_estado in ['borrador', 'publicado']:
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


# ==============================================================================
# GAMIFICACIÓN (FASE 3)
# ==============================================================================

@admin.route('/gamificacion')
@login_required
@admin_required
def gamificacion():
    from ..modelos import Insignia, ArticuloTienda
    insignias = Insignia.query.all()
    articulos_tienda = ArticuloTienda.query.all()
    
    return render_template('admin/gamificacion.html', 
                           insignias=insignias, 
                           articulos_tienda=articulos_tienda)

@admin.route('/gamificacion/insignias/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def nueva_insignia():
    if request.method == 'POST':
        from ..modelos import Insignia
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        icono = request.form.get('icono')
        criterio = request.form.get('criterio')
        nivel = request.form.get('nivel_requerido', type=int)
        
        ins = Insignia(nombre=nombre, descripcion=descripcion, icono=icono,
                       criterio=criterio, nivel_requerido=nivel)
        bd.session.add(ins)
        bd.session.commit()
        
        flash('Insignia creada exitosamente.', 'exito')
        return redirect(url_for('admin.gamificacion'))
    
    return render_template('admin/gamificacion_formulario.html', tipo='insignia', item=None)

@admin.route('/gamificacion/articulos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_articulo():
    if request.method == 'POST':
        from ..modelos import ArticuloTienda
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        tipo_articulo = request.form.get('tipo_articulo')
        precio = request.form.get('precio', type=int)
        icono = request.form.get('icono')
        css_clase = request.form.get('css_clase')
        rareza = request.form.get('rareza')
        activo = request.form.get('activo') == 'on'
        
        art = ArticuloTienda(nombre=nombre, descripcion=descripcion, tipo=tipo_articulo,
                             precio=precio, icono=icono, css_clase=css_clase, rareza=rareza, activo=activo)
        bd.session.add(art)
        bd.session.commit()
        
        flash('Artículo creado exitosamente.', 'exito')
        return redirect(url_for('admin.gamificacion'))
    
    return render_template('admin/gamificacion_formulario.html', tipo='articulo', item=None)

@admin.route('/gamificacion/eliminar/<tipo>/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_gamificacion(tipo, id):
    from ..modelos import Insignia, ArticuloTienda
    if tipo == 'insignia':
        item = Insignia.query.get_or_404(id)
        bd.session.delete(item)
    elif tipo == 'articulo':
        item = ArticuloTienda.query.get_or_404(id)
        bd.session.delete(item)
    else:
        abort(400)
        
    bd.session.commit()
    flash('Elemento de gamificación eliminado.', 'exito')
    return redirect(url_for('admin.gamificacion'))
