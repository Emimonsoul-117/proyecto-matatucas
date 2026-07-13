# Backend Architecture & Patterns - Matatucas LMS

## App Factory Pattern (app/__init__.py)
```python
def crear_app(nombre_config='por_defecto'):
    app = Flask(__name__)
    app.config.from_object(configuracion[nombre_config])
    bd.init_app(app)         # SQLAlchemy
    login_manager.init_app(app)  # Flask-Login
    csrf.init_app(app)       # Flask-WTF CSRF

    # Schema migrations (auto-ALTER TABLE for new columns)
    _ensure_codigo_curso_column(app)
    _ensure_bloqueado_inscripciones_column(app)
    _ensure_estado_cursos_column(app)
    _ensure_visibilidad_cursos_column(app)

    # Create new tables automatically
    with app.app_context():
        from . import modelos
        bd.create_all()

    # Register blueprints
    # Register error handlers (404, 403, 500)
    return app
```

## Blueprint Structure
Each blueprint follows this directory pattern:
```
app/blueprint_name/
├── __init__.py     # Blueprint creation + import routes
└── rutas.py        # All route definitions
```

## Security Decorators (app/decoradores.py)

### @admin_required
- Checks `current_user.rol == 'administrador'`
- Returns `abort(403)` if unauthorized

### @docente_required
- Allows both `'docente'` and `'administrador'` roles
- Returns `abort(403)` if unauthorized

### @curso_owner_required (PREFERRED for course operations)
- Verifies user owns the course OR is admin
- **Injects `_curso` kwarg** — the loaded Curso object
- Avoids duplicate DB query for the course
- Usage:
```python
@cursos.route('/<int:id_curso>/action', methods=['POST'])
@login_required
@curso_owner_required
def my_action(id_curso, _curso):
    curso = _curso  # Already loaded by decorator
```

## Database Patterns

### Optimized Queries (No N+1)
```python
# Step 1: Create subqueries for aggregated metrics
sub_completadas = (
    bd.session.query(
        LeccionCompletada.id_estudiante,
        func.count(LeccionCompletada.id).label('completadas')
    )
    .join(Leccion, LeccionCompletada.id_leccion == Leccion.id)
    .filter(Leccion.id_curso == id_curso)
    .group_by(LeccionCompletada.id_estudiante)
    .subquery()
)

# Step 2: Main query with LEFT JOINs
results = (
    bd.session.query(
        Usuario,
        func.coalesce(sub_completadas.c.completadas, 0).label('count')
    )
    .join(Inscripcion, Usuario.id == Inscripcion.id_estudiante)
    .outerjoin(sub_completadas, Usuario.id == sub_completadas.c.id_estudiante)
    .filter(Inscripcion.id_curso == id_curso)
    .all()
)
```

### Schema Migration Pattern
- New columns: Add `_ensure_*_column()` function in `__init__.py`
- These run on EVERY app start — idempotent (check before ALTER)
- New tables: Handled by `bd.create_all()`

## Service Layer (app/servicios/)
Services encapsulate business logic away from routes:
- `ia_servicio.py` — Gemini AI integration (exercises, chat, explanations)
- `excel_servicio.py` — Excel generation with openpyxl
- `auditoria_servicio.py` — Audit trail logging
- `reportes_servicio.py` — PDF report generation with ReportLab

## API Endpoints Pattern
```python
@cursos.route('/api/endpoint', methods=['POST'])
@login_required
def api_endpoint():
    data = request.json
    # Validate
    if not data.get('field'):
        return {'error': 'Falta campo'}, 400
    # Process
    result = process(data)
    # Return JSON
    return jsonify(result)
```

## Authentication Flow (Microsoft SSO)
1. User clicks "Iniciar sesión con Microsoft"
2. MSAL generates auth URL → redirect to Microsoft
3. Microsoft authenticates → callback to `/auth/callback`
4. App creates/finds user by `microsoft_id`
5. Auto-role assignment based on email domain:
   - `@teziutlan.tecnm.mx` → docente
   - `@teziutlan.tecnm.mx` (student pattern) → estudiante
