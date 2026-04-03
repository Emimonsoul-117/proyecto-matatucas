from .. import bd
from ..modelos import RegistroAuditoria
from flask import request
from flask_login import current_user

def registrar_accion(accion, detalles=None):
    """
    Registra una acción en el log de auditoría.
    :param accion: String identificador de la acción (ej: 'ELIMINAR_CURSO')
    :param detalles: Diccionario con información adicional
    """
    if not current_user.is_authenticated:
        return # No registrar acciones de usuarios no logueados por ahora o manejar anónimo
        
    audit = RegistroAuditoria(
        id_usuario=current_user.id,
        accion=accion,
        detalles=detalles,
        ip_address=request.remote_addr
    )
    bd.session.add(audit)
    bd.session.commit()
