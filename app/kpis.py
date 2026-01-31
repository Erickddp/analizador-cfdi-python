"""Cálculo de indicadores clave de desempeño (KPIs) a partir de CFDI."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import List, Dict, Tuple

import pandas as pd

from .models import CFDI
from .utils import month_key


def compute_kpis(
    cfdis: List[CFDI],
    invalid_count: int = 0,
    duplicates_count: int = 0,
    cfdi33_count: int = 0,
) -> Dict[str, object]:
    """Calcula KPIs generales y agrupados a partir de una lista de CFDI.

    Devuelve un diccionario con los siguientes elementos:
        total_ingresos, total_egresos, neto,
        iva_trasladado, isr_retenido, iva_retenido, ieps,
        conteo_cfdi,
        ingresos_por_mes (dict YYYY-MM -> total),
        egresos_por_mes (dict YYYY-MM -> total),
        top_clientes (lista de tuplas (RFC, total)),
        top_proveedores (lista de tuplas (RFC, total)),
        calidad (dict con invalidos, duplicados, cfdi33).
    """
    total_ingresos = 0.0
    total_egresos = 0.0
    total_iva_trasladado = 0.0
    total_isr_retenido = 0.0
    total_iva_retenido = 0.0
    total_ieps = 0.0
    
    # Contadores para CFDI clasificados
    count_ingresos = 0
    count_egresos = 0

    ingresos_por_mes: Dict[str, float] = defaultdict(float)
    egresos_por_mes: Dict[str, float] = defaultdict(float)
    clientes_counter: Dict[str, float] = defaultdict(float)
    proveedores_counter: Dict[str, float] = defaultdict(float)

    for c in cfdis:
        clasif = c.clasificacion
        month = month_key(c.fecha)
        if clasif == "Ingresos":
            total_ingresos += c.total
            count_ingresos += 1
            ingresos_por_mes[month] += c.total
            # clientes: emisor (error en original: clientes son receptores de MIS ingresos, pero el emisor soy YO.
            # Espera, si es Ingreso: Emisor=YO, Receptor=Cliente.
            # El código original usaba c.emisor_rfc para "clientes". Eso estaba mal si clasificaba al revés.
            # Con mi corrección en classifier: Ingreso -> Yo soy Emisor. El Receptor es mi Cliente.
            # Así que debo sumar a c.receptor_rfc. 
            # PERO, el código original decía # clientes: emisor.
            # Si mantengo la lógica de "top_clientes" como "a quién le vendo", debo usar Receptor.
            # Voy a corregirlo para ser consistente: Clientes = Receptores de mis Ingresos.
            clientes_counter[c.receptor_rfc] += c.total
        elif clasif == "Egresos":
            total_egresos += c.total
            count_egresos += 1
            egresos_por_mes[month] += c.total
            # proveedores: emisor (Yo soy Receptor, Emisor es Proveedor). Correcto.
            proveedores_counter[c.emisor_rfc] += c.total

        # Acumular impuestos globales
        total_iva_trasladado += c.iva_trasladado
        total_isr_retenido += c.isr_retenido
        total_iva_retenido += c.iva_retenido
        total_ieps += c.ieps

    neto = total_ingresos - total_egresos
    conteo = count_ingresos + count_egresos

    # Top 5 clientes y proveedores
    top_clientes = sorted(clientes_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    top_proveedores = sorted(proveedores_counter.items(), key=lambda x: x[1], reverse=True)[:5]

    kpis = {
        "total_ingresos": total_ingresos,
        "total_egresos": total_egresos,
        "neto": neto,
        "iva_trasladado": total_iva_trasladado,
        "isr_retenido": total_isr_retenido,
        "iva_retenido": total_iva_retenido,
        "ieps": total_ieps,
        "conteo_cfdi": conteo,
        "ingresos_por_mes": dict(ingresos_por_mes),
        "egresos_por_mes": dict(egresos_por_mes),
        "top_clientes": top_clientes,
        "top_proveedores": top_proveedores,
        "calidad": {
            "invalidos": invalid_count,
            "duplicados": duplicates_count,
            "cfdi33": cfdi33_count,
        },
    }
    return kpis


def cfdis_to_dataframe(cfdis: List[CFDI]) -> pd.DataFrame:
    """Convierte una lista de CFDI a un DataFrame de pandas.

    Las columnas corresponden a los campos relevantes para su presentación en
    tablas y exportaciones. Se formatea la fecha como cadena ISO.
    """
    records = []
    for c in cfdis:
        records.append({
            "UUID": c.uuid,
            "Fecha": c.fecha.strftime("%Y-%m-%d") if c.fecha else "",
            "Tipo": c.tipo,
            "Serie": c.serie,
            "Folio": c.folio,
            "Emisor RFC": c.emisor_rfc,
            "Emisor Nombre": c.emisor_nombre,
            "Emisor Régimen": c.emisor_regimen,
            "Receptor RFC": c.receptor_rfc,
            "Receptor Nombre": c.receptor_nombre,
            "Receptor Régimen": c.receptor_regimen,
            "Uso CFDI": c.uso_cfdi,
            "SubTotal": c.subtotal,
            "Descuento": c.descuento,
            "Total": c.total,
            "Moneda": c.moneda,
            "Tipo Cambio": c.tipo_cambio,
            "Forma Pago": c.forma_pago,
            "Método Pago": c.metodo_pago,
            "Lugar Expedición": c.lugar_expedicion,
            "IVA Trasladado": c.iva_trasladado,
            "ISR Retenido": c.isr_retenido,
            "IVA Retenido": c.iva_retenido,
            "IEPS": c.ieps,
            "Número Conceptos": c.num_conceptos,
            "Versión": c.version,
            "Advertencias": " | ".join(c.warnings),
            "Clasificación": c.clasificacion,
        })
    df = pd.DataFrame.from_records(records)
    return df