"""Parser de CFDI que extrae datos relevantes de un XML.

Este módulo utiliza lxml para analizar versiones 3.3 y 4.0 de CFDI. Se
ignoran los CFDI de tipo 'P' (Pagos). Los CFDI 3.3 se procesan pero se
marcan con una advertencia visible【760692873356022†L66-L83】.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List
from lxml import etree

from .models import CFDI, Concepto
from .utils import parse_iso_datetime


def _safe_float(value: Optional[str]) -> float:
    try:
        return float(value) if value is not None else 0.0
    except ValueError:
        return 0.0


def parse_cfdi(xml_path: str) -> Tuple[Optional[CFDI], List[Concepto]]:
    """Parsa un archivo XML de CFDI y devuelve los datos de CFDI y conceptos.

    Si el CFDI es inválido, no contiene UUID o es de tipo "P" (pagos),
    devuelve (None, []).
    """
    concepts: List[Concepto] = []
    try:
        parser = etree.XMLParser(huge_tree=True, resolve_entities=False)
        tree = etree.parse(str(xml_path), parser)
        root = tree.getroot()
    except Exception:
        # XML no válido
        return None, []

    # Determinar namespaces
    nsmap = {k if k else "cfdi": v for k, v in (root.nsmap or {}).items()}
    # Asegurar espacio de Timbre Fiscal Digital
    if "tfd" not in nsmap:
        nsmap["tfd"] = "http://www.sat.gob.mx/TimbreFiscalDigital"

    # Obtener versión
    version = root.get("Version") or root.get("version") or ""
    # Tipo de comprobante
    tipo = root.get("TipoDeComprobante") or root.get("TipoComprobante") or ""
    tipo = tipo.upper() if tipo else ""
    if tipo == "P":
        # Pagos se ignoran
        return None, []

    # UUID
    uuid = None
    complemento = root.find("cfdi:Complemento", namespaces=nsmap)
    if complemento is not None:
        timbre = complemento.find("tfd:TimbreFiscalDigital", namespaces=nsmap)
        if timbre is not None:
            uuid = timbre.get("UUID")
    if not uuid:
        # Sin UUID no podemos identificar el CFDI
        return None, []

    # Advertencias
    warnings: List[str] = []
    if version.startswith("3.3"):
        warnings.append("⚠️ CFDI 3.3 detectado: procesado, pero se recomienda CFDI 4.0")

    # Fecha
    fecha_str = root.get("Fecha") or root.get("fecha")
    fecha = parse_iso_datetime(fecha_str) if fecha_str else None

    # Serie y folio
    serie = root.get("Serie") or ""
    folio = root.get("Folio") or ""

    # Subtotal, descuento, total, moneda, tipo de cambio
    subtotal = _safe_float(root.get("SubTotal") or root.get("SubTotal"))
    descuento = _safe_float(root.get("Descuento"))
    total = _safe_float(root.get("Total"))
    moneda = root.get("Moneda") or "MXN"
    tipo_cambio = _safe_float(root.get("TipoCambio"))

    forma_pago = root.get("FormaPago") or ""
    metodo_pago = root.get("MetodoPago") or ""
    lugar_expedicion = root.get("LugarExpedicion") or ""

    # Emisor
    emisor = root.find("cfdi:Emisor", namespaces=nsmap)
    emisor_rfc = emisor.get("Rfc") if emisor is not None else ""
    emisor_nombre = emisor.get("Nombre") if emisor is not None else ""
    emisor_regimen = emisor.get("RegimenFiscal") if emisor is not None else ""

    # Receptor
    receptor = root.find("cfdi:Receptor", namespaces=nsmap)
    receptor_rfc = receptor.get("Rfc") if receptor is not None else ""
    receptor_nombre = receptor.get("Nombre") if receptor is not None else ""
    # Regimen fiscal receptor en 4.0
    receptor_regimen = receptor.get("RegimenFiscalReceptor") if receptor is not None else ""
    # UsoCFDI
    uso_cfdi = receptor.get("UsoCFDI") if receptor is not None else ""

    # Impuestos globales
    iva_trasladado = 0.0
    isr_retenido = 0.0
    iva_retenido = 0.0
    ieps_total = 0.0

    impuestos_node = root.find("cfdi:Impuestos", namespaces=nsmap)
    if impuestos_node is not None:
        # Traslados a nivel comprobante
        traslados = impuestos_node.find("cfdi:Traslados", namespaces=nsmap)
        if traslados is not None:
            for traslado in traslados.findall("cfdi:Traslado", namespaces=nsmap):
                impuesto = traslado.get("Impuesto")
                importe = _safe_float(traslado.get("Importe"))
                if impuesto == "002":
                    iva_trasladado += importe
        # Retenciones
        retenciones = impuestos_node.find("cfdi:Retenciones", namespaces=nsmap)
        if retenciones is not None:
            for retencion in retenciones.findall("cfdi:Retencion", namespaces=nsmap):
                impuesto = retencion.get("Impuesto")
                importe = _safe_float(retencion.get("Importe"))
                if impuesto == "001":
                    isr_retenido += importe
                elif impuesto == "002":
                    iva_retenido += importe
                elif impuesto == "003":
                    ieps_total += importe

    # Conceptos
    conceptos_parent = root.find("cfdi:Conceptos", namespaces=nsmap)
    if conceptos_parent is not None:
        for concepto in conceptos_parent.findall("cfdi:Concepto", namespaces=nsmap):
            c = Concepto(
                uuid=uuid,
                clave_prod_serv=concepto.get("ClaveProdServ") or "",
                cantidad=_safe_float(concepto.get("Cantidad")),
                clave_unidad=concepto.get("ClaveUnidad") or "",
                unidad=concepto.get("Unidad") or "",
                descripcion=concepto.get("Descripcion") or "",
                valor_unitario=_safe_float(concepto.get("ValorUnitario")),
                importe=_safe_float(concepto.get("Importe")),
                descuento=_safe_float(concepto.get("Descuento")),
            )
            # Impuestos por concepto
            imp_node = concepto.find("cfdi:Impuestos", namespaces=nsmap)
            if imp_node is not None:
                # Traslados
                tras = imp_node.find("cfdi:Traslados", namespaces=nsmap)
                if tras is not None:
                    for tr in tras.findall("cfdi:Traslado", namespaces=nsmap):
                        impuesto = tr.get("Impuesto")
                        importe = _safe_float(tr.get("Importe"))
                        c.impuestos_traslado[impuesto] = c.impuestos_traslado.get(impuesto, 0.0) + importe
                        # Acumular al global
                        if impuesto == "002":
                            iva_trasladado += importe
                        elif impuesto == "003":
                            ieps_total += importe
                # Retenciones
                ret = imp_node.find("cfdi:Retenciones", namespaces=nsmap)
                if ret is not None:
                    for rt in ret.findall("cfdi:Retencion", namespaces=nsmap):
                        impuesto = rt.get("Impuesto")
                        importe = _safe_float(rt.get("Importe"))
                        c.impuestos_retencion[impuesto] = c.impuestos_retencion.get(impuesto, 0.0) + importe
                        if impuesto == "001":
                            isr_retenido += importe
                        elif impuesto == "002":
                            iva_retenido += importe
                        elif impuesto == "003":
                            ieps_total += importe
            concepts.append(c)

    # Crear CFDI
    cfdi = CFDI(
        uuid=uuid,
        fecha=fecha,
        tipo=tipo,
        serie=serie,
        folio=folio,
        emisor_rfc=emisor_rfc or "",
        emisor_nombre=emisor_nombre or "",
        emisor_regimen=emisor_regimen or "",
        receptor_rfc=receptor_rfc or "",
        receptor_nombre=receptor_nombre or "",
        receptor_regimen=receptor_regimen or "",
        uso_cfdi=uso_cfdi or "",
        subtotal=subtotal,
        descuento=descuento,
        total=total,
        moneda=moneda,
        tipo_cambio=tipo_cambio,
        forma_pago=forma_pago or "",
        metodo_pago=metodo_pago or "",
        lugar_expedicion=lugar_expedicion or "",
        iva_trasladado=iva_trasladado,
        isr_retenido=isr_retenido,
        iva_retenido=iva_retenido,
        ieps=ieps_total,
        num_conceptos=len(concepts),
        version=version,
        warnings=warnings,
    )
    return cfdi, concepts