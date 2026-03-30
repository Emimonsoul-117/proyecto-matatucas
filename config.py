import os
from dotenv import load_dotenv

load_dotenv()

class Configuracion:
    """Configuración base para la aplicación."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-secreta-muy-dificil-de-adivinar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Microsoft Azure AD / Entra ID
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID')
    MICROSOFT_AUTHORITY = f"https://login.microsoftonline.com/{os.environ.get('MICROSOFT_TENANT_ID', 'common')}"
    MICROSOFT_REDIRECT_URI = os.environ.get('MICROSOFT_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    MICROSOFT_SCOPE = ["User.Read"]

class ConfiguracionDesarrollo(Configuracion):
    """Configuración para el entorno de desarrollo."""
    DEBUG = True
    # Configuración de conexión a MySQL con XAMPP (usuario root, sin contraseña por defecto)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+mysqlconnector://root:@localhost/Matatucas_db'

class ConfiguracionProduccion(Configuracion):
    """Configuración para el entorno de producción."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

configuracion = {
    'desarrollo': ConfiguracionDesarrollo,
    'produccion': ConfiguracionProduccion,
    'por_defecto': ConfiguracionDesarrollo
}
