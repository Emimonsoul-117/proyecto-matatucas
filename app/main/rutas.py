from flask import render_template, request, flash, redirect, url_for
from . import main
from flask_login import login_required, current_user
from .. import bd
from ..modelos import progreso_por_lecciones_completadas

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    from ..modelos import Curso, Inscripcion, Estudiante
    
    cursos_usuario = []
    
    if current_user.rol == 'estudiante':
        # Obtener cursos inscritos alineando progreso con lecciones completadas
        inscripciones = Inscripcion.query.filter_by(id_estudiante=current_user.id).all()
        cursos_usuario = []
        necesita_commit = False
        for i in inscripciones:
            curso = Curso.query.get(i.id_curso)
            if not curso:
                continue
            real = progreso_por_lecciones_completadas(current_user.id, curso.id)
            if abs(i.progreso - real) > 0.02:
                i.progreso = real
                necesita_commit = True
            cursos_usuario.append({'curso': curso, 'progreso': real})
        if necesita_commit:
            bd.session.commit()
    elif current_user.rol == 'docente' or current_user.rol == 'administrador':
        # Obtener cursos creados
        cursos_raw = Curso.query.filter_by(id_docente=current_user.id).all()
        cursos_usuario = [{'curso': c, 'progreso': None} for c in cursos_raw]
    
    return render_template('dashboard.html', nombre=current_user.nombre, cursos=cursos_usuario)

@main.route('/perfil')
@login_required
def perfil():
    from ..modelos import Estudiante, Insignia
    
    es_estudiante = current_user.rol == 'estudiante'
    estudiante = Estudiante.query.get(current_user.id) if es_estudiante else None
    
    # Si no es estudiante, mostrar la versión básica del perfil
    if not es_estudiante:
        return render_template('main/perfil.html', usuario=current_user, es_estudiante=False)

    # Obtener todas las insignias para mostrar ganadas vs pendientes
    todas_insignias = Insignia.query.order_by(Insignia.nivel_requerido).all()
    # IDs de insignias que ya tiene
    mis_insignias_ids = [l.id_insignia for l in estudiante.logros] if estudiante else []
    
    # Calcular nivel basado en puntos (ej: cada 1000 pts es un nivel)
    puntos_totales = estudiante.puntos_totales if estudiante else 0
    nivel_actual = (puntos_totales // 1000) + 1
    puntos_siguiente_nivel = 1000 - (puntos_totales % 1000)

    return render_template('main/perfil.html', 
                           usuario=current_user, 
                           estudiante=estudiante, 
                           insignias=todas_insignias, 
                           mis_insignias_ids=mis_insignias_ids,
                           nivel=nivel_actual,
                           puntos_next=puntos_siguiente_nivel,
                           es_estudiante=True)

@main.route('/leaderboard')
@login_required
def leaderboard():
    from ..modelos import Estudiante, Usuario
    # Top 20 estudiantes por puntos
    top_estudiantes = (
        bd.session.query(Estudiante, Usuario)
        .join(Usuario, Estudiante.id_usuario == Usuario.id)
        .order_by(Estudiante.puntos_totales.desc())
        .limit(20)
        .all()
    )
    
    mi_posicion = None
    if current_user.rol == 'estudiante':
        todos = (
            bd.session.query(Estudiante)
            .order_by(Estudiante.puntos_totales.desc())
            .all()
        )
        for i, e in enumerate(todos):
            if e.id_usuario == current_user.id:
                mi_posicion = i + 1
                break
    
    return render_template('main/leaderboard.html',
                           top_estudiantes=top_estudiantes,
                           mi_posicion=mi_posicion)


@main.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    from ..modelos import ConfiguracionUsuario, Estudiante
    
    config = ConfiguracionUsuario.query.get(current_user.id)
    if not config:
        config = ConfiguracionUsuario(id_usuario=current_user.id)
        bd.session.add(config)
        bd.session.commit()
    
    # Solo mostrar info académica si el usuario es estudiante
    es_estudiante = current_user.rol == 'estudiante'
    estudiante = Estudiante.query.get(current_user.id) if es_estudiante else None
    
    if request.method == 'POST':
        # Guardar preferencias generales
        config.tema = request.form.get('tema', 'claro')
        config.ocultar_ranking = request.form.get('ocultar_ranking') == 'on'
        config.tamano_fuente = request.form.get('tamano_fuente', 'normal')
        config.notif_nuevos_cursos = request.form.get('notif_nuevos_cursos') == 'on'
        config.notif_racha = request.form.get('notif_racha') == 'on'
        
        # Guardar info académica (solo estudiantes)
        if es_estudiante and estudiante:
            carrera = request.form.get('carrera')
            semestre = request.form.get('semestre', type=int)
            grupo = request.form.get('grupo')
            if carrera:
                estudiante.carrera = carrera
            if semestre is not None:
                estudiante.semestre = semestre
                from datetime import datetime
                estudiante.fecha_actualizacion_semestre = datetime.utcnow()
            if grupo:
                estudiante.grupo = grupo
        
        bd.session.commit()
        flash('Configuración guardada correctamente.', 'success')
        return redirect(url_for('main.configuracion'))
    
    return render_template('main/configuracion.html',
                           config=config,
                           estudiante=estudiante,
                           es_estudiante=es_estudiante)


@main.route('/tienda')
@login_required
def tienda():
    from ..modelos import ArticuloTienda, Estudiante, InventarioEstudiante
    
    estudiante = Estudiante.query.get(current_user.id)
    if not estudiante:
        flash('Solo los estudiantes pueden acceder a la tienda.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    articulos = ArticuloTienda.query.filter_by(activo=True).order_by(ArticuloTienda.precio).all()
    # IDs de artículos que ya posee
    mis_articulos = InventarioEstudiante.query.filter_by(id_estudiante=current_user.id).all()
    ids_comprados = [inv.id_articulo for inv in mis_articulos]
    
    return render_template('main/tienda.html',
                           estudiante=estudiante,
                           articulos=articulos,
                           ids_comprados=ids_comprados)


@main.route('/tienda/comprar/<int:id_articulo>', methods=['POST'])
@login_required
def comprar_articulo(id_articulo):
    from ..modelos import ArticuloTienda, Estudiante, InventarioEstudiante
    
    estudiante = Estudiante.query.get(current_user.id)
    if not estudiante:
        flash('Solo los estudiantes pueden comprar.', 'warning')
        return redirect(url_for('main.tienda'))
    
    articulo = ArticuloTienda.query.get_or_404(id_articulo)
    
    # Verificar si ya lo tiene
    ya_comprado = InventarioEstudiante.query.filter_by(
        id_estudiante=current_user.id, id_articulo=id_articulo
    ).first()
    if ya_comprado:
        flash('Ya tienes este artículo.', 'info')
        return redirect(url_for('main.tienda'))
    
    # Verificar monedas
    if estudiante.monedas < articulo.precio:
        flash(f'No tienes suficientes Matacoins. Necesitas {articulo.precio} y tienes {estudiante.monedas}.', 'warning')
        return redirect(url_for('main.tienda'))
    
    # Realizar compra
    estudiante.monedas -= articulo.precio
    bd.session.add(InventarioEstudiante(id_estudiante=current_user.id, id_articulo=id_articulo))
    bd.session.commit()
    flash(f'¡Has comprado "{articulo.nombre}"! 🎉', 'success')
    return redirect(url_for('main.tienda'))


@main.route('/tienda/equipar/<int:id_articulo>', methods=['POST'])
@login_required
def equipar_articulo(id_articulo):
    from ..modelos import ArticuloTienda, Estudiante, InventarioEstudiante
    
    estudiante = Estudiante.query.get(current_user.id)
    if not estudiante:
        return redirect(url_for('main.tienda'))
    
    # Verificar que lo tiene en inventario
    inv = InventarioEstudiante.query.filter_by(
        id_estudiante=current_user.id, id_articulo=id_articulo
    ).first()
    if not inv:
        flash('No tienes este artículo.', 'warning')
        return redirect(url_for('main.tienda'))
    
    articulo = ArticuloTienda.query.get(id_articulo)
    if articulo.tipo == 'avatar':
        # Toggle: desequipar si ya está activo
        if estudiante.avatar_activo == articulo.icono:
            estudiante.avatar_activo = None
            flash(f'Avatar "{articulo.nombre}" desequipado.', 'info')
        else:
            estudiante.avatar_activo = articulo.icono
            flash(f'Avatar "{articulo.nombre}" equipado. 🎭', 'success')
    elif articulo.tipo == 'marco':
        if estudiante.marco_activo == articulo.css_clase:
            estudiante.marco_activo = None
            flash(f'Marco "{articulo.nombre}" desequipado.', 'info')
        else:
            estudiante.marco_activo = articulo.css_clase
            flash(f'Marco "{articulo.nombre}" equipado. ✨', 'success')
    
    bd.session.commit()
    return redirect(url_for('main.tienda'))
