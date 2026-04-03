import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from io import BytesIO

def generar_reporte_docente_pdf(docente_nombre, cursos_data):
    """
    Genera un PDF profesional con el desempeño del docente.
    :param docente_nombre: Nombre del docente
    :param cursos_data: Lista de diccionarios [{'titulo', 'estudiantes', 'progreso_promedio'}]
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Encabezado
    elements.append(Paragraph(f"Reporte de Desempeño Docente - Matatucas Pro", title_style))
    elements.append(Paragraph(f"Docente: {docente_nombre}", styles['Heading2']))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Tabla de Cursos
    data = [["Curso", "Estudiantes Inscritos", "Progreso Promedio (%)"]]
    for c in cursos_data:
        data.append([c['titulo'], str(c['estudiantes']), f"{c['progreso_promedio']}%"])
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Este documento es generado automáticamente por el sistema de Gestión Académica Matatucas Pro.", styles['Italic']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
