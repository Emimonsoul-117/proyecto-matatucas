# Elevar Matatucas al Siguiente Nivel

Plan integral para corregir problemas existentes y añadir funcionalidades clave que transformen la plataforma.

---

## 1. Corrección de Etiquetas Incoherentes / Textos "Cringe"

Hay textos en la UI que usan jerga técnica forzada, no describen la acción real o son confusos para el usuario final. Propongo renombrar todo a lenguaje claro y profesional.

### Archivos afectados

#### [MODIFY] [nueva_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/nueva_leccion.html)

| Texto actual (incoherente) | Texto propuesto (claro) |
|---|---|
| `Creador Estructural` | `Nueva Lección` |
| `Arsenal de Contenido` | `Agregar Contenido` |
| `Teoría Docente` | `📝 Texto / Teoría` |
| `Nodo Audiovisual` / `Nodo Audiovisual Externo` | `🎬 Video de YouTube` |
| `Reactivo con IA Neuronal` | `✏️ Ejercicio / Pregunta` |
| `Archivo Anexo` | `📎 Recurso / Enlace` |
| `Lienzo Operativo Despejado` | `Sin contenido aún` |
| `Usa el Arsenal de Contenido a tu izquierda para inyectar bloques sin tener que desplazar la pantalla` | `Usa los botones de la izquierda para agregar secciones de contenido a tu lección.` |
| `Cerrar / Abortar` | `Volver al curso` |
| `Lienzo de Redacción Teórica` | `Texto / Teoría` |
| `Validación Neuronal / Examen` | `Ejercicio` |
| `Repositorio de Archivos` | `Recurso adjunto` |
| `Subir Prioridad` / `Bajar Prioridad` | `Mover arriba` / `Mover abajo` |
| `Destruir Nodo` | `Eliminar sección` |
| `Asistente Neuronal` | `Generador con IA` |
| `Creación automática de evaluación algorítmica` | `Genera un ejercicio automáticamente usando Gemini` |
| `Auto-Generar Evaluación` | `Generar con IA` |
| `Extrayendo métricas del curso y forjando reactivo con IA Gemini...` | `Generando ejercicio con IA...` |
| `¿Emitir orden a la Red Neuronal para autogenerar evaluación de "..." en ...?` | `¿Generar ejercicio de "..." con IA?` |
| `Cuerpo del Problema` | `Enunciado de la pregunta` |
| `Modo de Captura` | `Tipo de pregunta` |
| `Decisión Múltiple Clásica` | `Opción múltiple` |
| `Contraste Binario (Verdadero/Falso)` | `Verdadero / Falso` |
| `Digitación de Valor Seco` | `Respuesta numérica` |
| `Llave de Validación Correcta` | `Respuesta correcta` |
| `Distractor A/B/C/D` | `Opción A/B/C/D` |
| `Enlace Público de YouTube` | `URL del video` |
| `Requisito estricto: El estudiante debe consumirlo para avanzar` | `El alumno debe ver este video para avanzar en la lección` |
| `Plasma el fundamento de tu conocimiento aquí...` (placeholder Quill) | `Escribe el contenido teórico aquí...` |
| `Redacta el cuestionamiento definitivo...` (placeholder pregunta) | `Escribe el enunciado del ejercicio...` |
| `Alias del Documento` | `Nombre del recurso` |
| `Enlace Público de Alojamiento` | `URL del recurso` |
| `Resolución Sistematizada por IA` | `Solución paso a paso (generada por IA)` |
| `Carga Completada. Reactivo Operativo.` | `✅ Ejercicio generado correctamente` |
| `Precaución Crítica:` (alert error) | `Error:` |
| `Latencia en Motor Neuronal` (error fallback) | `Error al generar el ejercicio` |
| `Edición de Módulo` (breadcrumb) | `Nueva Lección` |
| `Guardar Lección ☁️` | `💾 Guardar Lección` |

#### [MODIFY] [editar_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/editar_leccion.html)
- Mismas correcciones que `nueva_leccion.html` (comparten el mismo patrón de etiquetas).

#### [MODIFY] [ver.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/ver.html)

| Texto actual | Texto propuesto |
|---|---|
| `Plan de Estudios` | `Información del Curso` |
| `Visualización General del Estudiante` (badge) | `Vista general` |
| `Matricularme Ahora Mismo` | `Inscribirme al curso` |
| `Imprimir Certificado Oficial` | `Descargar Certificado` |
| `Ficha Técnica` | `Detalles del Curso` |
| `Complejidad` | `Nivel` |
| `Volumen` → `X Capítulos` | `Lecciones` → `X lecciones` |
| `Alcance` → `X Alumnos` | `Alumnos inscritos` |

#### [MODIFY] [lista.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/lista.html)

| Texto actual | Texto propuesto |
|---|---|
| `Academia Matatucas` | `Matatucas` |
| `Materias` (stats) | `Cursos` |

#### [MODIFY] [chatbot.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/componentes/chatbot.html)

| Texto actual | Texto propuesto |
|---|---|
| `Thinking...` | `Pensando...` |
| `Error de conexión.` | `Error de conexión. Inténtalo de nuevo.` |

#### [MODIFY] [nuevo_ejercicio.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/nuevo_ejercicio.html)

| Texto actual | Texto propuesto |
|---|---|
| `Pensando un ejercicio matemático con Gemini 2.5 Flash...` | `Generando ejercicio con IA...` |

---

## 2. Administradores Ven Solo Sus Propios Cursos

> [!IMPORTANT]
> Actualmente en [docente/rutas.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/docente/rutas.py) línea 27-28, si el usuario es administrador, se muestran **TODOS** los cursos de la plataforma. El admin debe ver solo los cursos que él mismo creó.

### Cambio propuesto

#### [MODIFY] [rutas.py (docente)](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/docente/rutas.py)
- Línea 27-28: Eliminar la condición especial para administrador. Tanto docentes como admins verán solo `Curso.query.filter_by(id_docente=current_user.id)`.

#### [MODIFY] [rutas.py (cursos)](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/cursos/rutas.py)
- En `lista_cursos()` (línea 107-143): Los administradores actualmente ven todos los cursos sin filtrar. Agregaremos el mismo filtro que los docentes para que solo vean sus propios cursos + los cursos globales publicados.

---

## 3. Vista Previa "Como Alumno" para Docentes

> [!IMPORTANT]
> Los docentes necesitan ver cómo lucirá un curso desde la perspectiva del estudiante antes de publicarlo.

### Cambio propuesto

#### [NEW] Ruta `/cursos/<id>/vista-alumno`
- En [rutas.py (cursos)](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/cursos/rutas.py): Nueva ruta `vista_alumno(id)` que renderiza la misma vista `ver.html` pero con una variable `modo_preview=True` y simula `rol='estudiante'` en el template.
- El docente verá el curso exactamente como lo ve un alumno: sidebar con lecciones, botón de inscripción, ficha técnica, etc.
- Sin botones de gestión docente (editar, eliminar, publicar).

#### [MODIFY] [ver.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/ver.html)
- Agregar botón "👁 Vista Alumno" en los comandos de docente.
- Agregar lógica condicional que oculte controles de docente cuando `modo_preview=True`.
- Agregar banner superior indicando "Estás viendo esto como alumno" con botón de "Volver a Vista Docente".

---

## 4. Mejora de IA Generativa

El servicio de IA actual ([ia_servicio.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/servicios/ia_servicio.py)) solo genera 3 tipos de ejercicios y tiene prompts limitados. Propongo:

### Cambios propuestos

#### [MODIFY] [ia_servicio.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/servicios/ia_servicio.py)
- **Nuevo método: `generar_teoria(tema, nivel)`** → Genera contenido teórico en HTML a partir de un tema y nivel. El docente presiona un botón y la IA genera una sección de teoría completa.
- **Nuevo método: `generar_leccion_completa(tema, nivel)`** → Genera una lección con teoría + ejercicios variados en un solo paso.
- **Mejorar prompts existentes**: Hacer los prompts más robustos con instrucciones de idioma español y formato consistente.
- **Manejo de errores mejorado**: Reintentos automáticos, mensajes de error claros al usuario.

#### [MODIFY] [rutas.py (cursos)](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/cursos/rutas.py)
- Nuevo endpoint `api_generar_teoria` (POST).
- Nuevo endpoint `api_generar_leccion_completa` (POST).

#### [MODIFY] [nueva_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/nueva_leccion.html) + [editar_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/editar_leccion.html)
- Botón "✨ Generar teoría con IA" dentro de la sección de teoría.
- Botón global "🪄 Generar lección completa con IA" que genera automáticamente teoría + ejercicios variados.

---

## 5. Nuevos Tipos de Ejercicios y Evaluaciones

> [!IMPORTANT]
> Actualmente solo hay 3 tipos: `opcion_multiple`, `verdadero_falso`, `numerico`. Es limitado para una plataforma educativa seria.

### Nuevos tipos propuestos

| Tipo | Nombre visible | Descripción |
|---|---|---|
| `completar_texto` | Completar el texto | El alumno llena espacios en blanco ("fill the blanks") |
| `ordenar_pasos` | Ordenar pasos | El alumno arrastra y ordena pasos en la secuencia correcta |
| `respuesta_corta` | Respuesta corta | El alumno escribe una respuesta de texto libre (calificada por coincidencia flexible) |

### Archivos afectados

#### [MODIFY] [modelos.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/modelos.py)
- Ampliar el Enum de `Ejercicio.tipo` para incluir los nuevos tipos: `'opcion_multiple', 'verdadero_falso', 'numerico', 'completar_texto', 'ordenar_pasos', 'respuesta_corta'`.

#### [MODIFY] [__init__.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/__init__.py)
- Agregar migración automática para ampliar el ENUM en la BD existente.

#### [MODIFY] [nueva_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/nueva_leccion.html) + [editar_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/editar_leccion.html)
- Agregar las nuevas opciones en el select de tipo de pregunta.
- Renderizar campos específicos según tipo (editor de blanks, editor de pasos reordenables, campo de texto libre).

#### [MODIFY] [hacer_ejercicios.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/hacer_ejercicios.html)
- Renderizar cada nuevo tipo de ejercicio con UI interactiva apropiada:
  - **Completar texto**: Input inline dentro del enunciado.
  - **Ordenar pasos**: Drag-and-drop de tarjetas.
  - **Respuesta corta**: Textarea.

#### [MODIFY] [ver_leccion.html](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/templates/cursos/ver_leccion.html)
- Soportar renderizado inline de los nuevos tipos en la vista de lección.

#### [MODIFY] [rutas.py (cursos)](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/cursos/rutas.py)
- En `hacer_ejercicios()`: agregar lógica de calificación para los nuevos tipos.
- En `nueva_leccion()` / `editar_leccion()`: persistir los nuevos tipos correctamente.

#### [MODIFY] [ia_servicio.py](file:///home/emimonsoul/Descargas/proyecto%20matatucas/proyecto-matatucas-master/app/servicios/ia_servicio.py)
- Agregar soporte de generación IA para los nuevos tipos de ejercicio.

---

## Orden de Ejecución

1. ⬜ **Fase 1**: Corrección de etiquetas incoherentes (todas las templates)
2. ⬜ **Fase 2**: Admin ve solo sus cursos (backend)
3. ⬜ **Fase 3**: Vista previa "como alumno" (ruta + template)
4. ⬜ **Fase 4**: Nuevos tipos de ejercicios (modelo → migración → UI docente → UI alumno → calificación)
5. ⬜ **Fase 5**: Mejora de IA generativa (servicio → endpoints → botones en templates)

---

## Verificación

### Pruebas manuales
- Verificar que todas las etiquetas de la UI son claras y coherentes.
- Iniciar sesión como administrador y confirmar que solo ve sus propios cursos.
- Como docente, usar "Vista Alumno" y confirmar que se ocultan controles de gestión.
- Crear ejercicios de cada nuevo tipo y confirmar que se guardan y evalúan correctamente.
- Generar teoría y ejercicios con IA y confirmar respuestas válidas.

### Verificación de código
- Confirmar que la aplicación arranca sin errores (`python run.py`).
- Confirmar que la migración del ENUM funciona en BD existente.

---

## Open Questions

> [!NOTE]
> 1. **¿Quieres que los administradores tengan un botón adicional para ver "todos los cursos" del sistema?** O definitivamente solo ven los que ellos crearon. Actualmente propongo que solo vean los suyos.
> 2. **Para "completar texto" y "ordenar pasos"**: ¿Quieres que estos tipos se puedan generar también con IA? Propongo que sí.
> 3. **¿Hay algún texto adicional en la interfaz que consideres confuso y quieras mencionar?**
