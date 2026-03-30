import os
import re
import google.generativeai as genai
import json

# Configurar API Key
genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

class ServicioIA:
    def __init__(self):
        self.modelo = genai.GenerativeModel('gemini-2.5-flash')

    def generar_ejercicio(self, tema, nivel, tipo='opcion_multiple'):
        """
        Genera un ejercicio matematico basado en el tema y nivel.
        Retorna un diccionario con la estructura del ejercicio, incluyendo
        pasos detallados de solucion.
        """
        prompt = f"""
        Actua como un profesor de matematicas experto. Genera UN ejercicio de {tema} para nivel {nivel}.
        El tipo de pregunta debe ser: {tipo}.

        Si es 'opcion_multiple', responde SOLAMENTE con un JSON con esta estructura:
        {{
            "enunciado": "La pregunta aqui (usa LaTeX para formulas entre \\( \\))",
            "opciones": {{
                "a": "opcion 1",
                "b": "opcion 2",
                "c": "opcion 3",
                "d": "opcion 4"
            }},
            "respuesta_correcta": "letra de la correcta (a, b, c, o d)",
            "explicacion": "Breve explicacion de la solucion",
            "pasos": [
                "Paso 1: Descripcion detallada del primer paso",
                "Paso 2: Descripcion detallada del segundo paso",
                "Paso 3: Descripcion detallada del tercer paso"
            ]
        }}

        Si es 'verdadero_falso', responde JSON:
        {{
            "enunciado": "Afirmacion matematica",
            "respuesta_correcta": "Verdadero o Falso",
            "explicacion": "Por que es V o F",
            "pasos": [
                "Paso 1: Analisis de la afirmacion",
                "Paso 2: Justificacion"
            ]
        }}

        Si es 'numerico', responde JSON:
        {{
            "enunciado": "Pregunta de calculo",
            "respuesta_correcta": "valor numerico o expresion simple",
            "explicacion": "Pasos clave",
            "pasos": [
                "Paso 1: Identificar datos del problema",
                "Paso 2: Plantear la operacion",
                "Paso 3: Resolver paso a paso",
                "Paso 4: Verificar el resultado"
            ]
        }}

        REGLAS para el campo "pasos":
        - Cada paso debe ser claro, detallado y didactico.
        - Usa LaTeX entre \\( \\) para formulas matematicas dentro de los pasos.
        - Los pasos deben guiar al estudiante desde el planteamiento hasta la solucion final.
        - Incluye entre 3 y 6 pasos segun la complejidad del ejercicio.

        IMPORTANTE: Responde UNICAMENTE con el JSON valido, sin texto adicional ni formato markdown.
        """

        try:
            respuesta = self.modelo.generate_content(prompt)
            texto = respuesta.text
            # Limpiar posible formato markdown
            texto = texto.replace('```json', '').replace('```', '').strip()
            # Arreglar backslashes de LaTeX que rompen JSON
            texto = self._limpiar_json(texto)
            resultado = json.loads(texto)
            # Asegurar que siempre tenga el campo pasos
            if 'pasos' not in resultado:
                resultado['pasos'] = []
            return resultado
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON de IA: {e}")
            print(f"Texto recibido: {respuesta.text if 'respuesta' in dir() else 'N/A'}")
            # Intento de recuperacion: extraer JSON con regex
            try:
                match = re.search(r'\{[\s\S]*\}', respuesta.text)
                if match:
                    texto2 = self._limpiar_json(match.group(0))
                    resultado = json.loads(texto2)
                    resultado.setdefault('pasos', [])
                    return resultado
            except Exception:
                pass
            return {"error": f"La IA no devolvio un JSON valido. Intentalo de nuevo."}
        except Exception as e:
            print(f"Error generando ejercicio: {e}")
            return {"error": str(e)}

    def _limpiar_json(self, texto):
        """
        Arregla backslashes invalidos en JSON que vienen de LaTeX.
        Ej: \\( \\frac \\sqrt se convierten en \\\\( \\\\frac \\\\sqrt
        """
        # Reemplazar backslashes que NO son escapes JSON validos
        # Escapes JSON validos: \" \\ \/ \b \f \n \r \t \uXXXX
        texto = re.sub(
            r'\\(?!["\\/bfnrtu])',
            r'\\\\',
            texto
        )
        return texto

    def generar_explicacion_ejercicio(self, enunciado, respuesta_correcta, respuesta_usuario):
        """
        Genera una explicacion paso a paso de como resolver un ejercicio.
        Util cuando el estudiante falla y quiere ver el procedimiento.
        """
        prompt = f"""
        Eres un tutor de matematicas paciente y didactico.
        Un estudiante respondio incorrectamente un ejercicio. Genera una explicacion
        paso a paso de como resolverlo correctamente.

        Ejercicio: {enunciado}
        Respuesta correcta: {respuesta_correcta}
        Respuesta del estudiante: {respuesta_usuario}

        Responde UNICAMENTE con un JSON valido con esta estructura:
        {{
            "explicacion_breve": "Resumen corto de por que la respuesta es incorrecta",
            "pasos": [
                "Paso 1: ...",
                "Paso 2: ...",
                "Paso 3: ..."
            ],
            "consejo": "Un consejo o tip para el estudiante"
        }}

        Usa LaTeX entre \\( \\) para formulas matematicas.
        IMPORTANTE: Responde UNICAMENTE con el JSON valido, sin texto adicional.
        """

        try:
            respuesta = self.modelo.generate_content(prompt)
            texto = respuesta.text.replace('```json', '').replace('```', '').strip()
            texto = self._limpiar_json(texto)
            return json.loads(texto)
        except Exception as e:
            print(f"Error generando explicacion: {e}")
            return {
                "explicacion_breve": "No se pudo generar la explicacion automatica.",
                "pasos": [f"La respuesta correcta es: {respuesta_correcta}"],
                "consejo": "Revisa la teoria de la leccion e intentalo de nuevo."
            }

    def chat_educativo(self, mensaje, contexto_leccion=""):
        """
        Responde dudas del estudiante en el contexto de una leccion.
        """
        prompt = f"""
        Eres un tutor de matematicas amable y paciente llamado 'MathBot'.
        El estudiante esta en una leccion sobre: {contexto_leccion}.
        Pregunta del estudiante: "{mensaje}"

        Instrucciones:
        1. Responde de forma concisa y didactica.
        2. Usa LaTeX para formulas matematicas (entre \\( \\)).
        3. No des la respuesta directa a ejercicios, guia al estudiante.
        4. Si te preguntan algo fuera de matematicas, responde cortesmente que solo sabes de mates.
        """

        try:
            respuesta = self.modelo.generate_content(prompt)
            return respuesta.text
        except Exception as e:
            return "Lo siento, tuve un problema pensando la respuesta. Intentalo de nuevo."
