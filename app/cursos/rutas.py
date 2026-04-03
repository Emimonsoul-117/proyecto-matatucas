import json
import secrets
import string
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from . import cursos
from .. import bd
from ..modelos import (
    Curso,
    Leccion,
    Video,
    Inscripcion,
    Ejercicio,
    LeccionCompletada,
    Usuario,
    asegurar_fila_docente_si_falta,
    progreso_por_lecciones_completadas,
    IntentoEjercicio,
)
from ..decoradores import docente_required
from ..servicios.auditoria_servicio import registrar_accion


def _generar_codigo_curso_unico():
    """Código corto legible para compartir (ej. MTC-A1B2C3D4)."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        sufijo = ''.join(secrets.choice(alphabet) for _ in range(8))
        codigo = f'MTC-{sufijo}'
        if not Curso.query.filter_by(codigo_curso=codigo).first():
            return codigo


def _asegurar_codigo_curso(curso):
    if not curso.codigo_curso:
        curso.codigo_curso = _generar_codigo_curso_unico()


# ─────────────────────────────────────
# Función interna: marcar lección completada
# ─────────────────────────────────────
def _marcar_como_completada(id_estudiante, id_leccion, id_curso):
    """Marca una lección como completada y recalcula el progreso.
    Devuelve dict con puntos ganados y nuevas insignias (puede ser None si ya estaba hecha).
    """
    ya_completada = LeccionCompletada.query.filter_by(
        id_estudiante=id_estudiante,
        id_leccion=id_leccion
    ).first()

    if ya_completada:
        return None  # Sin cambios

    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=id_estudiante,
        id_curso=id_curso
    ).first()

    total_lecciones = Leccion.query.filter_by(id_curso=id_curso).count()
    # Contar completadas ANTES de insertar; si se hace después, el autoflush de SQLAlchemy
    # incluye la fila nueva y el +1 duplicaba el avance (porcentajes mayores a 100 %).
    lecciones_hechas_antes = LeccionCompletada.query.join(Leccion).filter(
        LeccionCompletada.id_estudiante == id_estudiante,
        Leccion.id_curso == id_curso
    ).count()
    lecciones_hechas = lecciones_hechas_antes + 1

    nueva_completada = LeccionCompletada(
        id_estudiante=id_estudiante,
        id_leccion=id_leccion
    )
    bd.session.add(nueva_completada)

    if inscripcion:
        if total_lecciones <= 0:
            inscripcion.progreso = 0.0
        else:
            inscripcion.progreso = min(
                100.0,
                round((lecciones_hechas / total_lecciones) * 100, 1)
            )

    bd.session.commit()

    # Otorgar puntos
    from ..servicios.gamificacion_servicio import ServicioGamificacion
    servicio_g = ServicioGamificacion()
    puntos = 50
    if inscripcion and inscripcion.progreso >= 100:
        puntos += 100  # Bono por completar el curso
    resultado = servicio_g.otorgar_puntos(id_estudiante, puntos)

    nuevas_insignias = resultado.get('nuevas_insignias', []) if resultado else []
    return {
        'puntos': puntos,
        'progreso': inscripcion.progreso if inscripcion else 0,
        'nuevas_insignias': [i.nombre for i in nuevas_insignias]
    }


# ─────────────────────────────────────
# Lista de cursos
# ─────────────────────────────────────
@cursos.route('/')
@login_required
def lista_cursos():
    q = (request.args.get('q') or '').strip()
    query = Curso.query.order_by(Curso.fecha_creacion.desc())
    if q:
        like = f'%{q}%'
        query = query.filter(
            or_(
                Curso.titulo.ilike(like),
                Curso.descripcion.ilike(like),
                Curso.codigo_curso.ilike(like),
            )
        )
    
    # Si es estudiante, solo mostrar cursos PUBLICADOS
    if current_user.is_authenticated and current_user.rol == 'estudiante':
        query = query.filter_by(estado='publicado')
        
    lista_cursos = query.all()
    necesita_commit = False
    for c in lista_cursos:
        if not c.codigo_curso:
            _asegurar_codigo_curso(c)
            necesita_commit = True
    if necesita_commit:
        bd.session.commit()
    mis_inscripciones = set()
    if current_user.rol == 'estudiante':
        inscripciones = Inscripcion.query.filter_by(id_estudiante=current_user.id).all()
        mis_inscripciones = {i.id_curso for i in inscripciones}
    return render_template(
        'cursos/lista.html',
        cursos=lista_cursos,
        mis_inscripciones=mis_inscripciones,
        busqueda=q,
    )


# ─────────────────────────────────────
# Crear curso
# ─────────────────────────────────────
@cursos.route('/crear', methods=['GET', 'POST'])
@login_required
@docente_required
def crear_curso():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        nivel = request.form.get('nivel')

        asegurar_fila_docente_si_falta(current_user)

        nuevo_curso = Curso(
            titulo=titulo,
            descripcion=descripcion,
            nivel=nivel,
            id_docente=current_user.id,
            codigo_curso=_generar_codigo_curso_unico(),
            estado='borrador' # Se inicia en borrador por defecto
        )
        bd.session.add(nuevo_curso)
        bd.session.commit()
        
        registrar_accion('CREAR_CURSO', {'id_curso': nuevo_curso.id, 'titulo': nuevo_curso.titulo})
        
        flash('Curso creado exitosamente. Recuerda enviarlo a revisión cuando esté listo.', 'exito')
        return redirect(url_for('cursos.lista_cursos'))

    return render_template('cursos/crear.html')


# ─────────────────────────────────────
# Ver / Editar curso
# ─────────────────────────────────────
@cursos.route('/<int:id>')
@login_required
def ver_curso(id):
    curso = Curso.query.get_or_404(id)
    if not curso.codigo_curso:
        _asegurar_codigo_curso(curso)
        bd.session.commit()
    # Obtener lecciones completadas por el estudiante (para mostrar badges)
    lecciones_completadas_ids = set()
    inscripcion = None
    if current_user.rol == 'estudiante':
        completadas = LeccionCompletada.query.join(Leccion).filter(
            LeccionCompletada.id_estudiante == current_user.id,
            Leccion.id_curso == id
        ).all()
        lecciones_completadas_ids = {c.id_leccion for c in completadas}
        inscripcion = Inscripcion.query.filter_by(
            id_estudiante=current_user.id,
            id_curso=id
        ).first()
        if inscripcion:
            real = progreso_por_lecciones_completadas(current_user.id, id)
            if abs(inscripcion.progreso - real) > 0.02:
                inscripcion.progreso = real
                bd.session.commit()
    return render_template(
        'cursos/ver.html',
        curso=curso,
        lecciones_completadas_ids=lecciones_completadas_ids,
        inscripcion=inscripcion,
    )


@cursos.route('/<int:id_curso>/alumnos', methods=['GET'])
@login_required
@docente_required
def ver_alumnos_curso(id_curso):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para ver los alumnos de este curso.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    q = (request.args.get('q') or '').strip()
    total_lecciones = Leccion.query.filter_by(id_curso=id_curso).count()

    inscripciones = Inscripcion.query.filter_by(id_curso=id_curso).all()
    estudiantes = []
    for ins in inscripciones:
        usuario = Usuario.query.get(ins.id_estudiante)
        if not usuario:
            continue

        if q:
            hay = (
                (usuario.nombre and q.lower() in usuario.nombre.lower())
                or (usuario.email and q.lower() in usuario.email.lower())
                or (usuario.numero_control and q.lower() in usuario.numero_control.lower())
            )
            if not hay:
                continue

        progreso = progreso_por_lecciones_completadas(usuario.id, id_curso)

        completadas_count = LeccionCompletada.query.join(Leccion).filter(
            LeccionCompletada.id_estudiante == usuario.id,
            Leccion.id_curso == id_curso,
        ).count()

        intento_q = (
            IntentoEjercicio.query
            .join(Ejercicio, IntentoEjercicio.id_ejercicio == Ejercicio.id)
            .join(Leccion, Ejercicio.id_leccion == Leccion.id)
            .filter(
                IntentoEjercicio.id_estudiante == usuario.id,
                Leccion.id_curso == id_curso,
            )
        )

        intentos_totales = intento_q.count()
        correctas_totales = intento_q.filter(IntentoEjercicio.es_correcta.is_(True)).count()
        avg_puntaje = intento_q.with_entities(func.avg(IntentoEjercicio.puntaje)).scalar() or 0.0

        estudiantes.append(
            {
                'usuario': usuario,
                'progreso': progreso,
                'completadas': completadas_count,
                'total_lecciones': total_lecciones,
                'intentos_totales': intentos_totales,
                'correctas_totales': correctas_totales,
                'avg_puntaje': float(avg_puntaje),
            }
        )

    estudiantes.sort(key=lambda x: x['progreso'], reverse=True)

    return render_template(
        'cursos/curso_alumnos.html',
        curso=curso,
        estudiantes=estudiantes,
        q=q,
    )


@cursos.route('/<int:id_curso>/alumnos/<int:id_estudiante>', methods=['GET'])
@login_required
@docente_required
def ver_alumno_curso(id_curso, id_estudiante):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para ver este alumno.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    usuario = Usuario.query.get_or_404(id_estudiante)
    total_lecciones = Leccion.query.filter_by(id_curso=id_curso).count()
    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=id_estudiante,
        id_curso=id_curso,
    ).first()
    progreso = progreso_por_lecciones_completadas(id_estudiante, id_curso)

    completadas_rows = (
        bd.session.query(LeccionCompletada, Leccion)
        .join(Leccion, LeccionCompletada.id_leccion == Leccion.id)
        .filter(
            LeccionCompletada.id_estudiante == id_estudiante,
            Leccion.id_curso == id_curso,
        )
        .order_by(Leccion.orden.asc())
        .all()
    )
    completadas = [
        {
            'leccion_id': lc.id_leccion,
            'orden': l.orden,
            'titulo': l.titulo,
            'fecha_completada': lc.fecha_completada,
        }
        for lc, l in completadas_rows
    ]

    # Últimos intentos (para no saturar la página)
    intentos_rows = (
        bd.session.query(IntentoEjercicio, Ejercicio, Leccion)
        .join(Ejercicio, IntentoEjercicio.id_ejercicio == Ejercicio.id)
        .join(Leccion, Ejercicio.id_leccion == Leccion.id)
        .filter(
            IntentoEjercicio.id_estudiante == id_estudiante,
            Leccion.id_curso == id_curso,
        )
        .order_by(IntentoEjercicio.fecha_intento.desc())
        .limit(200)
        .all()
    )

    return render_template(
        'cursos/curso_alumno.html',
        curso=curso,
        usuario=usuario,
        inscripcion=inscripcion,
        progreso=progreso,
        completadas=completadas,
        total_lecciones=total_lecciones,
        intentos_rows=intentos_rows,
    )


@cursos.route('/<int:id_curso>/alumnos/<int:id_estudiante>/bloquear', methods=['POST'])
@login_required
@docente_required
def bloquear_alumno_curso(id_curso, id_estudiante):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para esta acción.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    ins = Inscripcion.query.filter_by(id_curso=id_curso, id_estudiante=id_estudiante).first_or_404()
    ins.bloqueado = True
    bd.session.commit()
    flash('Alumno bloqueado en el curso.', 'exito')
    return redirect(url_for('cursos.ver_alumno_curso', id_curso=id_curso, id_estudiante=id_estudiante))


@cursos.route('/<int:id_curso>/alumnos/<int:id_estudiante>/desbloquear', methods=['POST'])
@login_required
@docente_required
def desbloquear_alumno_curso(id_curso, id_estudiante):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para esta acción.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    ins = Inscripcion.query.filter_by(id_curso=id_curso, id_estudiante=id_estudiante).first_or_404()
    ins.bloqueado = False
    bd.session.commit()
    flash('Alumno desbloqueado en el curso.', 'exito')
    return redirect(url_for('cursos.ver_alumno_curso', id_curso=id_curso, id_estudiante=id_estudiante))


@cursos.route('/<int:id_curso>/alumnos/<int:id_estudiante>/retirar', methods=['POST'])
@login_required
@docente_required
def retirar_alumno_curso(id_curso, id_estudiante):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para esta acción.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    ins = Inscripcion.query.filter_by(id_curso=id_curso, id_estudiante=id_estudiante).first_or_404()

    # Eliminar completadas e intentos de este curso del estudiante (para que al re-inscribir
    # no se arrastre progreso/calificaciones previas).
    bd.session.query(LeccionCompletada).join(
        Leccion, LeccionCompletada.id_leccion == Leccion.id
    ).filter(
        LeccionCompletada.id_estudiante == id_estudiante,
        Leccion.id_curso == id_curso,
    ).delete(synchronize_session=False)

    bd.session.query(IntentoEjercicio).join(
        Ejercicio, IntentoEjercicio.id_ejercicio == Ejercicio.id
    ).join(
        Leccion, Ejercicio.id_leccion == Leccion.id
    ).filter(
        IntentoEjercicio.id_estudiante == id_estudiante,
        Leccion.id_curso == id_curso,
    ).delete(synchronize_session=False)

    bd.session.delete(ins)
    bd.session.commit()
    flash('Inscripción retirada (progreso e intentos eliminados).', 'exito')
    return redirect(url_for('cursos.ver_alumnos_curso', id_curso=id_curso))


@cursos.route('/<int:id_curso>/analytics', methods=['GET'])
@login_required
@docente_required
def curso_analytics(id_curso):
    curso = Curso.query.get_or_404(id_curso)
    if current_user.rol != 'administrador' and curso.id_docente != current_user.id:
        flash('No tienes permiso para ver analíticas de este curso.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    total_lecciones = Leccion.query.filter_by(id_curso=id_curso).count()
    inscripciones = Inscripcion.query.filter_by(id_curso=id_curso).all()

    estudiantes = []
    for ins in inscripciones:
        usuario = Usuario.query.get(ins.id_estudiante)
        if not usuario:
            continue

        progreso = progreso_por_lecciones_completadas(usuario.id, id_curso)

        intento_q = (
            IntentoEjercicio.query
            .join(Ejercicio, IntentoEjercicio.id_ejercicio == Ejercicio.id)
            .join(Leccion, Ejercicio.id_leccion == Leccion.id)
            .filter(
                IntentoEjercicio.id_estudiante == usuario.id,
                Leccion.id_curso == id_curso,
            )
        )

        total_intentos = intento_q.count()
        avg_puntaje = intento_q.with_entities(func.avg(IntentoEjercicio.puntaje)).scalar() or 0.0
        correctas = intento_q.filter(IntentoEjercicio.es_correcta.is_(True)).count()

        estudiantes.append(
            {
                'usuario': usuario,
                'progreso': progreso,
                'avg_puntaje': float(avg_puntaje),
                'total_intentos': total_intentos,
                'correctas': correctas,
            }
        )

    estudiantes.sort(key=lambda x: x['progreso'], reverse=True)
    total_estudiantes = len(estudiantes)

    completados = [e for e in estudiantes if total_lecciones > 0 and e['progreso'] >= 100]
    tasa_completitud = (len(completados) / total_estudiantes * 100) if total_estudiantes > 0 else 0.0

    # Puntaje global basado en intentos
    intentos_global_q = (
        IntentoEjercicio.query
        .join(Ejercicio, IntentoEjercicio.id_ejercicio == Ejercicio.id)
        .join(Leccion, Ejercicio.id_leccion == Leccion.id)
        .filter(Leccion.id_curso == id_curso)
    )
    total_intentos_global = intentos_global_q.count()
    avg_puntaje_global = intentos_global_q.with_entities(func.avg(IntentoEjercicio.puntaje)).scalar() or 0.0
    correctas_global = intentos_global_q.filter(IntentoEjercicio.es_correcta.is_(True)).count()
    tasa_correcta = (correctas_global / total_intentos_global * 100) if total_intentos_global > 0 else 0.0

    top = estudiantes[:5]

    return render_template(
        'cursos/curso_analytics.html',
        curso=curso,
        total_lecciones=total_lecciones,
        total_estudiantes=total_estudiantes,
        tasa_completitud=tasa_completitud,
        tasa_correcta=tasa_correcta,
        avg_puntaje_global=float(avg_puntaje_global),
        estudiantes=estudiantes,
        top=top,
    )


@cursos.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@docente_required
def editar_curso(id):
    curso = Curso.query.get_or_404(id)
    if curso.id_docente != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permiso para editar este curso.', 'peligro')
        return redirect(url_for('cursos.lista_cursos'))

    if request.method == 'POST':
        curso.titulo = request.form.get('titulo')
        curso.descripcion = request.form.get('descripcion')
        curso.nivel = request.form.get('nivel')
        bd.session.commit()
        flash('Curso actualizado correctamente.', 'exito')
        return redirect(url_for('cursos.ver_curso', id=curso.id))

    return render_template('cursos/editar.html', curso=curso)


# ─────────────────────────────────────
# Nueva lección (Secciones)
# ─────────────────────────────────────
@cursos.route('/<int:id_curso>/leccion/nueva', methods=['GET', 'POST'])
@login_required
@docente_required
def nueva_leccion(id_curso):
    curso = Curso.query.get_or_404(id_curso)
    if curso.id_docente != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permiso para agregar lecciones a este curso.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        orden = request.form.get('orden')
        secciones_json = request.form.get('secciones_json', '[]')

        try:
            secciones = json.loads(secciones_json)
        except (json.JSONDecodeError, TypeError):
            secciones = []

        # Asignar orden a cada sección
        for i, sec in enumerate(secciones):
            sec['orden'] = i + 1

        leccion = Leccion(
            titulo=titulo,
            orden=int(orden) if orden else (len(curso.lecciones) + 1),
            id_curso=id_curso,
            secciones=secciones if secciones else None,
            # Legacy: si solo hay 1 sección de teoría, también se guarda en contenido_teoria
            contenido_teoria=next(
                (s.get('contenido', '') for s in secciones if s.get('tipo') == 'teoria'),
                None
            )
        )
        bd.session.add(leccion)
        bd.session.commit()

        # Persistir ejercicios legacy para que el endpoint de evaluación
        # (`/leccion/<id>/ejercicios`) funcione también con el editor por secciones JSON.
        for sec in secciones or []:
            if sec.get('tipo') != 'ejercicio':
                continue
            tipo_q = sec.get('tipo_q') or 'opcion_multiple'
            bd.session.add(
                Ejercicio(
                    id_leccion=leccion.id,
                    enunciado=sec.get('pregunta') or '',
                    tipo=tipo_q,
                    opciones=sec.get('opciones') or {},
                    respuesta_correcta=sec.get('respuesta') or '',
                    dificultad=sec.get('dificultad') or 1,
                )
            )
        # Guardar también los ejercicios persistidos (si hubo).
        bd.session.commit()

        flash('Lección agregada exitosamente.', 'exito')
        return redirect(url_for('cursos.ver_curso', id=id_curso))

    return render_template('cursos/nueva_leccion.html', curso=curso)


# ─────────────────────────────────────
# Inscribirse a un curso
# ─────────────────────────────────────
def _ejecutar_inscripcion_estudiante(id_estudiante, id_curso):
    """Devuelve ('ok'|'ya'|'no_estudiante', id_curso). Hace commit si inscribe."""
    usuario = Usuario.query.get(id_estudiante)
    if not usuario or usuario.rol != 'estudiante':
        return 'no_estudiante', id_curso

    if Inscripcion.query.filter_by(id_estudiante=id_estudiante, id_curso=id_curso).first():
        return 'ya', id_curso

    bd.session.add(Inscripcion(id_estudiante=id_estudiante, id_curso=id_curso))
    bd.session.commit()
    return 'ok', id_curso


@cursos.route('/<int:id>/inscribir', methods=['POST'])
@login_required
def inscribir_curso(id):
    if current_user.rol != 'estudiante':
        flash('Solo los estudiantes pueden inscribirse a cursos.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id))

    estado, _ = _ejecutar_inscripcion_estudiante(current_user.id, id)
    if estado == 'ya':
        flash('Ya estás inscrito en este curso.', 'info')
    elif estado == 'ok':
        flash('¡Inscripción exitosa! Bienvenido al curso.', 'exito')
    return redirect(url_for('cursos.ver_curso', id=id))


# ─────────────────────────────────────
# Unirse a un curso por código único
# ─────────────────────────────────────
@cursos.route('/unirse', methods=['POST'])
@login_required
def unirse_por_codigo():
    if current_user.rol != 'estudiante':
        flash('Solo los estudiantes pueden unirse a cursos con código.', 'peligro')
        return redirect(url_for('cursos.lista_cursos'))

    codigo_raw = (request.form.get('codigo') or '').strip().upper()
    codigo_norm = codigo_raw.replace(' ', '')
    if not codigo_norm:
        flash('Introduce el código del curso.', 'advertencia')
        return redirect(url_for('cursos.lista_cursos'))

    curso = Curso.query.filter(
        or_(
            Curso.codigo_curso == codigo_norm,
            Curso.codigo_curso.ilike(codigo_norm),
        )
    ).first()

    if not curso:
        flash('No existe ningún curso con ese código. Revisa e inténtalo de nuevo.', 'peligro')
        return redirect(url_for('cursos.lista_cursos'))

    estado, cid = _ejecutar_inscripcion_estudiante(current_user.id, curso.id)
    if estado == 'ya':
        flash('Ya estás inscrito en este curso.', 'info')
    elif estado == 'ok':
        flash(f'¡Te uniste al curso con código {curso.codigo_curso}!', 'exito')
    return redirect(url_for('cursos.ver_curso', id=cid))


# ─────────────────────────────────────
# Ver lección (con auto-completado)
# ─────────────────────────────────────
@cursos.route('/leccion/<int:id>')
@login_required
def ver_leccion(id):
    leccion = Leccion.query.get_or_404(id)
    completada = False

    if current_user.rol == 'estudiante':
        inscripcion = Inscripcion.query.filter_by(
            id_estudiante=current_user.id,
            id_curso=leccion.id_curso
        ).first()
        if not inscripcion:
            flash('Debes inscribirte al curso para ver esta lección.', 'peligro')
            return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))
        if getattr(inscripcion, 'bloqueado', False):
            flash('Tu acceso a este curso fue bloqueado por el docente.', 'peligro')
            return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))

        # Verificar si ya está completada
        completada = LeccionCompletada.query.filter_by(
            id_estudiante=current_user.id,
            id_leccion=id
        ).first() is not None

        # Bloqueo por secuencia:
        # Si el estudiante NO completó la lección actual y existen lecciones anteriores,
        # entonces debe haber completado todas las anteriores por `orden`.
        if not completada:
            prev_count = Leccion.query.filter(
                Leccion.id_curso == leccion.id_curso,
                Leccion.orden < leccion.orden,
            ).count()
            if prev_count > 0:
                prev_done = LeccionCompletada.query.join(Leccion).filter(
                    LeccionCompletada.id_estudiante == current_user.id,
                    Leccion.id_curso == leccion.id_curso,
                    Leccion.orden < leccion.orden,
                ).count()

                if prev_done < prev_count:
                    flash('Primero completa las lecciones anteriores para avanzar en el curso.', 'advertencia')

                    # Redirigir a la primera lección incompleta
                    completadas_ids = (
                        LeccionCompletada.query.join(Leccion)
                        .filter(
                            LeccionCompletada.id_estudiante == current_user.id,
                            Leccion.id_curso == leccion.id_curso,
                        )
                        .with_entities(LeccionCompletada.id_leccion)
                        .all()
                    )
                    completadas_ids_set = {x[0] for x in completadas_ids}
                    lecciones_orden = Leccion.query.filter_by(id_curso=leccion.id_curso).order_by(Leccion.orden.asc()).all()
                    for l in lecciones_orden:
                        if l.id not in completadas_ids_set:
                            return redirect(url_for('cursos.ver_leccion', id=l.id))

                    return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))

        # Determinar si hay secciones de video/ejercicios (incluye legacy).
        secciones_base = leccion.secciones or []
        tiene_video = any(s.get('tipo') == 'video' for s in secciones_base) or bool(leccion.videos)
        tiene_ejercicio = any(s.get('tipo') == 'ejercicio' for s in secciones_base) or bool(leccion.ejercicios)

        # Auto-completar solo si NO hay video y NO hay ejercicios.
        # - Video se completa desde el frontend (YouTube) vía `api_auto_completar`.
        # - Ejercicios se completan pasando `hacer_ejercicios` (persistiendo intentos).
        if not completada and not tiene_video and not tiene_ejercicio:
            resultado = _marcar_como_completada(current_user.id, id, leccion.id_curso)
            if resultado:
                completada = True
                flash(f'✅ Lección completada automáticamente. +{resultado["puntos"]} XP', 'exito')
                for insignia in resultado['nuevas_insignias']:
                    flash(f'🏆 ¡Nueva insignia: {insignia}!', 'info')

    # Compatibilidad legacy: si no hay secciones pero sí contenido_teoria o videos
    secciones = leccion.secciones
    if not secciones:
        secciones = []
        if leccion.contenido_teoria:
            secciones.append({'tipo': 'teoria', 'contenido': leccion.contenido_teoria, 'orden': 1})
        for v in leccion.videos:
            secciones.append({
                'tipo': 'video',
                'url': v.url_youtube,
                'titulo': v.titulo or 'Video de la Lección',
                'orden': len(secciones) + 1
            })
        for e in leccion.ejercicios:
            secciones.append({
                'tipo': 'ejercicio',
                'pregunta': e.enunciado,
                'tipo_q': e.tipo,
                'opciones': e.opciones or {},
                'respuesta': e.respuesta_correcta,
                'dificultad': e.dificultad,
                'id_ejercicio': e.id,
                'orden': len(secciones) + 1
            })

    return render_template('cursos/ver_leccion.html',
                           leccion=leccion,
                           secciones=secciones,
                           completada=completada)


# ─────────────────────────────────────
# API: Auto-completar lección tras video
# ─────────────────────────────────────
@cursos.route('/leccion/<int:id>/auto-completar', methods=['POST'])
@login_required
def api_auto_completar(id):
    """Llamado desde JS cuando el video de YouTube termina."""
    if current_user.rol != 'estudiante':
        return jsonify({'error': 'Solo estudiantes'}), 403

    leccion = Leccion.query.get_or_404(id)

    # Si la lección tiene ejercicios, no se completa solo por terminar el video.
    # El estudiante debe resolverlos en el endpoint de evaluación.
    if current_user.rol == 'estudiante' and leccion.ejercicios:
        return jsonify({
            'status': 'requiere_ejercicios',
            'message': 'Esta lección requiere resolver los ejercicios para completarse.',
        })
    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.id,
        id_curso=leccion.id_curso
    ).first()
    if not inscripcion:
        return jsonify({'error': 'No inscrito'}), 403
    if getattr(inscripcion, 'bloqueado', False):
        return jsonify({'error': 'Acceso bloqueado'}), 403

    resultado = _marcar_como_completada(current_user.id, id, leccion.id_curso)

    if resultado is None:
        return jsonify({'status': 'ya_completada', 'message': 'Ya completada'})

    return jsonify({
        'status': 'completada',
        'puntos': resultado['puntos'],
        'progreso': resultado['progreso'],
        'nuevas_insignias': resultado['nuevas_insignias']
    })


# ─────────────────────────────────────
# Completar lección manual (legacy, sigue funcionando)
# ─────────────────────────────────────
@cursos.route('/leccion/<int:id>/completar', methods=['POST'])
@login_required
def completar_leccion(id):
    if current_user.rol != 'estudiante':
        return jsonify({'error': 'Solo estudiantes pueden marcar lecciones.'}), 403

    leccion = Leccion.query.get_or_404(id)
    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.id,
        id_curso=leccion.id_curso
    ).first_or_404()

    if getattr(inscripcion, 'bloqueado', False):
        flash('Tu acceso fue bloqueado por el docente.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))

    resultado = _marcar_como_completada(current_user.id, id, leccion.id_curso)

    if resultado:
        flash(f'¡Lección completada! +{resultado["puntos"]} XP ganados.', 'exito')
        if resultado['progreso'] >= 100:
            flash('🎉 ¡Felicidades! Completaste el curso al 100%.', 'exito')
        for nombre in resultado['nuevas_insignias']:
            flash(f'🏆 ¡Nueva insignia: {nombre}!', 'info')
    else:
        flash('Ya habías completado esta lección.', 'info')

    return redirect(url_for('cursos.ver_leccion', id=id))


# ─────────────────────────────────────
# Ejercicios (páginas externas - legacy)
# ─────────────────────────────────────
@cursos.route('/leccion/<int:id_leccion>/ejercicios', methods=['GET', 'POST'])
@login_required
def hacer_ejercicios(id_leccion):
    leccion = Leccion.query.get_or_404(id_leccion)
    ejercicios = leccion.ejercicios

    if current_user.rol == 'estudiante':
        inscripcion = Inscripcion.query.filter_by(
            id_estudiante=current_user.id,
            id_curso=leccion.id_curso,
        ).first()
        if not inscripcion:
            flash('Debes inscribirte al curso para resolver estos ejercicios.', 'peligro')
            return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))
        if getattr(inscripcion, 'bloqueado', False):
            flash('Tu acceso a este curso fue bloqueado por el docente.', 'peligro')
            return redirect(url_for('cursos.ver_curso', id=leccion.id_curso))

    if not ejercicios:
        flash('Esta lección aún no tiene ejercicios.', 'info')
        return redirect(url_for('cursos.ver_leccion', id=id_leccion))

    puntaje = None
    resultados = None

    if request.method == 'POST':
        # Guardar intentos con el mismo número de intento para todos los ejercicios de esta lección.
        intento_num = (
            IntentoEjercicio.query.join(Ejercicio)
            .filter(
                IntentoEjercicio.id_estudiante == current_user.id,
                Ejercicio.id_leccion == id_leccion,
            )
            .with_entities(func.max(IntentoEjercicio.intento_num))
            .scalar()
        ) or 0
        intento_num += 1

        correctas = 0
        resultados = {}
        # Persistir intentos por cada ejercicio (se hace en batch al final)
        nuevos_intentos = []

        for ejercicio in ejercicios:
            respuesta_usuario = request.form.get(f'respuesta_{ejercicio.id}')
            es_correcta = False

            if (
                respuesta_usuario
                and respuesta_usuario.strip().lower()
                == (ejercicio.respuesta_correcta or '').strip().lower()
            ):
                correctas += 1
                es_correcta = True

            puntaje_ejercicio = 100.0 if es_correcta else 0.0

            nuevos_intentos.append(
                IntentoEjercicio(
                    id_estudiante=current_user.id,
                    id_ejercicio=ejercicio.id,
                    intento_num=intento_num,
                    respuesta_usuario=respuesta_usuario,
                    es_correcta=es_correcta,
                    puntaje=puntaje_ejercicio,
                )
            )

            resultados[ejercicio.id] = {
                'respuesta': respuesta_usuario,
                'correcta': es_correcta,
                'solucion': ejercicio.respuesta_correcta,
            }

        bd.session.add_all(nuevos_intentos)
        bd.session.commit()

        puntaje = int((correctas / len(ejercicios)) * 100)

        if puntaje >= 70:
            resultado = _marcar_como_completada(current_user.id, id_leccion, leccion.id_curso)
            if resultado:
                flash(f'¡Lección completada! +{resultado["puntos"]} XP ganados.', 'exito')
                if resultado['nuevas_insignias']:
                    for nombre in resultado['nuevas_insignias']:
                        flash(f'🏆 ¡Nueva insignia: {nombre}!', 'info')
            else:
                flash('Lección ya completada antes. Tus respuestas se guardaron.', 'info')
        else:
            flash(f'Obtuviste {puntaje}/100. Inténtalo de nuevo.', 'advertencia')

    return render_template('cursos/hacer_ejercicios.html', leccion=leccion, ejercicios=ejercicios, resultados=resultados, puntaje=puntaje)


# ─────────────────────────────────────
# Nuevo ejercicio (legacy)
# ─────────────────────────────────────
@cursos.route('/leccion/<int:id_leccion>/ejercicio/nuevo', methods=['GET', 'POST'])
@login_required
@docente_required
def nuevo_ejercicio(id_leccion):
    leccion = Leccion.query.get_or_404(id_leccion)
    if leccion.curso.id_docente != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permiso para agregar ejercicios a esta lección.', 'peligro')
        return redirect(url_for('cursos.ver_leccion', id=id_leccion))

    if request.method == 'POST':
        enunciado = request.form.get('enunciado')
        tipo = request.form.get('tipo')
        respuesta_correcta = request.form.get('respuesta_correcta')
        dificultad = request.form.get('dificultad')

        opciones = None
        if tipo == 'opcion_multiple':
            opciones = {
                'a': request.form.get('opcion_a'),
                'b': request.form.get('opcion_b'),
                'c': request.form.get('opcion_c'),
                'd': request.form.get('opcion_d')
            }

        nuevo_ejercicio = Ejercicio(
            id_leccion=id_leccion,
            enunciado=enunciado,
            tipo=tipo,
            opciones=opciones,
            respuesta_correcta=respuesta_correcta,
            dificultad=dificultad
        )
        bd.session.add(nuevo_ejercicio)
        bd.session.commit()
        flash('Ejercicio agregado correctamente.', 'exito')
        return redirect(url_for('cursos.ver_leccion', id=id_leccion))

    return render_template('cursos/nuevo_ejercicio.html', leccion=leccion)


# ─────────────────────────────────────
# APIs de IA
# ─────────────────────────────────────
@cursos.route('/api/generar-ejercicio', methods=['POST'])
@login_required
@docente_required
def api_generar_ejercicio():
    data = request.json
    tema = data.get('tema')
    nivel = data.get('nivel')
    tipo = data.get('tipo', 'opcion_multiple')

    if not tema or not nivel:
        return {'error': 'Faltan parámetros'}, 400

    from ..servicios.ia_servicio import ServicioIA
    servicio = ServicioIA()
    ejercicio_generado = servicio.generar_ejercicio(tema, nivel, tipo)

    if isinstance(ejercicio_generado, dict):
        if 'error' in ejercicio_generado:
            return {'error': ejercicio_generado['error']}, 500
        ejercicio_generado.setdefault('pasos', [])
        return ejercicio_generado
    else:
        return {'error': 'No se pudo generar el ejercicio'}, 500


@cursos.route('/api/explicar-ejercicio', methods=['POST'])
@login_required
def api_explicar_ejercicio():
    """Genera una explicación paso a paso usando IA cuando el estudiante falla."""
    data = request.json
    enunciado = data.get('enunciado', '')
    respuesta_correcta = data.get('respuesta_correcta', '')
    respuesta_usuario = data.get('respuesta_usuario', '')

    if not enunciado or not respuesta_correcta:
        return {'error': 'Faltan parámetros'}, 400

    from ..servicios.ia_servicio import ServicioIA
    servicio = ServicioIA()
    explicacion = servicio.generar_explicacion_ejercicio(
        enunciado, respuesta_correcta, respuesta_usuario
    )
    return jsonify(explicacion)


@cursos.route('/api/chat-educativo', methods=['POST'])
@login_required
def api_chat_educativo():
    data = request.json
    mensaje = data.get('mensaje')
    contexto = data.get('contexto', 'Matemáticas general')

    if not mensaje:
        return {'error': 'Mensaje vacío'}, 400

    from ..servicios.ia_servicio import ServicioIA
    servicio = ServicioIA()
    respuesta = servicio.chat_educativo(mensaje, contexto)
    return {'respuesta': respuesta}


# ─────────────────────────────────────
# Certificado PDF
# ─────────────────────────────────────
@cursos.route('/<int:id>/certificado')
@login_required
def descargar_certificado(id):
    """Genera y descarga un certificado PDF cuando el progreso es 100%."""
    if current_user.rol != 'estudiante':
        flash('Solo los estudiantes pueden descargar certificados.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id))

    curso = Curso.query.get_or_404(id)
    inscripcion = Inscripcion.query.filter_by(
        id_estudiante=current_user.id,
        id_curso=id
    ).first()

    if inscripcion and getattr(inscripcion, 'bloqueado', False):
        flash('Tu acceso fue bloqueado por el docente.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id))

    real = progreso_por_lecciones_completadas(current_user.id, id)
    if inscripcion and abs(inscripcion.progreso - real) > 0.02:
        inscripcion.progreso = real
        bd.session.commit()

    if not inscripcion or real < 100:
        flash('Debes completar el curso al 100% para obtener el certificado.', 'peligro')
        return redirect(url_for('cursos.ver_curso', id=id))

    from io import BytesIO
    from flask import Response
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import cm
    from datetime import datetime

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elementos = []

    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=36,
                                   textColor=colors.HexColor('#4F46E5'), spaceAfter=10, fontName='Helvetica-Bold')
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Normal'], fontSize=14,
                                      textColor=colors.HexColor('#64748B'), spaceAfter=6, alignment=1)
    estilo_nombre = ParagraphStyle('Nombre', parent=styles['Normal'], fontSize=28,
                                   textColor=colors.HexColor('#1E293B'), fontName='Helvetica-Bold',
                                   alignment=1, spaceAfter=6)
    estilo_curso = ParagraphStyle('Curso', parent=styles['Normal'], fontSize=20,
                                  textColor=colors.HexColor('#4F46E5'), fontName='Helvetica-Bold',
                                  alignment=1, spaceAfter=6)
    estilo_normal_c = ParagraphStyle('NormalC', parent=styles['Normal'], fontSize=12,
                                     textColor=colors.HexColor('#64748B'), alignment=1, spaceAfter=4)

    fecha_str = datetime.utcnow().strftime('%d de %B de %Y')

    elementos.append(Spacer(1, 1*cm))
    elementos.append(Paragraph("🎓 MATATUCAS", estilo_titulo))
    elementos.append(Paragraph("Plataforma Educativa con IA", estilo_subtitulo))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor('#4F46E5')))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("Certifica que", estilo_subtitulo))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(current_user.nombre, estilo_nombre))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("ha completado satisfactoriamente el curso:", estilo_subtitulo))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(curso.titulo, estilo_curso))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph(f"Nivel: {curso.nivel.capitalize()}", estilo_subtitulo))
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width="60%", thickness=1, color=colors.HexColor('#E2E8F0')))
    elementos.append(Spacer(1, 0.4*cm))
    elementos.append(Paragraph(f"Emitido el {fecha_str}", estilo_normal_c))

    doc.build(elementos)
    buffer.seek(0)

    nombre_archivo = f"certificado_{curso.titulo.replace(' ', '_')}.pdf"
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{nombre_archivo}"'}
    )
