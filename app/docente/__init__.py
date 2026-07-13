from flask import Blueprint

docente = Blueprint('docente', __name__)

from . import rutas
