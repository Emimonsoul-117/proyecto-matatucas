from flask import render_template, redirect, url_for
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
    cursos = Curso.query.filter_by(id_docente=current_user.id).order_by(Curso.fecha_creacion.desc()).all()

    # Métricas globales
    total_cursos = len(cursos)
    ids_cursos = [c.id for c in cursos]

    total_alumnos = 0
    total_lecciones_global = 0
    cursos_info = []

    for curso in cursos:
        num_inscritos = Inscripcion.query.filter_by(id_curso=curso.id).count()
        num_lecciones = Leccion.query.filter_by(id_curso=curso.id).count()
        total_alumnos += num_inscritos
        total_lecciones_global += num_lecciones

        cursos_info.append({
            'curso': curso,
            'num_inscritos': num_inscritos,
            'num_lecciones': num_lecciones,
        })

    cursos_publicados = sum(1 for c in cursos if c.estado == 'publicado')
    cursos_borrador = sum(1 for c in cursos if c.estado == 'borrador')

    # Últimas inscripciones a cursos del docente (actividad reciente)
    actividad_reciente = []
    if ids_cursos:
        ultimas_inscripciones = (
            Inscripcion.query
            .filter(Inscripcion.id_curso.in_(ids_cursos))
            .order_by(Inscripcion.fecha_inscripcion.desc())
            .limit(10)
            .all()
        )
        for ins in ultimas_inscripciones:
            usuario = Usuario.query.get(ins.id_estudiante)
            curso = Curso.query.get(ins.id_curso)
            if usuario and curso:
                actividad_reciente.append({
                    'tipo': 'inscripcion',
                    'alumno': usuario.nombre,
                    'curso': curso.titulo,
                    'fecha': ins.fecha_inscripcion,
                })

    return render_template(
        'docente/dashboard_docente.html',
        cursos_info=cursos_info,
        total_cursos=total_cursos,
        total_alumnos=total_alumnos,
        total_lecciones=total_lecciones_global,
        cursos_publicados=cursos_publicados,
        cursos_borrador=cursos_borrador,
        actividad_reciente=actividad_reciente,
    )
