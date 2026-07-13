# Coding Conventions & Best Practices - Matatucas LMS

## Python / Flask Backend

### Naming Conventions
- **Variables y funciones**: `snake_case` en español (ej. `ver_alumnos_curso`, `total_lecciones`)
- **Clases/Modelos**: `PascalCase` en español (ej. `LeccionCompletada`, `IntentoEjercicio`)
- **Templates**: `snake_case.html` en español
- **Blueprints**: sustantivo singular (`auth`, `cursos`, `admin`, `docente`)
- **Rutas URL**: kebab-case con español (ej. `/exportar-alumnos`, `/nuevo-ejercicio`)

### Route Patterns
```python
# Siempre usar este orden de decoradores:
@blueprint.route('/path', methods=['GET', 'POST'])
@login_required
@role_decorator          # docente_required, admin_required, curso_owner_required
def nombre_funcion():
    ...
```

### Security Patterns
- **NUNCA verificar permisos inline** cuando existe `@curso_owner_required`
- `@curso_owner_required` inyecta `_curso` como kwarg — usarlo siempre
- CSRF tokens obligatorios en todos los formularios POST
- Validar y sanitizar todos los inputs del usuario con `[:150]` para strings

### Database Query Patterns
- **PROHIBIDO**: Loops N+1 (query dentro de un for)
- **REQUERIDO**: Subqueries con `bd.session.query().subquery()` y `outerjoin()`
- Usar `func.coalesce(subquery.c.column, 0)` para valores nulos
- `func.cast(column, bd.Integer)` para convertir booleanos en sumas

### Flash Messages Categories
- `'exito'` - Operación exitosa (verde)
- `'peligro'` - Error o prohibición (rojo)
- `'advertencia'` - Warning no bloqueante (amarillo)
- `'info'` - Información neutral (azul)

### File Organization
```
app/
├── __init__.py          # App factory, migrations, error handlers
├── modelos.py           # ALL models in one file
├── decoradores.py       # Security decorators
├── auth/                # Microsoft SSO
├── main/                # Landing, profile, config, rankings
├── cursos/              # All course CRUD + student interactions
├── docente/             # Teacher dashboard
├── admin/               # Admin panel
├── servicios/           # Business logic services
│   ├── ia_servicio.py
│   ├── excel_servicio.py
│   ├── auditoria_servicio.py
│   └── reportes_servicio.py
└── templates/
    ├── base.html        # Master layout
    └── errores/         # 404, 403, 500
```

### Error Handling
- Use `get_or_404()` for individual record lookups
- Use `abort(400)` for bad requests (validation failures)
- Custom error pages registered in `__init__.py`
- Always wrap DB operations in try/except for batch operations

### Auditing
- All destructive/important actions MUST call `registrar_accion()`
- Actions: CREAR_CURSO, DUPLICAR_CURSO, ELIMINAR_CURSO, PUBLICAR_CURSO, etc.
- Details dict should include relevant IDs and human-readable info
