from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func
from . import docente
from .. import bd
from ..modelos import (
    Curso,
    Leccion,
    Inscripcion,
    Usuario,
    Estudiante,
    LeccionCompletada,
    IntentoEjercicio,
    Ejercicio,
    progreso_por_lecciones_completadas,
)
from ..decoradores import docente_required


@docente.route('/')
@docente.route('/dashboard')
@login_required
@docente_required
def dashboard():
    """Dashboard principal del docente con métricas globales y lista de cursos."""
    ver_todos = request.args.get('ver_todos', type=int) == 1
    # 1. Obtener cursos y lecciones (usamos dict para rápido acceso por id)
    if current_user.rol == 'administrador' and ver_todos:
        cursos = Curso.query.order_by(Curso.fecha_creacion.desc()).all()
    else:
        cursos = Curso.query.filter_by(id_docente=current_user.id).order_by(Curso.fecha_creacion.desc()).all()
    
    if not cursos:
        return render_template('docente/dashboard_docente.html', cursos_info=[], total_cursos=0, total_alumnos=0, 
                               total_lecciones=0, cursos_publicados=0, cursos_borrador=0, actividad_reciente=[],
                               progreso_global=0, tasa_completitud=0)

    ids_cursos = [c.id for c in cursos]

    # 2. Subquery para contar lecciones por curso
    lecciones_count = (
        bd.session.query(Leccion.id_curso, func.count(Leccion.id).label('count'))
        .filter(Leccion.id_curso.in_(ids_cursos))
        .group_by(Leccion.id_curso)
        .all()
    )
    dict_lecciones = {lc.id_curso: lc.count for lc in lecciones_count}

    # 3. Subquery para métricas de inscritos (progresos)
    # Obtenemos lecciones completadas por cada inscripción
    metricas_estudiantes = (
        bd.session.query(
            Inscripcion.id_curso,
            Inscripcion.id_estudiante,
            func.count(LeccionCompletada.id).label('completadas')
        )
        .outerjoin(LeccionCompletada, (Inscripcion.id_estudiante == LeccionCompletada.id_estudiante))
        .join(Leccion, (LeccionCompletada.id_leccion == Leccion.id))
        .filter(Inscripcion.id_curso.in_(ids_cursos))
        .filter(Leccion.id_curso == Inscripcion.id_curso)
        .group_by(Inscripcion.id_curso, Inscripcion.id_estudiante)
        .all()
    )

    # Procesar métricas globales
    total_progreso_acumulado = 0
    total_completados = 0
    total_inscripciones = 0
    
    # Agrupar por curso para cursos_info (ya tenemos dict_lecciones)
    for me in metricas_estudiantes:
        total_inscripciones += 1
        num_lecc = dict_lecciones.get(me.id_curso, 0)
        prog = (me.completadas / num_lecc * 100) if num_lecc > 0 else 0
        total_progreso_acumulado += prog
        if prog >= 100:
            total_completados += 1
            
    # Contar alumnos únicos por curso (para la lista)
    inscritos_por_curso = (
        bd.session.query(Inscripcion.id_curso, func.count(Inscripcion.id).label('count'))
        .filter(Inscripcion.id_curso.in_(ids_cursos))
        .group_by(Inscripcion.id_curso)
        .all()
    )
    dict_inscritos_count = {ic.id_curso: ic.count for ic in inscritos_por_curso}

    cursos_info = []
    for c in cursos:
        num_lecc = dict_lecciones.get(c.id, 0)
        num_ins = dict_inscritos_count.get(c.id, 0)
        cursos_info.append({
            'curso': c,
            'num_inscritos': num_ins,
            'num_lecciones': num_lecc,
        })

    # Actividad reciente
    ultimas_inscripciones = (
        Inscripcion.query
        .join(Usuario, Inscripcion.id_estudiante == Usuario.id)
        .join(Curso, Inscripcion.id_curso == Curso.id)
        .filter(Inscripcion.id_curso.in_(ids_cursos))
        .order_by(Inscripcion.fecha_inscripcion.desc())
        .limit(10)
        .with_entities(Usuario.nombre, Curso.titulo, Inscripcion.fecha_inscripcion)
        .all()
    )
    
    actividad_reciente = [{
        'tipo': 'inscripcion',
        'alumno': res.nombre,
        'curso': res.titulo,
        'fecha': res.fecha_inscripcion
    } for res in ultimas_inscripciones]

    # Métricas finales
    total_alumnos = sum(dict_inscritos_count.values())
    progreso_global = round(total_progreso_acumulado / total_inscripciones, 1) if total_inscripciones > 0 else 0
    tasa_completitud = round(total_completados / total_inscripciones * 100, 1) if total_inscripciones > 0 else 0

    return render_template(
        'docente/dashboard_docente.html',
        cursos_info=cursos_info,
        total_cursos=len(cursos),
        total_alumnos=total_alumnos,
        total_lecciones=sum(dict_lecciones.values()),
        cursos_publicados=sum(1 for c in cursos if c.estado == 'publicado'),
        cursos_borrador=sum(1 for c in cursos if c.estado == 'borrador'),
        actividad_reciente=actividad_reciente,
        progreso_global=progreso_global,
        tasa_completitud=tasa_completitud,
        ver_todos=ver_todos
    )
