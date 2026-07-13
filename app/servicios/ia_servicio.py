import os
import re
import time
import google.generativeai as genai
import json

genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

MAX_REINTENTOS = 3


class ServicioIA:
    def __init__(self):
        pass

    def _llamar_modelo(self, prompt):
        ultimo_error = None
        modelos_a_probar = ['gemini-2.5-flash', 'gemini-1.5-flash']
        
        for modelo_nombre in modelos_a_probar:
            modelo = genai.GenerativeModel(modelo_nombre)
            for intento in range(1, MAX_REINTENTOS + 1):
                try:
                    respuesta = modelo.generate_content(prompt)
                    return respuesta.text
                except Exception as exc:
                    ultimo_error = exc
                    print(f'Intento {intento}/{MAX_REINTENTOS} con {modelo_nombre} fallido: {exc}')
                    # Si el error es sobre modelo no encontrado o no autorizado, cambiamos de modelo de inmediato
                    exc_str = str(exc).lower()
                    if 'not found' in exc_str or '404' in exc_str or 'invalid' in exc_str or 'model' in exc_str:
                        break
                    if intento < MAX_REINTENTOS:
                        time.sleep(1.5 * intento)
            print(f'Todos los intentos con {modelo_nombre} fallaron. Probando siguiente modelo de respaldo...')
            
        raise ultimo_error

    def _parsear_json(self, texto):
        texto = texto.replace('```json', '').replace('```', '').strip()
        texto = self._limpiar_json(texto)
        return json.loads(texto)

    def _limpiar_json(self, texto):
        texto = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', texto)
        return texto

    def _extraer_json(self, texto):
        try:
            return self._parsear_json(texto)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', texto)
            if match:
                return self._parsear_json(match.group(0))
            raise

    def generar_ejercicio(self, tema, nivel, tipo='opcion_multiple'):
        """Genera un ejercicio según el tipo solicitado."""
        prompts_tipo = {
            'opcion_multiple': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "La pregunta (usa LaTeX entre \\( \\) para fórmulas)",
            "opciones": {"a": "...", "b": "...", "c": "...", "d": "..."},
            "respuesta_correcta": "letra correcta (a, b, c o d)",
            "explicacion": "Breve explicación",
            "pasos": ["Paso 1: ...", "Paso 2: ..."]
        }""",
            'verdadero_falso': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "Afirmación matemática clara",
            "respuesta_correcta": "Verdadero o Falso",
            "explicacion": "Por qué es V o F",
            "pasos": ["Paso 1: ...", "Paso 2: ..."]
        }""",
            'numerico': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "Pregunta de cálculo",
            "respuesta_correcta": "valor numérico",
            "explicacion": "Pasos clave",
            "pasos": ["Paso 1: ...", "Paso 2: ...", "Paso 3: ..."]
        }""",
            'completar_texto': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "Oración con espacios en corchetes, ej: 'El resultado de 2+3 es [5]'",
            "respuesta_correcta": "valores separados por | si hay varios espacios, ej: '5' o '5|10'",
            "explicacion": "Breve explicación",
            "pasos": ["Paso 1: ...", "Paso 2: ..."]
        }
        Usa corchetes [respuesta] en el enunciado para cada espacio en blanco.""",
            'ordenar_pasos': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "Ordena los siguientes pasos para resolver el problema:",
            "opciones": {"a": "primer paso", "b": "segundo paso", "c": "tercer paso", "d": "cuarto paso"},
            "respuesta_correcta": "a,b,c,d",
            "explicacion": "Por qué ese orden es correcto",
            "pasos": ["Paso 1: ...", "Paso 2: ..."]
        }
        Los pasos en opciones deben estar en el orden correcto (a→b→c→d).""",
            'respuesta_corta': """
        Responde SOLAMENTE con un JSON:
        {
            "enunciado": "Pregunta que requiere respuesta breve de texto",
            "respuesta_correcta": "respuesta esperada;alternativa aceptable",
            "explicacion": "Breve explicación",
            "pasos": ["Paso 1: ...", "Paso 2: ..."]
        }
        Si hay varias respuestas válidas, sepáralas con punto y coma (;).""",
        }

        instruccion_tipo = prompts_tipo.get(tipo, prompts_tipo['opcion_multiple'])
        prompt = f"""
        Actúa como un profesor de matemáticas experto. Genera UN ejercicio sobre "{tema}" para nivel {nivel}.
        El tipo de pregunta debe ser: {tipo}.
        Escribe TODO en español claro y didáctico.

        {instruccion_tipo}

        REGLAS para "pasos":
        - Entre 3 y 6 pasos didácticos.
        - Usa LaTeX entre \\( \\) para fórmulas.
        IMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin markdown ni texto adicional.
        """

        try:
            texto = self._llamar_modelo(prompt)
            resultado = self._extraer_json(texto)
            resultado.setdefault('pasos', [])
            return resultado
        except json.JSONDecodeError as exc:
            print(f'Error parseando JSON de IA: {exc}')
            return {'error': 'La IA no devolvió un JSON válido. Inténtalo de nuevo.'}
        except Exception as exc:
            print(f'Error generando ejercicio: {exc}')
            return {'error': 'Error al generar el ejercicio. Inténtalo de nuevo.'}

    def generar_teoria(self, tema, nivel):
        """Genera contenido teórico en HTML para una lección."""
        prompt = f"""
        Actúa como un profesor de matemáticas experto. Genera contenido teórico educativo
        sobre "{tema}" para estudiantes de nivel {nivel}.

        Responde ÚNICAMENTE con un JSON válido:
        {{
            "teoria": "<contenido HTML con párrafos, listas, negritas y fórmulas LaTeX entre \\( \\)>"
        }}

        Requisitos:
        - Todo en español claro y profesional.
        - Incluye definiciones, ejemplos y un resumen breve.
        - Usa etiquetas HTML: <p>, <h3>, <ul>, <li>, <strong>, <em>.
        - Entre 300 y 600 palabras.
        - Sin markdown, solo HTML dentro del campo "teoria".
        """

        try:
            texto = self._llamar_modelo(prompt)
            resultado = self._extraer_json(texto)
            if not resultado.get('teoria'):
                return {'error': 'La IA no generó contenido teórico válido.'}
            return resultado
        except Exception as exc:
            print(f'Error generando teoría: {exc}')
            return {'error': 'Error al generar la teoría. Inténtalo de nuevo.'}

    def generar_leccion_completa(self, tema, nivel):
        """Genera una lección con teoría y ejercicios variados."""
        prompt = f"""
        Actúa como un profesor de matemáticas experto. Genera una lección completa sobre "{tema}"
        para nivel {nivel}.

        Responde ÚNICAMENTE con un JSON válido:
        {{
            "secciones": [
                {{
                    "tipo": "teoria",
                    "contenido": "<HTML con teoría didáctica>"
                }},
                {{
                    "tipo": "ejercicio",
                    "pregunta": "enunciado del ejercicio",
                    "tipo_q": "opcion_multiple|verdadero_falso|numerico|completar_texto|ordenar_pasos|respuesta_corta",
                    "respuesta": "respuesta correcta",
                    "opciones": {{"a": "...", "b": "...", "c": "...", "d": "..."}}
                }}
            ]
        }}

        Requisitos:
        - Todo en español.
        - Incluye 1 sección de teoría y entre 2 y 4 ejercicios de tipos variados.
        - Para completar_texto usa corchetes [respuesta] en la pregunta.
        - Para ordenar_pasos incluye opciones a,b,c,d en orden correcto y respuesta "a,b,c,d".
        - Para respuesta_corta, respuesta puede tener alternativas separadas por ;.
        - opciones solo es necesario para opcion_multiple y ordenar_pasos.
        """

        try:
            texto = self._llamar_modelo(prompt)
            resultado = self._extraer_json(texto)
            secciones = resultado.get('secciones', [])
            if not secciones:
                return {'error': 'La IA no generó secciones válidas.'}
            return {'secciones': secciones}
        except Exception as exc:
            print(f'Error generando lección completa: {exc}')
            return {'error': 'Error al generar la lección. Inténtalo de nuevo.'}

    def generar_explicacion_ejercicio(self, enunciado, respuesta_correcta, respuesta_usuario):
        prompt = f"""
        Eres un tutor de matemáticas paciente y didáctico.
        Un estudiante respondió incorrectamente un ejercicio. Genera una explicación paso a paso.

        Ejercicio: {enunciado}
        Respuesta correcta: {respuesta_correcta}
        Respuesta del estudiante: {respuesta_usuario}

        Responde ÚNICAMENTE con JSON válido:
        {{
            "explicacion_breve": "Resumen corto de por qué la respuesta es incorrecta",
            "pasos": ["Paso 1: ...", "Paso 2: ..."],
            "consejo": "Un consejo para el estudiante"
        }}

        Usa LaTeX entre \\( \\) para fórmulas. Todo en español.
        """

        try:
            texto = self._llamar_modelo(prompt)
            return self._extraer_json(texto)
        except Exception as exc:
            print(f'Error generando explicación: {exc}')
            return {
                'explicacion_breve': 'No se pudo generar la explicación automática.',
                'pasos': [f'La respuesta correcta es: {respuesta_correcta}'],
                'consejo': 'Revisa la teoría de la lección e inténtalo de nuevo.',
            }

    def chat_educativo(self, mensaje, contexto_leccion=''):
        prompt = f"""
        Eres un tutor de matemáticas amable llamado 'MathBot'.
        El estudiante está en una lección sobre: {contexto_leccion}.
        Pregunta del estudiante: "{mensaje}"

        Instrucciones:
        1. Responde de forma concisa y didáctica en español.
        2. Usa LaTeX para fórmulas (entre \\( \\)).
        3. No des la respuesta directa a ejercicios, guía al estudiante.
        4. Si preguntan algo fuera de matemáticas, indica cortésmente que solo ayudas con mates.
        """

        try:
            return self._llamar_modelo(prompt)
        except Exception as exc:
            print(f'Error en chat educativo: {exc}')
            return 'Lo siento, tuve un problema al procesar tu pregunta. Inténtalo de nuevo.'
