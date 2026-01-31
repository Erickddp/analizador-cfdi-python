"""Modelos de datos para representar CFDI y conceptos.

Se utilizan dataclasses simples para almacenar la información extraída de los
XML. Estas estructuras permiten pasar datos de forma tipada entre el parser,
el clasificador, las vistas y los exportadores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class Concepto:
    """Representa un concepto dentro de un CFDI."""
    uuid: str
    clave_prod_serv: str
    cantidad: float
    clave_unidad: str
    unidad: str
    descripcion: str
    valor_unitario: float
    importe: float
    descuento: float
    impuestos_traslado: Dict[str, float] = field(default_factory=dict)  # impuesto: importe
    impuestos_retencion: Dict[str, float] = field(default_factory=dict)  # impuesto: importe


@dataclass
class CFDI:
    """Representa los datos principales de un CFDI."""
    uuid: str
    fecha: Optional[datetime]
    tipo: str
    serie: str
    folio: str
    emisor_rfc: str
    emisor_nombre: str
    emisor_regimen: str
    receptor_rfc: str
    receptor_nombre: str
    receptor_regimen: str
    uso_cfdi: str
    subtotal: float
    descuento: float
    total: float
    moneda: str
    tipo_cambio: float
    forma_pago: str
    metodo_pago: str
    lugar_expedicion: str
    iva_trasladado: float
    isr_retenido: float
    iva_retenido: float
    ieps: float
    num_conceptos: int
    version: str
    warnings: List[str] = field(default_factory=list)
    clasificacion: str = "No clasificado"  # Se establece posteriormente