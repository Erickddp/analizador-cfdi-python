"""Generación de archivos Excel con pandas y xlsxwriter.

Este módulo crea un libro de Excel con las hojas Ingresos, Egresos, KPIs y
Conceptos. Cada hoja tiene un formato básico y columnas ajustadas. También se
agregan gráficas simples en la hoja de KPIs utilizando xlsxwriter.
"""
from __future__ import annotations

from typing import List, Dict
import pandas as pd

from .models import CFDI, Concepto
from .kpis import cfdis_to_dataframe


def export_to_excel(
    filename: str,
    cfdis: List[CFDI],
    concepts: List[Concepto],
    kpis: Dict[str, object],
) -> None:
    """Exporta los datos a un archivo XLSX con múltiples hojas.

    Args:
        filename: ruta completa donde se guardará el archivo XLSX.
        cfdis: lista de CFDI procesados.
        concepts: lista de conceptos asociados a los CFDI.
        kpis: diccionario de KPIs calculados.
    """
    df_all = cfdis_to_dataframe(cfdis)
    df_ingresos = df_all[df_all["Clasificación"] == "Ingresos"].copy()
    df_egresos = df_all[df_all["Clasificación"] == "Egresos"].copy()

    # Crear DataFrame de conceptos
    concept_records = []
    for c in concepts:
        # Sumar impuestos de traslado y retención por tipo
        iva_tr = c.impuestos_traslado.get("002", 0.0)
        ieps_tr = c.impuestos_traslado.get("003", 0.0)
        isr_rt = c.impuestos_retencion.get("001", 0.0)
        iva_rt = c.impuestos_retencion.get("002", 0.0)
        ieps_rt = c.impuestos_retencion.get("003", 0.0)
        concept_records.append({
            "UUID": c.uuid,
            "ClaveProdServ": c.clave_prod_serv,
            "Cantidad": c.cantidad,
            "ClaveUnidad": c.clave_unidad,
            "Unidad": c.unidad,
            "Descripción": c.descripcion,
            "ValorUnitario": c.valor_unitario,
            "Importe": c.importe,
            "Descuento": c.descuento,
            "IVA Trasladado": iva_tr,
            "IEPS Trasladado": ieps_tr,
            "ISR Retenido": isr_rt,
            "IVA Retenido": iva_rt,
            "IEPS Retenido": ieps_rt,
        })
    df_concepts = pd.DataFrame.from_records(concept_records)

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        workbook = writer.book
        # Formatos
        header_format = workbook.add_format({"bold": True, "bg_color": "#DDEBF7", "border": 1})
        money_format = workbook.add_format({"num_format": '#,##0.00'})

        # Ingresos
        df_ingresos.to_excel(writer, sheet_name="Ingresos", index=False)
        sheet = writer.sheets["Ingresos"]
        for col_num, value in enumerate(df_ingresos.columns.values):
            sheet.write(0, col_num, value, header_format)
            # Ajustar ancho
            width = max(len(str(value)), 12)
            sheet.set_column(col_num, col_num, width)

        # Egresos
        df_egresos.to_excel(writer, sheet_name="Egresos", index=False)
        sheet = writer.sheets["Egresos"]
        for col_num, value in enumerate(df_egresos.columns.values):
            sheet.write(0, col_num, value, header_format)
            width = max(len(str(value)), 12)
            sheet.set_column(col_num, col_num, width)

        # Conceptos - REMOVIDO por solicitud de usuario
        # (Se mantiene el código de generación del DF arriba por si se requiere en futuro,
        # pero ya no se escribe la hoja)
        # df_concepts.to_excel(writer, sheet_name="Conceptos", index=False)

        # KPIs
        kpi_sheet = workbook.add_worksheet("KPIs")
        row = 0
        # Resumen
        kpi_sheet.write(row, 0, "Indicador", header_format)
        kpi_sheet.write(row, 1, "Valor", header_format)
        row += 1
        kpi_sheet.write(row, 0, "Total Ingresos")
        kpi_sheet.write_number(row, 1, kpis["total_ingresos"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "Total Egresos")
        kpi_sheet.write_number(row, 1, kpis["total_egresos"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "Neto")
        kpi_sheet.write_number(row, 1, kpis["neto"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "IVA Trasladado")
        kpi_sheet.write_number(row, 1, kpis["iva_trasladado"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "ISR Retenido")
        kpi_sheet.write_number(row, 1, kpis["isr_retenido"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "IVA Retenido")
        kpi_sheet.write_number(row, 1, kpis["iva_retenido"], money_format)
        row += 1
        kpi_sheet.write(row, 0, "IEPS")
        kpi_sheet.write_number(row, 1, kpis["ieps"], money_format)
        row += 2
        # Calidad de datos
        kpi_sheet.write(row, 0, "Calidad de datos", header_format)
        row += 1
        for key, val in kpis["calidad"].items():
            kpi_sheet.write(row, 0, key.capitalize())
            kpi_sheet.write_number(row, 1, val)
            row += 1
        row += 1
        # Totales por mes - Ingresos y Egresos
        # Crear tablas simples
        kpi_sheet.write(row, 0, "Mes", header_format)
        kpi_sheet.write(row, 1, "Ingresos", header_format)
        kpi_sheet.write(row, 2, "Egresos", header_format)
        row += 1
        months = sorted(set(list(kpis["ingresos_por_mes"].keys()) + list(kpis["egresos_por_mes"].keys())))
        for m in months:
            kpi_sheet.write(row, 0, m)
            kpi_sheet.write_number(row, 1, kpis["ingresos_por_mes"].get(m, 0.0), money_format)
            kpi_sheet.write_number(row, 2, kpis["egresos_por_mes"].get(m, 0.0), money_format)
            row += 1
        # Gráfica de totales por mes
        chart1 = workbook.add_chart({"type": "column"})
        start_row = row - len(months)
        chart1.add_series({
            "name": "Ingresos",
            "categories": ["KPIs", start_row, 0, row - 1, 0],
            "values": ["KPIs", start_row, 1, row - 1, 1],
            "fill": {"color": "#4CAF50"},
        })
        chart1.add_series({
            "name": "Egresos",
            "categories": ["KPIs", start_row, 0, row - 1, 0],
            "values": ["KPIs", start_row, 2, row - 1, 2],
            "fill": {"color": "#F44336"},
        })
        chart1.set_title({"name": "Totales por mes"})
        chart1.set_x_axis({"name": "Mes"})
        chart1.set_y_axis({"name": "Monto"})
        chart1.set_legend({"position": "bottom"})
        # Insertar al lado derecho
        kpi_sheet.insert_chart(start_row - 1, 4, chart1, {"x_offset": 25, "y_offset": 10})
        row += 2
        # Top clientes y proveedores
        # Clientes
        kpi_sheet.write(row, 0, "Top 5 Clientes", header_format)
        row += 1
        kpi_sheet.write(row, 0, "RFC", header_format)
        kpi_sheet.write(row, 1, "Total", header_format)
        row += 1
        for rfc, total in kpis["top_clientes"]:
            kpi_sheet.write(row, 0, rfc)
            kpi_sheet.write_number(row, 1, total, money_format)
            row += 1
        row += 1
        # Proveedores
        kpi_sheet.write(row, 0, "Top 5 Proveedores", header_format)
        row += 1
        kpi_sheet.write(row, 0, "RFC", header_format)
        kpi_sheet.write(row, 1, "Total", header_format)
        row += 1
        for rfc, total in kpis["top_proveedores"]:
            kpi_sheet.write(row, 0, rfc)
            kpi_sheet.write_number(row, 1, total, money_format)
            row += 1