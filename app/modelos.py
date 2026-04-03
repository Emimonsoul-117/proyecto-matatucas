from . import bd
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, bd.Model):
    __tablename__ = 'usuarios'
    id = bd.Column(bd.Integer, primary_key=True)
    email = bd.Column(bd.String(120), unique=True, nullable=False)
    password_hash = bd.Column(bd.String(256), nullable=True)
    nombre = bd.Column(bd.String(100), nullable=False)
    numero_control = bd.Column(bd.String(20), unique=True)
    microsoft_id = bd.Column(bd.String(100), unique=True, nullable=True)
    rol = bd.Column(bd.Enum('administrador', 'docente', 'estudiante'), nullable=False)
    fecha_registro = bd.Column(bd.DateTime, default=datetime.utcnow)

    @property
    def nombre_usuario(self):
        """Devuelve el nombre para mostrar en la interfaz."""
        return self.nombre.split()[0] if self.nombre else self.email.split('@')[0]

    def get_id(self):
        return str(self.id)

class Estudiante(bd.Model):
    __tablename__ = 'estudiantes'
    id_usuario = bd.Column(bd.Integer, bd.ForeignKey('usuarios.id'), primary_key=True)
    puntos_totales = bd.Column(bd.Integer, default=0)
    racha_dias = bd.Column(bd.Integer, default=0)
    ultimo_login = bd.Column(bd.DateTime, nullable=True)
    carrera = bd.Column(bd.String(100), nullable=True)
    semestre = bd.Column(bd.Integer, nullable=True)
    grupo = bd.Column(bd.String(10), nullable=True)
    fecha_actualizacion_semestre = bd.Column(bd.DateTime, default=datetime.utcnow)
    monedas = bd.Column(bd.Integer, default=0)
    avatar_activo = bd.Column(bd.String(255), nullable=True)
    marco_activo = bd.Column(bd.String(255), nullable=True)

    @property
    def semestre_actual(self):
        """Calcula el semestre actual basado en el tiempo transcurrido (periodos TecNM)."""
        if not self.semestre or not self.fecha_actualizacion_semestre:
            return self.semestre
            
        def get_period_id(dt):
            # TecNM: Enero-Junio (0) y Agosto-Diciembre (1)
            # Corte común en julio/agosto.
            half = 0 if dt.month < 8 else 1
            return dt.year * 2 + half

        now_period = get_period_id(datetime.utcnow())
        saved_period = get_period_id(self.fecha_actualizacion_semestre)
        
        diff = now_period - saved_period
        # Calcular nuevo semestre asegurando que no pase de 12
        calculated_sem = self.semestre + diff
        return min(calculated_sem, 12) if calculated_sem > 0 else 1

class Docente(bd.Model):
    __tablename__ = 'docentes'
    id_usuario = bd.Column(bd.Integer, bd.ForeignKey('usuarios.id'), primary_key=True)
    especialidad = bd.Column(bd.String(100))


def asegurar_fila_docente_si_falta(usuario):
    """Crea docentes.id_usuario si el usuario es docente/admin y falta la fila (evita error FK al crear cursos)."""
    if usuario is None or usuario.rol not in ('docente', 'administrador'):
        return
    if Docente.query.get(usuario.id):
        return
    especialidad = 'Administración' if usuario.rol == 'administrador' else 'General'
    bd.session.add(Docente(id_usuario=usuario.id, especialidad=especialidad))


class Curso(bd.Model):
    __tablename__ = 'cursos'
    id = bd.Column(bd.Integer, primary_key=True)
    codigo_curso = bd.Column(bd.String(16), unique=True, nullable=True, index=True)
    titulo = bd.Column(bd.String(150), nullable=False)
    descripcion = bd.Column(bd.Text)
    nivel = bd.Column(bd.Enum('basico', 'intermedio', 'avanzado'), nullable=False)
    id_docente = bd.Column(bd.Integer, bd.ForeignKey('docentes.id_usuario'))
    fecha_creacion = bd.Column(bd.DateTime, default=datetime.utcnow)
    estado = bd.Column(bd.Enum('borrador', 'revision', 'publicado'), default='borrador', nullable=False)
    
    # Relaciones
    lecciones = bd.relationship('Leccion', backref='curso', lazy=True)
    inscripciones = bd.relationship('Inscripcion', backref='curso', lazy=True)

class Leccion(bd.Model):
    __tablename__ = 'lecciones'
    id = bd.Column(bd.Integer, primary_key=True)
    id_curso = bd.Column(bd.Integer, bd.ForeignKey('cursos.id'), nullable=False)
    titulo = bd.Column(bd.String(150), nullable=False)
    orden = bd.Column(bd.Integer, nullable=False)
    contenido_teoria = bd.Column(bd.Text)  # Legacy: plain text/HTML
    secciones = bd.Column(bd.JSON, nullable=True)  # New: list of section blocks
    # secciones format: [{"tipo": "teoria"|"video"|"ejercicio", ...}, ...]

    ejercicios = bd.relationship('Ejercicio', backref='leccion', lazy=True)
    videos = bd.relationship('Video', backref='leccion', lazy=True)

class Video(bd.Model):
    __tablename__ = 'videos'
    id = bd.Column(bd.Integer, primary_key=True)
    id_leccion = bd.Column(bd.Integer, bd.ForeignKey('lecciones.id'), nullable=False)
    url_youtube = bd.Column(bd.String(255), nullable=False)
    titulo = bd.Column(bd.String(150))

class Ejercicio(bd.Model):
    __tablename__ = 'ejercicios'
    id = bd.Column(bd.Integer, primary_key=True)
    id_leccion = bd.Column(bd.Integer, bd.ForeignKey('lecciones.id'), nullable=False)
    enunciado = bd.Column(bd.Text, nullable=False)
    tipo = bd.Column(bd.Enum('opcion_multiple', 'verdadero_falso', 'numerico'), nullable=False)
    opciones = bd.Column(bd.JSON) # Almacena opciones como JSON
    respuesta_correcta = bd.Column(bd.String(255), nullable=False)
    dificultad = bd.Column(bd.Integer, default=1)


class IntentoEjercicio(bd.Model):
    __tablename__ = 'intentos_ejercicios'

    id = bd.Column(bd.Integer, primary_key=True)
    id_estudiante = bd.Column(
        bd.Integer,
        bd.ForeignKey('estudiantes.id_usuario'),
        nullable=False,
        index=True,
    )
    id_ejercicio = bd.Column(
        bd.Integer,
        bd.ForeignKey('ejercicios.id'),
        nullable=False,
        index=True,
    )
    intento_num = bd.Column(bd.Integer, nullable=False, default=1)
    respuesta_usuario = bd.Column(bd.String(255), nullable=True)
    es_correcta = bd.Column(bd.Boolean, nullable=False, default=False)
    puntaje = bd.Column(bd.Float, nullable=False, default=0.0)
    fecha_intento = bd.Column(bd.DateTime, default=datetime.utcnow)

    __table_args__ = (
        bd.UniqueConstraint(
            'id_estudiante',
            'id_ejercicio',
            'intento_num',
            name='unique_intento_ejercicio',
        ),
    )

class Inscripcion(bd.Model):
    __tablename__ = 'inscripciones'
    id = bd.Column(bd.Integer, primary_key=True)
    id_estudiante = bd.Column(bd.Integer, bd.ForeignKey('estudiantes.id_usuario'), nullable=False)
    id_curso = bd.Column(bd.Integer, bd.ForeignKey('cursos.id'), nullable=False)
    fecha_inscripcion = bd.Column(bd.DateTime, default=datetime.utcnow)
    progreso = bd.Column(bd.Float, default=0.0)
    bloqueado = bd.Column(bd.Boolean, default=False, nullable=False)

class Insignia(bd.Model):
    __tablename__ = 'insignias'
    id = bd.Column(bd.Integer, primary_key=True)
    nombre = bd.Column(bd.String(100), nullable=False)
    descripcion = bd.Column(bd.String(255))
    icono = bd.Column(bd.String(50)) # Clase de icono Bootstrap o URL
    criterio = bd.Column(bd.String(50)) # Identificador interno para lógica (ej: 'racha_7')
    nivel_requerido = bd.Column(bd.Integer, default=1)

class InsigniaEstudiante(bd.Model):
    __tablename__ = 'insignias_estudiantes'
    id = bd.Column(bd.Integer, primary_key=True)
    id_estudiante = bd.Column(bd.Integer, bd.ForeignKey('estudiantes.id_usuario'), nullable=False)
    id_insignia = bd.Column(bd.Integer, bd.ForeignKey('insignias.id'), nullable=False)
    fecha_obtencion = bd.Column(bd.DateTime, default=datetime.utcnow)

    # Relaciones para facilitar acceso
    insignia = bd.relationship('Insignia')
    estudiante = bd.relationship('Estudiante', backref=bd.backref('logros', lazy=True))

class LeccionCompletada(bd.Model):
    __tablename__ = 'lecciones_completadas'
    id = bd.Column(bd.Integer, primary_key=True)
    id_estudiante = bd.Column(bd.Integer, bd.ForeignKey('estudiantes.id_usuario'), nullable=False)
    id_leccion = bd.Column(bd.Integer, bd.ForeignKey('lecciones.id'), nullable=False)
    fecha_completada = bd.Column(bd.DateTime, default=datetime.utcnow)

    __table_args__ = (bd.UniqueConstraint('id_estudiante', 'id_leccion', name='unique_completion'),)


class ConfiguracionUsuario(bd.Model):
    __tablename__ = 'configuracion_usuario'
    id_usuario = bd.Column(bd.Integer, bd.ForeignKey('usuarios.id'), primary_key=True)
    tema = bd.Column(bd.String(10), default='claro', nullable=False)
    ocultar_ranking = bd.Column(bd.Boolean, default=False, nullable=False)
    tamano_fuente = bd.Column(bd.String(10), default='normal', nullable=False)
    notif_nuevos_cursos = bd.Column(bd.Boolean, default=True, nullable=False)
    notif_racha = bd.Column(bd.Boolean, default=True, nullable=False)


class ArticuloTienda(bd.Model):
    __tablename__ = 'articulos_tienda'
    id = bd.Column(bd.Integer, primary_key=True)
    nombre = bd.Column(bd.String(100), nullable=False)
    descripcion = bd.Column(bd.String(255))
    tipo = bd.Column(bd.Enum('avatar', 'marco'), nullable=False)
    precio = bd.Column(bd.Integer, nullable=False, default=0)
    icono = bd.Column(bd.String(255))          # Bootstrap icon class or emoji
    css_clase = bd.Column(bd.String(255))       # CSS class for border/frame
    rareza = bd.Column(bd.Enum('comun', 'raro', 'epico', 'legendario'), default='comun', nullable=False)
    activo = bd.Column(bd.Boolean, default=True, nullable=False)


class InventarioEstudiante(bd.Model):
    __tablename__ = 'inventario_estudiante'
    id = bd.Column(bd.Integer, primary_key=True)
    id_estudiante = bd.Column(bd.Integer, bd.ForeignKey('estudiantes.id_usuario'), nullable=False)
    id_articulo = bd.Column(bd.Integer, bd.ForeignKey('articulos_tienda.id'), nullable=False)
    fecha_compra = bd.Column(bd.DateTime, default=datetime.utcnow)

    articulo = bd.relationship('ArticuloTienda')
    __table_args__ = (bd.UniqueConstraint('id_estudiante', 'id_articulo', name='unique_inv'),)


def progreso_por_lecciones_completadas(id_estudiante, id_curso):
    """Porcentaje 0–100 según lecciones completadas vs total (sin depender del valor guardado en inscripción)."""
    total = Leccion.query.filter_by(id_curso=id_curso).count()
    if total == 0:
        return 0.0
    hechas = (
        LeccionCompletada.query.join(Leccion)
        .filter(
            LeccionCompletada.id_estudiante == id_estudiante,
            Leccion.id_curso == id_curso,
        )
        .count()
    )
    return min(100.0, round((hechas / total) * 100, 1))


class RegistroAuditoria(bd.Model):
    __tablename__ = 'registro_auditoria'
    id = bd.Column(bd.Integer, primary_key=True)
    id_usuario = bd.Column(bd.Integer, bd.ForeignKey('usuarios.id'), nullable=False)
    accion = bd.Column(bd.String(100), nullable=False) # ej: 'ELIMINAR_CURSO', 'CAMBIO_ROL'
    detalles = bd.Column(bd.JSON) # Datos adicionales del cambio
    ip_address = bd.Column(bd.String(45))
    timestamp = bd.Column(bd.DateTime, default=datetime.utcnow)

    usuario = bd.relationship('Usuario')


class ConfiguracionGlobal(bd.Model):
    __tablename__ = 'configuracion_global'
    clave = bd.Column(bd.String(50), primary_key=True)
    valor = bd.Column(bd.Text)
    descripcion = bd.Column(bd.String(255))
    ultima_actualizacion = bd.Column(bd.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
