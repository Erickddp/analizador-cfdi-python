"""Pruebas básicas para el parser y la clasificación de CFDI."""
import tempfile
from pathlib import Path

from cfdi_analyzer_edpp.app.parser_cfdi import parse_cfdi
from cfdi_analyzer_edpp.app.classifier import classify_cfdi


SAMPLE_CFDI_40 = """
<cfdi:Comprobante Version="4.0" Fecha="2023-01-31T12:00:00" Serie="A" Folio="1" TipoDeComprobante="I"
 SubTotal="100" Total="116" Moneda="MXN" FormaPago="01" MetodoPago="PUE" LugarExpedicion="99999"
 xmlns:cfdi="http://www.sat.gob.mx/cfd/4" xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital">
  <cfdi:Emisor Rfc="AAA010101AAA" Nombre="Emisor SA de CV" RegimenFiscal="601"/>
  <cfdi:Receptor Rfc="BBB010101BBB" Nombre="Receptor SA de CV" UsoCFDI="G03" RegimenFiscalReceptor="601"/>
  <cfdi:Conceptos>
    <cfdi:Concepto ClaveProdServ="01010101" Cantidad="1" ClaveUnidad="E48" Unidad="Servicio" Descripcion="Servicio de prueba" ValorUnitario="100" Importe="100">
      <cfdi:Impuestos>
        <cfdi:Traslados>
          <cfdi:Traslado Base="100" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="16"/>
        </cfdi:Traslados>
      </cfdi:Impuestos>
    </cfdi:Concepto>
  </cfdi:Conceptos>
  <cfdi:Impuestos>
    <cfdi:Traslados>
      <cfdi:Traslado Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="16"/>
    </cfdi:Traslados>
  </cfdi:Impuestos>
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital Version="1.1" UUID="12345678-1234-1234-1234-123456789012" FechaTimbrado="2023-01-31T12:00:00" RfcProvCertif="AAA010101AAA"/>
  </cfdi:Complemento>
</cfdi:Comprobante>
"""


def test_parse_and_classify_cfdi_40():
    # Crear archivo temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "cfdi.xml"
        fpath.write_text(SAMPLE_CFDI_40.strip(), encoding="utf-8")
        cfdi, concepts = parse_cfdi(str(fpath))
        assert cfdi is not None, "El parser debe retornar un CFDI válido"
        assert cfdi.uuid == "12345678-1234-1234-1234-123456789012"
        # Clasificación
        clasif = classify_cfdi(cfdi, "BBB010101BBB")
        assert clasif == "Ingresos"
        cfdi.clasificacion = clasif
        assert cfdi.total == 116.0
        # Conceptos
        assert len(concepts) == 1