"""Clasifica CFDI en Ingresos, Egresos o No clasificado según el RFC del usuario."""
from __future__ import annotations

from .models import CFDI


def classify_cfdi(cfdi: CFDI, user_rfc: str) -> str:
    """Devuelve la clasificación del CFDI (Ingresos, Egresos o No clasificado).

    Reglas:
        - Ingresos: TipoComprobante "I" y RFC usuario == EMISOR.
        - Egresos: TipoComprobante "I" y RFC usuario == RECEPTOR.
        - Tipo "E" (Notas de crédito) y "P" (Pagos): "No clasificado" (por ahora).
    """
    if not cfdi or not user_rfc:
        return "No clasificado"
    
    rfc_user = user_rfc.strip().upper()
    emisor = (cfdi.emisor_rfc or "").strip().upper()
    receptor = (cfdi.receptor_rfc or "").strip().upper()
    tipo = (cfdi.tipo or "").upper()

    # Solo clasificamos Ingresos y Egresos reales (Facturas)
    if tipo == "I":
        if rfc_user == emisor:
            return "Ingresos"
        elif rfc_user == receptor:
            return "Egresos"
    
    # Notas de crédito (E), Pagos (P) y Nómina (N) u otros -> No clasificado
    return "No clasificado"