import re
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..modelos import Usuario, Estudiante, Docente, asegurar_fila_docente_si_falta
from .. import bd
import msal


def _build_msal_app(cache=None):
    """Construye la aplicación MSAL confidencial."""
    client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
    tenant_id = current_app.config.get('MICROSOFT_TENANT_ID')

    if not client_id or not tenant_id or client_id == 'TU_CLIENT_ID_AQUI' or tenant_id == 'TU_TENANT_ID_AQUI':
        return None

    return msal.ConfidentialClientApplication(
        client_id,
        authority=current_app.config['MICROSOFT_AUTHORITY'],
        client_credential=current_app.config.get('MICROSOFT_CLIENT_SECRET'),
        token_cache=cache
    )


def _build_auth_url(app_msal, scopes=None):
    """Genera la URL de autorización de Microsoft."""
    if not app_msal:
        return None
        
    auth_url = app_msal.get_authorization_request_url(
        scopes or current_app.config.get('MICROSOFT_SCOPE', ["User.Read"]),
        redirect_uri=current_app.config.get('MICROSOFT_REDIRECT_URI')
    )
    return auth_url


SUPERUSUARIOS = [
    'l23te0030@teziutlan.tecnm.mx'
]

def _determinar_rol(email):
    """
    Determina el rol basándose en el formato del correo institucional.
    Patrón de matrícula (estudiante): L23TE0030@teziutlan.tecnm.mx
    - Empieza con letra(s), seguido de números, letras, números
    Si no coincide con patrón de matrícula, se asume docente.
    """
    email_lower = email.lower()
    if email_lower in SUPERUSUARIOS:
        return 'administrador'

    parte_local = email_lower.split('@')[0]
    # Patrón típico de matrícula TecNM: letra(s) + 2 dígitos + 2 letras + 4 dígitos
    patron_matricula = re.compile(r'^[A-Za-z]\d{2}[A-Za-z]{2}\d{4}$', re.IGNORECASE)
    if patron_matricula.match(parte_local):
        return 'estudiante'
    return 'docente'


def _extraer_numero_control(email):
    """Extrae el número de control del correo institucional si es estudiante."""
    email_lower = email.lower()
    if email_lower in SUPERUSUARIOS:
         return None
         
    parte_local = email_lower.split('@')[0]
    patron_matricula = re.compile(r'^[A-Za-z]\d{2}[A-Za-z]{2}\d{4}$', re.IGNORECASE)
    if patron_matricula.match(parte_local):
        return parte_local.upper()
    return None


@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Generar URL de autorización de Microsoft y redirigir
    app_msal = _build_msal_app()
    if not app_msal:
        flash('⚠️ El inicio de sesión con Microsoft no está configurado. Faltan las credenciales en el archivo .env', 'peligro')
        return redirect(url_for('auth.login_page'))
        
    auth_url = _build_auth_url(app_msal)
    return redirect(auth_url)


@auth.route('/login-page')
def login_page():
    """Muestra la página de login con el botón de Microsoft."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('auth/login.html')


@auth.route('/callback')
def callback():
    """Callback de Microsoft después de la autenticación."""
    if request.args.get('error'):
        error_desc = request.args.get('error_description', 'Error desconocido')
        flash(f'Error de autenticación: {error_desc}', 'peligro')
        return redirect(url_for('auth.login_page'))

    code = request.args.get('code')
    if not code:
        flash('No se recibió código de autorización.', 'peligro')
        return redirect(url_for('auth.login_page'))

    # Intercambiar código por token
    app_msal = _build_msal_app()
    if not app_msal:
        flash('Inicio de sesión no configurado.', 'peligro')
        return redirect(url_for('auth.login_page'))
        
    result = app_msal.acquire_token_by_authorization_code(
        code,
        scopes=current_app.config['MICROSOFT_SCOPE'],
        redirect_uri=current_app.config['MICROSOFT_REDIRECT_URI']
    )

    if 'error' in result:
        flash(f"Error al obtener token: {result.get('error_description', result.get('error'))}", 'peligro')
        return redirect(url_for('auth.login_page'))

    # Extraer información del usuario del token ID
    id_token_claims = result.get('id_token_claims', {})
    microsoft_id = id_token_claims.get('oid') or id_token_claims.get('sub')
    email = id_token_claims.get('preferred_username') or id_token_claims.get('email', '')
    nombre = id_token_claims.get('name', email.split('@')[0])

    if not email:
        flash('No se pudo obtener el correo electrónico de Microsoft.', 'peligro')
        return redirect(url_for('auth.login_page'))

    email = email.lower()

    # Buscar usuario existente por microsoft_id o email
    usuario = None
    if microsoft_id:
        usuario = Usuario.query.filter_by(microsoft_id=microsoft_id).first()
    if not usuario:
        usuario = Usuario.query.filter_by(email=email).first()

    if usuario:
        # Actualizar microsoft_id si no lo tenía
        if microsoft_id and not usuario.microsoft_id:
            usuario.microsoft_id = microsoft_id
        # Actualizar nombre si cambió
        if nombre and usuario.nombre != nombre:
            usuario.nombre = nombre
        bd.session.commit()
    else:
        # Crear usuario nuevo automáticamente
        rol = _determinar_rol(email)
        numero_control = _extraer_numero_control(email)

        usuario = Usuario(
            email=email,
            nombre=nombre,
            password_hash=None,
            rol=rol,
            numero_control=numero_control,
            microsoft_id=microsoft_id
        )

        bd.session.add(usuario)
        bd.session.commit()

        # Crear registro en tabla específica según rol
        if rol == 'estudiante':
            estudiante = Estudiante(id_usuario=usuario.id)
            bd.session.add(estudiante)
        elif rol in ('docente', 'administrador'):
            esp = 'Administración' if rol == 'administrador' else 'General'
            bd.session.add(Docente(id_usuario=usuario.id, especialidad=esp))

        bd.session.commit()
        flash('¡Bienvenido! Tu cuenta ha sido creada automáticamente.', 'exito')

    login_user(usuario, remember=True)
    asegurar_fila_docente_si_falta(usuario)
    bd.session.commit()

    # Actualizar racha de estudio si es estudiante
    if usuario.rol == 'estudiante':
        from ..servicios.gamificacion_servicio import ServicioGamificacion
        ServicioGamificacion().actualizar_racha_login(usuario.id)

    return redirect(url_for('main.dashboard'))


@auth.route('/logout')
@login_required
def logout():
    """Solo cierra la sesión en esta aplicación; no desconecta la cuenta de Microsoft en el navegador."""
    logout_user()
    return redirect(url_for('main.index'))
