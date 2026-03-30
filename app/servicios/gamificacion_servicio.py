from .. import bd
from ..modelos import Estudiante, Insignia, InsigniaEstudiante, Inscripcion, Ejercicio
from datetime import datetime, timedelta

class ServicioGamificacion:
    def otorgar_puntos(self, id_estudiante, cantidad, motivo=""):
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return None
        
        estudiante.puntos_totales += cantidad
        estudiante.monedas += cantidad  # Matacoins: se ganan junto con XP
        bd.session.commit()
        
        # Verificar insignias tras ganar puntos
        nuevas_insignias = self.verificar_insignias(estudiante)
        return {
            'nuevos_puntos': estudiante.puntos_totales,
            'nuevas_insignias': nuevas_insignias
        }

    def verificar_insignias(self, estudiante):
        """
        Verifica si el estudiante cumple condiciones para nuevas insignias.
        Retorna lista de nombres de insignias ganadas.
        """
        insignias_ganadas = []
        
        # Obtener todas las insignias posibles
        todas_insignias = Insignia.query.all()
        ids_ya_ganadas = [i.id_insignia for i in estudiante.logros]

        for insignia in todas_insignias:
            if insignia.id in ids_ya_ganadas:
                continue

            ganada = False
            
            # --- LÓGICA STRICTA Y VARIADA ---
            
            # 1. Rachas de Estudio (Consistencia)
            if insignia.criterio == 'racha_3':
                if estudiante.racha_dias >= 3: ganada = True
            elif insignia.criterio == 'racha_7':
                if estudiante.racha_dias >= 7: ganada = True
            elif insignia.criterio == 'racha_30':
                if estudiante.racha_dias >= 30: ganada = True
            
            # 2. Puntos (Acumulación)
            elif insignia.criterio == 'puntos_1000':
                if estudiante.puntos_totales >= 1000: ganada = True
            elif insignia.criterio == 'puntos_5000':
                if estudiante.puntos_totales >= 5000: ganada = True

            # 3. Exploración (Cursos inscritos)
            elif insignia.criterio == 'explorador':
                inscripciones = Inscripcion.query.filter_by(id_estudiante=estudiante.id_usuario).count()
                if inscripciones >= 3: ganada = True

            # 4. Excelencia (Cursos completados al 100%)
            elif insignia.criterio == 'maestro':
                completados = Inscripcion.query.filter_by(id_estudiante=estudiante.id_usuario, progreso=100.0).count()
                if completados >= 1: ganada = True

            # Guardar si se ganó
            if ganada:
                nuevo_logro = InsigniaEstudiante(id_estudiante=estudiante.id_usuario, id_insignia=insignia.id)
                bd.session.add(nuevo_logro)
                insignias_ganadas.append(insignia)
        
        if insignias_ganadas:
            bd.session.commit()
            
        return insignias_ganadas

    def actualizar_racha_login(self, id_estudiante):
        """Actualiza la racha de días de estudio al hacer login."""
        from datetime import date
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return
        
        hoy = date.today()
        
        if estudiante.ultimo_login:
            ultimo = estudiante.ultimo_login.date()
            diferencia = (hoy - ultimo).days
            
            if diferencia == 0:
                # Ya hizo login hoy, no cambiar racha
                return
            elif diferencia == 1:
                # Login consecutivo → incrementar racha
                estudiante.racha_dias += 1
            else:
                # Rompió la racha → reiniciar
                estudiante.racha_dias = 1
        else:
            # Primer login
            estudiante.racha_dias = 1
        
        estudiante.ultimo_login = datetime.utcnow()
        bd.session.commit()
        
        # Verificar insignias de racha
        self.verificar_insignias(estudiante)
