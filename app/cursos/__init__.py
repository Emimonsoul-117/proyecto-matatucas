from flask import Blueprint

cursos = Blueprint('cursos', __name__)

from . import rutas
