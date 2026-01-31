# Analizador CFDI EDDP

Bienvenido al **Analizador CFDI EDDP**, una herramienta de escritorio (Windows) diseñada para contadores y usuarios que necesitan **cargar, clasificar y analizar masivamente comprobantes fiscales digitales (CFDI)** de manera totalmente offline. La aplicación está desarrollada en **Python 3.11** utilizando **PySide6** para la interfaz gráfica y soporta las versiones **CFDI 4.0** y **CFDI 3.3**.

## Características principales

1. **Carga masiva de XML**: selecciona archivos individuales o carpetas completas con cientos o miles de CFDI.
2. **Procesamiento concurrente**: el escaneo y parsing se realiza en segundo plano para que la interfaz no se congele.
3. **Clasificación automática**:
   - **Ingresos**: `TipoComprobante = "I"` y el RFC configurado corresponde al receptor.
   - **Egresos**: `TipoComprobante = "E"` y el RFC configurado corresponde al receptor.
   - CFDI tipo **P (Pagos)** se ignoran en esta versión.
4. **Detección de duplicados e inválidos**: los CFDI se deduplican por UUID; los XML inválidos se registran y no detienen el procesamiento.
5. **Compatible con CFDI 4.0 y 3.3**: los CFDI 3.3 se procesan pero muestran una advertencia de actualización【760692873356022†L66-L83】.
6. **Interfaz premium minimalista en español** con tema claro/oscuro conmutables y persistentes.
7. **Visualización de datos**: tablas con búsqueda y filtros simples; KPIs con tarjetas y gráficas (totales, neto, IVA trasladado, ISR retenido, etc.).
8. **Exportación**:
   - **Excel** en formato XLSX con hojas para Ingresos, Egresos, KPIs y Conceptos.
   - **Reporte PDF** (una sola hoja tamaño carta) con KPIs, gráficas y tablas principales.
9. **100 % offline**: no requiere conexión a internet, n8n ni webhooks.

## Instalación

1. Clona o descarga este repositorio y asegúrate de tener instalado **Python 3.11** o superior en Windows.
2. Instala las dependencias utilizando:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación con:

   ```bash
   python -m cfdi_analyzer_edpp.app.main
   ```

La primera vez que abras la aplicación se te pedirá tu RFC. Este valor se almacena localmente mediante `QSettings` y se utiliza para clasificar tus CFDI.

## Uso de la aplicación

1. Haz clic en **“Cargar XML”** para seleccionar uno o más archivos XML o una carpeta completa. La aplicación comenzará a procesar los archivos en segundo plano y mostrará una barra de progreso y contadores de **total**, **procesados**, **inválidos**, **duplicados** y **CFDI 3.3 detectados**.
2. Una vez finalizado el procesamiento, se actualizarán las pestañas **Ingresos**, **Egresos** y **KPIs**:
   - **Ingresos/Egresos**: muestran tablas con los campos relevantes (UUID, fecha, RFC emisor/receptor, importe, impuestos, etc.). Puedes buscar por UUID, RFC, nombre o folio y aplicar filtros sencillos.
   - **KPIs**: presenta tarjetas con totales y estadísticas (ingresos, egresos, neto, IVA trasladado, ISR retenido, número de CFDI) y gráficas de totales por mes, top RFC clientes/proveedores y calidad de datos.
3. Utiliza el interruptor de la esquina superior derecha para cambiar entre **tema claro** y **tema oscuro**. La selección queda guardada para futuras sesiones.
4. Cuando estés listo, utiliza los botones **“Exportar Excel”** o **“Generar Reporte PDF”** para crear un archivo XLSX o un PDF con la información procesada. Se te pedirá la ruta de destino para guardar el archivo.

## Generación de archivos Excel y PDF

### Excel

La exportación genera un libro de Excel con cuatro hojas:

1. **Ingresos**: una fila por CFDI de ingresos.
2. **Egresos**: una fila por CFDI de egresos.
3. **KPIs**: contiene los totales generales, totales por mes, top RFC clientes/proveedores y calidad de datos.
4. **Conceptos**: una fila por concepto, relacionada mediante el UUID y con desglose de impuestos por concepto.

### PDF

Se crea un PDF tamaño carta de una sola hoja con un diseño profesional en alto contraste. Incluye:

1. Título y RFC del perfil.
2. Tarjetas de KPIs clave.
3. Gráficas principales (ingresos vs egresos por mes, top clientes/proveedores).
4. Tabla Top 5 de clientes y proveedores.
5. Notas sobre la calidad de los datos (inválidos, duplicados y CFDI 3.3).

## Empaquetado y generación de EXE

### Generar ZIP del proyecto

Para crear un archivo ZIP con todo el proyecto listo para distribución, ejecuta:

```bash
python packaging/make_zip.py
```

Esto generará un archivo `dist/cfdi_analyzer_edpp.zip` con todos los archivos necesarios. También se incluye un script de PowerShell (`packaging/make_zip.ps1`) para usuarios que prefieran PowerShell en Windows.

### Crear ejecutable EXE (Windows)

Se incluye un script de PowerShell (`packaging/build_exe.ps1`) que utiliza **PyInstaller**. Para generar el ejecutable, sigue estos pasos:

1. Instala PyInstaller si aún no lo tienes:

   ```bash
   pip install pyinstaller
   ```

2. Ejecuta el script desde PowerShell en el directorio raíz del proyecto:

   ```powershell
   .\packaging\build_exe.ps1
   ```

El script creará la carpeta `dist\cfdi_analyzer_edpp` con el ejecutable y las dependencias necesarias. Asegúrate de copiar la carpeta `assets` junto con el ejecutable para que los recursos (íconos, temas, etc.) funcionen correctamente.

## Pruebas

Se incluyen casos de prueba unitarios en la carpeta `tests` (sin datos sensibles). Para ejecutarlos, instala `pytest` e inicia las pruebas:

```bash
pip install pytest
pytest
```

## Notas para futuras extensiones

- **CFDI de Pagos (Tipo P)** y **CFDI PPD**: actualmente la aplicación ignora los comprobantes de pagos. En futuras versiones se puede extender el parser para reconocerlos y sumarlos correctamente.
- **Validación contra el SAT**: al ser una herramienta offline, no realiza validaciones en línea. Se podría incorporar una verificación opcional mediante servicios del SAT cuando se tenga conexión.
- **Soporte para más complementos**: por ejemplo, nómina, carta porte u otros complementos que añaden nodos adicionales.

## Fuentes de referencia

Las diferencias entre las versiones CFDI 3.3 y 4.0 fueron consultadas a partir de publicaciones oficiales y blogs especializados. Entre los cambios más relevantes se encuentran la obligatoriedad de incluir nombre o razón social y domicilio fiscal del emisor y receptor, el régimen fiscal del receptor y la eliminación de la clave “P01 Por definir”【760692873356022†L66-L83】.

---

Desarrollado con ❤️ por **EDDP**."# analizador-cfdi-python" 
