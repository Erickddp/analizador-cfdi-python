"""Generación de un reporte PDF de una sola hoja con KPIs y gráficas.

El reporte PDF se diseña en tamaño carta y alto contraste. Incluye un título,
KPIs destacados, gráficas generadas con matplotlib y tablas de los principales
clientes y proveedores. Para mantener la compatibilidad offline se utiliza
reportlab y matplotlib exclusivamente.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import List, Dict

import matplotlib

# Utilizar backend no interactivo para generar imágenes en memoria
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from .models import CFDI


def _create_chart_totales_mes(kpis: Dict[str, object]) -> bytes:
    """Genera una gráfica de barras de ingresos y egresos por mes y devuelve bytes de PNG."""
    meses = sorted(set(list(kpis["ingresos_por_mes"].keys()) + list(kpis["egresos_por_mes"].keys())))
    ingresos = [kpis["ingresos_por_mes"].get(m, 0.0) for m in meses]
    egresos = [kpis["egresos_por_mes"].get(m, 0.0) for m in meses]
    fig, ax = plt.subplots(figsize=(6, 3))
    x = range(len(meses))
    ax.bar([i - 0.2 for i in x], ingresos, width=0.4, label="Ingresos", color="#4CAF50")
    ax.bar([i + 0.2 for i in x], egresos, width=0.4, label="Egresos", color="#F44336")
    ax.set_xticks(list(x))
    ax.set_xticklabels(meses, rotation=45, ha='right')
    ax.set_title("Totales por mes")
    ax.set_ylabel("Monto")
    ax.legend(loc="upper right")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()


def _create_chart_top_list(top_list: List[tuple], title: str) -> bytes:
    """Genera una gráfica de barras horizontal para top clientes/proveedores."""
    if not top_list:
        return b""
    rfc = [r[0] for r in top_list]
    total = [r[1] for r in top_list]
    fig, ax = plt.subplots(figsize=(4, 2.5))
    y_pos = range(len(rfc))
    ax.barh(y_pos, total, color="#2196F3")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(rfc)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel("Monto")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()


def generate_report(
    filename: str,
    cfdis: List[CFDI],
    kpis: Dict[str, object],
    user_rfc: str,
) -> None:
    """Genera un reporte PDF de una sola hoja tipo dashboard."""
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements: List[object] = []

    # 1. Encabezado
    title_style = ParagraphStyle(name="Title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=20, spaceAfter=10)
    subtitle_style = ParagraphStyle(name="Subtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12, textColor=colors.gray)
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph("Reporte Financiero CFDI", title_style))
    elements.append(Paragraph(f"RFC: {user_rfc} | Generado: {now}", subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))

    # 2. Tarjetas de KPIs (Grid de 2 filas x 4 columnas)
    # Fila 1: Ingresos, Egresos, Neto
    # Fila 2: Impuestos y Conteo
    
    def format_money(val):
        return f"${val:,.2f}"

    total_ing = kpis.get('total_ingresos', 0)
    total_egr = kpis.get('total_egresos', 0)
    neto = kpis.get('neto', 0)
    conteo = kpis.get('conteo_cfdi', 0)
    
    # Estilo de tarjeta
    card_style = TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke), # Header row background
        ('TEXTCOLOR', (0,1), (-1,1), colors.black),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,1), 12),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ])

    # Primera Fila de Tarjetas
    data_row1 = [
        ["Total Ingresos", "Total Egresos", "Neto (I-E)", "CFDIs Clasificados"],
        [format_money(total_ing), format_money(total_egr), format_money(neto), str(conteo)]
    ]
    t1 = Table(data_row1, colWidths=[1.8*inch]*4)
    t1.setStyle(card_style)
    # Colorear textos clave
    t1.setStyle(TableStyle([
        ('TEXTCOLOR', (0,1), (0,1), colors.green),
        ('TEXTCOLOR', (1,1), (1,1), colors.red),
        ('TEXTCOLOR', (2,1), (2,1), colors.blue),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 0.1 * inch))

    # Segunda Fila de Tarjetas (Impuestos)
    iva_t = kpis.get('iva_trasladado', 0)
    isr_r = kpis.get('isr_retenido', 0)
    iva_r = kpis.get('iva_retenido', 0)
    
    data_row2 = [
        ["IVA Trasladado", "ISR Retenido", "IVA Retenido", "IEPS"],
        [format_money(iva_t), format_money(isr_r), format_money(iva_r), format_money(kpis.get('ieps', 0))]
    ]
    t2 = Table(data_row2, colWidths=[1.8*inch]*4)
    t2.setStyle(card_style)
    elements.append(t2)
    elements.append(Spacer(1, 0.4 * inch))

    # 3. Gráficas (Lado a Lado)
    # Generar imágenes
    chart_mes_bytes = _create_chart_totales_mes(kpis)
    
    # Top Clientes (o Proveedores si es mayor)
    top_clients = kpis.get("top_clientes", [])
    # Preferimos mostrar Top Clientes por defecto, o split
    chart_top_bytes = _create_chart_top_list(top_clients, "Top 5 Clientes")
    
    imgs_row = []
    if chart_mes_bytes:
        img1 = Image(io.BytesIO(chart_mes_bytes), width=3.5*inch, height=2.5*inch)
        imgs_row.append(img1)
    
    if chart_top_bytes:
        img2 = Image(io.BytesIO(chart_top_bytes), width=3.5*inch, height=2.5*inch)
        imgs_row.append(img2)
    
    if imgs_row:
        t_charts = Table([imgs_row], colWidths=[3.8*inch]*len(imgs_row))
        t_charts.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t_charts)
    
    elements.append(Spacer(1, 0.3 * inch))

    # 4. Calidad de Datos (Footer discreto)
    calidad = kpis.get("calidad", {})
    inv = calidad.get("invalidos", 0)
    dup = calidad.get("duplicados", 0)
    c33 = calidad.get("cfdi33", 0)
    
    footer_text = f"Control de Calidad: {inv} archivos inválidos | {dup} duplicados omitidos | {c33} CFDI Versión 3.3"
    elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9, textColor=colors.darkgray)))

    # Construir PDF
    doc.build(elements)