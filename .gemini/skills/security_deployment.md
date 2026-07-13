# Matatucas LMS - Seguridad y Despliegue

## Autenticación
- **Microsoft SSO** exclusivo (Azure AD / Entra ID) vía `msal`
- No hay formulario de login local (email/password eliminado)
- Redirect URI dinámico: `url_for('auth.callback', _external=True)` soporta localhost e IP
- Roles asignados automáticamente por patrón de email:
  - Matrícula (ej. `L23TE0030@...`): estudiante
  - Otro: docente
  - Superusuarios hardcodeados: administrador
- Registro automático en primer login

## Protección CSRF
- `Flask-WTF CSRFProtect` global
- Todos los formularios POST incluyen `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`
- APIs JSON protegidas con header `X-CSRFToken`

## Control de Acceso
- Decoradores en cascada: `@login_required` → `@docente_required` → `@curso_owner_required`
- Verificación inline de permisos cuando los decoradores no aplican
- `@curso_owner_required` inyecta `_curso` en kwargs para evitar query duplicada

## Auditoría
- `registrar_accion(accion, detalles)` en `app/servicios/auditoria_servicio.py`
- Registra usuario, acción, detalles JSON, IP, timestamp
- Acciones registradas: CREAR_CURSO, ELIMINAR_CURSO, DUPLICAR_CURSO, CAMBIO_ROL, etc.

## Configuración de Red
- `run.py`: `app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')`
- HTTPS con certificados autogenerados (pyOpenSSL)
- Requiere registrar ambas redirect URIs en Azure AD:
  - `https://localhost:5000/auth/callback`
  - `https://<IP_LOCAL>:5000/auth/callback`

## Variables de Entorno (.env)
```
SECRET_KEY=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT_ID=...
MICROSOFT_REDIRECT_URI=https://localhost:5000/auth/callback
DATABASE_URL=mysql+mysqlconnector://root:@localhost/Matatucas_db
```

## Despliegue (Notas)
- Actualmente solo desarrollo local con XAMPP
- Para producción: usar Gunicorn/uWSGI, certificados SSL reales, MySQL remoto
- `.gitignore` excluye: `__pycache__/`, `.env`, `.venv/`, `*.db`, `*.log`, `tmp/`
- `pyOpenSSL` necesario para modo HTTPS adhoc en desarrollo
