"""Interfaz de usuario principal de la aplicación CFDI Analyzer.

La interfaz se construye con PySide6 y sigue un diseño minimalista en
español. Incluye un encabezado con nombre de la aplicación y toggle de tema,
botón de carga de XML, barra de progreso, contadores y tres pestañas para
Ingresos, Egresos y KPIs. La clase `MainWindow` coordina la lógica de UI con
el escaneo, clasificación y exportación de datos.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QTabWidget,
    QLineEdit,
    QTableView,
    QMessageBox,
    QCheckBox,
    QApplication,
    QSizePolicy,
    QMenu,
    QHeaderView,
    QFrame,
    QGridLayout,
    QScrollArea,
    QToolButton,
)
from PySide6.QtGui import QAction, QIcon, QCursor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from .settings import Settings
from .utils import (
    apply_theme, 
    validate_rfc, 
    build_monthly_series, 
    format_currency_axis, 
    apply_mpl_theme
)
from .scanner import XMLScanner
from .kpis import compute_kpis, cfdis_to_dataframe
from .exporter_excel import export_to_excel
from .report_pdf import generate_report
from .models import CFDI
from matplotlib.ticker import FuncFormatter


class CFDITableModel(QSortFilterProxyModel):
    """Modelo de tabla basado en un DataFrame con soporte de filtrado global."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)  # Filtrar todas las columnas

    def set_source(self, df):
        from PySide6.QtCore import QAbstractTableModel

        class _Model(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
                self._headers = list(data.columns)

            def rowCount(self, parent=None):
                return len(self._data)

            def columnCount(self, parent=None):
                return len(self._headers)

            def data(self, index, role=Qt.DisplayRole):
                if not index.isValid():
                    return None
                if role == Qt.DisplayRole:
                    value = self._data.iat[index.row(), index.column()]
                    return "" if value is None else str(value)
                return None

            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    if orientation == Qt.Horizontal:
                        return self._headers[section]
                    else:
                        return section + 1
                return None

        model = _Model(df)
        self.setSourceModel(model)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizador CFDI")
        self.settings = Settings()
        self.setMinimumSize(1180, 720)
        
        # Aplicar tema globalmente
        apply_theme(QApplication.instance(), self.settings.theme)
        
        # Contenedores de datos
        self.cfdis: List[CFDI] = []
        self.ingresos: List[CFDI] = []
        self.egresos: List[CFDI] = []
        self.concepts: List = []
        self.kpis_data = {}
        self.invalid_count = 0
        self.duplicates_count = 0
        self.cfdi33_count = 0
        self._build_ui()
        self._prompt_for_rfc()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("Analizador CFDI")
        title.setStyleSheet("font-size: 20pt; font-weight: bold;")
        subtitle = QLabel("by EDDP")
        subtitle.setStyleSheet("font-size: 8pt; color: gray;")
        title_container = QVBoxLayout()
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        header.addLayout(title_container)
        header.addStretch()
        
        # Selector de tema
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Tema:")
        theme_label.setStyleSheet("font-weight: bold; color: gray;")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Sistema", "Claro", "Oscuro"])
        self.theme_selector.setFixedWidth(100)
        
        # Configurar selección actual
        current_mode = self.settings.theme_mode
        mode_map = {"system": 0, "light": 1, "dark": 2}
        self.theme_selector.setCurrentIndex(mode_map.get(current_mode, 0))
        
        self.theme_selector.activated.connect(self._on_theme_changed)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        header.addLayout(theme_layout)
        
        vbox.addLayout(header)

        # Botón de carga
        self.load_button = QPushButton("Cargar XML")
        self.load_button.setFixedHeight(40)
        self.load_button.clicked.connect(self._on_load_clicked)
        vbox.addWidget(self.load_button)

        # Barra de progreso y contadores
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        vbox.addWidget(self.progress_bar)
        counts_layout = QHBoxLayout()
        self.label_total = QLabel("Total: 0")
        self.label_invalid = QLabel("Inválidos: 0")
        self.label_duplicates = QLabel("Duplicados: 0")
        self.label_cfdi33 = QLabel("CFDI 3.3: 0")
        counts_layout.addWidget(self.label_total)
        counts_layout.addWidget(self.label_invalid)
        counts_layout.addWidget(self.label_duplicates)
        counts_layout.addWidget(self.label_cfdi33)
        counts_layout.addStretch()
        vbox.addLayout(counts_layout)

        # Tabs
        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs)

        # Ingresos tab
        self.tab_ingresos = QWidget()
        self._setup_tab(self.tab_ingresos)
        self.tabs.addTab(self.tab_ingresos, "Ingresos")

        # Egresos tab
        self.tab_egresos = QWidget()
        self._setup_tab(self.tab_egresos)
        self.tabs.addTab(self.tab_egresos, "Egresos")

        # KPIs tab
        self.tab_kpis = QWidget()
        self._setup_kpis_tab()
        self.tabs.addTab(self.tab_kpis, "KPIs")

        # Export buttons
        export_layout = QHBoxLayout()
        self.btn_export_excel = QPushButton("Exportar Excel")
        self.btn_export_excel.clicked.connect(self._export_excel)
        self.btn_export_pdf = QPushButton("Generar Reporte PDF")
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        export_layout.addWidget(self.btn_export_excel)
        export_layout.addWidget(self.btn_export_pdf)
        export_layout.addStretch()
        vbox.addLayout(export_layout)

    def _setup_tab(self, tab_widget: QWidget):
        layout = QVBoxLayout(tab_widget)
        # Barra de búsqueda
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("UUID, RFC, nombre, folio…")
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        # Tabla
        table_view = QTableView()
        table_view.setSortingEnabled(True)
        # Ajustes de estabilidad visual
        header = table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        layout.addWidget(table_view)
        # Modelo
        model = CFDITableModel(self)
        table_view.setModel(model)
        # Conectar búsqueda a filtro
        def on_search(text):
            regex = QRegularExpression(text)
            model.setFilterRegularExpression(regex)
        search_edit.textChanged.connect(on_search)
        # Guardar referencias en widget para acceso posterior
        tab_widget._table = table_view
        tab_widget._model = model

    def _create_kpi_card(self, title: str) -> tuple[QFrame, QLabel]:
        """Crea una tarjeta tipo KPI con título fijo y valor actualizable."""
        card = QFrame()
        card.setFixedHeight(85)
        # Estilo base manejado por stylesheet (clase QFrame) pero reforzamos bordes/fondo especifico si se desea
        # card.setStyleSheet("background-color: ...") -> mejor dejar que el tema global maneje QFrame o usar un objectName
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 10pt; color: gray; font-weight: normal;")
        lbl_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        lbl_value = QLabel("0")
        lbl_value.setStyleSheet("font-size: 16pt; font-weight: bold;")
        lbl_value.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return card, lbl_value

    def _setup_kpis_tab(self):
        # Layout principal del tab (contendrá solo el ScrollArea)
        main_layout = QVBoxLayout(self.tab_kpis)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Crear ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        main_layout.addWidget(scroll)

        # 2. Contenido del Scroll
        self.kpis_scroll_content = QWidget()
        scroll.setWidget(self.kpis_scroll_content)
        
        scroll_layout = QVBoxLayout(self.kpis_scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        # --- A. Grid de Tarjetas (Cards) ---
        self.kpi_value_labels = {}
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        kpis_row1 = [
            ("Total Ingresos", "total_ingresos"),
            ("Total Egresos", "total_egresos"),
            ("Neto", "neto"),
            ("N° CFDI", "conteo_cfdi")
        ]
        kpis_row2 = [
            ("IVA Trasladado", "iva_trasladado"),
            ("ISR Retenido", "isr_retenido"),
            ("IVA Retenido", "iva_retenido"),
            ("IEPS", "ieps")
        ]

        for col, (name, key) in enumerate(kpis_row1):
            card, lbl_val = self._create_kpi_card(name)
            grid_layout.addWidget(card, 0, col)
            self.kpi_value_labels[key] = lbl_val
            
        for col, (name, key) in enumerate(kpis_row2):
            card, lbl_val = self._create_kpi_card(name)
            grid_layout.addWidget(card, 1, col)
            self.kpi_value_labels[key] = lbl_val

        scroll_layout.addLayout(grid_layout)

        # --- B. Gráfica Principal ---
        self.kpis_fig_main = plt.figure(constrained_layout=True)
        self.kpis_canvas_main = FigureCanvas(self.kpis_fig_main)
        self.kpis_canvas_main.setStyleSheet("background: transparent;")
        self.kpis_canvas_main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kpis_canvas_main.setMinimumHeight(320)
        
        scroll_layout.addWidget(self.kpis_canvas_main)

        # --- C. Botón Colapsable ---
        self.details_btn = QToolButton()
        self.details_btn.setText("Mostrar detalles")
        self.details_btn.setCheckable(True)
        self.details_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.details_btn.setArrowType(Qt.RightArrow)
        self.details_btn.setStyleSheet("QToolButton { border: none; color: gray; font-size: 10pt; font-weight: bold; }")
        self.details_btn.clicked.connect(self._toggle_details)
        
        scroll_layout.addWidget(self.details_btn, alignment=Qt.AlignLeft)

        # --- D. Sección de Detalles (Top 5) ---
        self.details_container = QWidget()
        self.details_container.setVisible(False)
        details_layout = QHBoxLayout(self.details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(20)
        
        # Top Clientes
        self.kpis_fig_clients = plt.figure(constrained_layout=True)
        self.kpis_canvas_clients = FigureCanvas(self.kpis_fig_clients)
        self.kpis_canvas_clients.setStyleSheet("background: transparent;")
        self.kpis_canvas_clients.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kpis_canvas_clients.setMinimumHeight(220)
        
        # Top Proveedores
        self.kpis_fig_providers = plt.figure(constrained_layout=True)
        self.kpis_canvas_providers = FigureCanvas(self.kpis_fig_providers)
        self.kpis_canvas_providers.setStyleSheet("background: transparent;")
        self.kpis_canvas_providers.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kpis_canvas_providers.setMinimumHeight(220)
        
        details_layout.addWidget(self.kpis_canvas_clients)
        details_layout.addWidget(self.kpis_canvas_providers)
        
        scroll_layout.addWidget(self.details_container)
        
        # Inicializar axes placeholders
        self.kpis_ax_main = None
        self.kpis_ax_clients = None
        self.kpis_ax_providers = None

    def _toggle_details(self):
        visible = self.details_btn.isChecked()
        self.details_container.setVisible(visible)
        if visible:
            self.details_btn.setText("Ocultar detalles")
            self.details_btn.setArrowType(Qt.DownArrow)
        else:
            self.details_btn.setText("Mostrar detalles")
            self.details_btn.setArrowType(Qt.RightArrow)

    def _update_kpis_ui(self):
        if not self.kpis_data:
            return
            
        # 1. Actualizar Tarjetas
        for key, label in self.kpi_value_labels.items():
            val = self.kpis_data.get(key, 0)
            if isinstance(val, (int, float)):
                # Formato moneda excepto para conteo
                if key == "conteo_cfdi":
                    text = f"{val}"
                else:
                    text = f"${val:,.2f}"
            else:
                text = str(val)
            label.setText(text)

        # 2. Actualizar Gráficas
        theme_mode = self.settings.theme  # "light" o "dark"
        
        # Definir fuente de datos
        ingresos = self.ingresos if hasattr(self, 'ingresos') else []
        egresos = self.egresos if hasattr(self, 'egresos') else []

        # --- A) Gráfica Principal: Totales por mes ---
        self.kpis_fig_main.clear()
        # Ajuste para evitar recorte de etiquetas rotadas
        self.kpis_fig_main.subplots_adjust(bottom=0.22)
        ax_main = self.kpis_fig_main.add_subplot(111)
        
        df_monthly = build_monthly_series(ingresos, egresos)
        
        if not df_monthly.empty:
            x = range(len(df_monthly.index))
            # Barras lado a lado
            ax_main.bar([i - 0.2 for i in x], df_monthly["Ingresos"], width=0.4, label="Ingresos", color="#4CAF50")
            ax_main.bar([i + 0.2 for i in x], df_monthly["Egresos"], width=0.4, label="Egresos", color="#F44336")
            
            ax_main.set_xticks(list(x))
            ax_main.set_xticklabels(df_monthly.index, rotation=35, ha='right')
            ax_main.set_xlabel("Mes")
            ax_main.set_ylabel("Monto")
            ax_main.set_title("Totales por mes")
            ax_main.yaxis.set_major_formatter(FuncFormatter(format_currency_axis))
            ax_main.legend()
        else:
            ax_main.text(0.5, 0.5, "Sin datos para mostrar", ha='center', va='center')

        # Helper para truncar etiquetas
        def truncate_label(text, length=18):
            s = str(text)
            return s[:length] + "..." if len(s) > length else s

        # --- B) Top 5 Clientes (Ingresos) ---
        self.kpis_fig_clients.clear()
        self.kpis_fig_clients.subplots_adjust(left=0.25) # Espacio para nombres
        ax_clients = self.kpis_fig_clients.add_subplot(111)
        
        if ingresos:
            # Agrupar por RFC Receptor (mis clientes)
            clients_sum = {}
            for c in ingresos:
                key = c.receptor_nombre if c.receptor_nombre else c.receptor_rfc
                clients_sum[key] = clients_sum.get(key, 0.0) + c.total
            
            top_clients = sorted(clients_sum.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_clients:
                # Truncar nombres
                names = [truncate_label(item[0]) for item in top_clients]
                vals = [item[1] for item in top_clients]
                # Invertir
                ax_clients.barh(names[::-1], vals[::-1], color="#2196F3")
                ax_clients.set_title("Top 5 Clientes")
                ax_clients.xaxis.set_major_formatter(FuncFormatter(format_currency_axis))
                # Margen X para que quepan los textos de valores si se ponen, o simplemente estética
                ax_clients.margins(x=0.05)
        else:
            ax_clients.text(0.5, 0.5, "Sin datos de Ingresos", ha='center', va='center')

        # --- C) Top 5 Proveedores (Egresos) ---
        self.kpis_fig_providers.clear()
        self.kpis_fig_providers.subplots_adjust(left=0.25)
        ax_providers = self.kpis_fig_providers.add_subplot(111)
        
        if egresos:
            # Agrupar por RFC Emisor (mis proveedores)
            providers_sum = {}
            for c in egresos:
                key = c.emisor_nombre if c.emisor_nombre else c.emisor_rfc
                providers_sum[key] = providers_sum.get(key, 0.0) + c.total
            
            top_providers = sorted(providers_sum.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_providers:
                names = [truncate_label(item[0]) for item in top_providers]
                vals = [item[1] for item in top_providers]
                ax_providers.barh(names[::-1], vals[::-1], color="#FF9800")
                ax_providers.set_title("Top 5 Proveedores")
                ax_providers.xaxis.set_major_formatter(FuncFormatter(format_currency_axis))
                ax_providers.margins(x=0.05)
        else:
            ax_providers.text(0.5, 0.5, "Sin datos de Egresos", ha='center', va='center')

        # Aplicar tema unificado
        apply_mpl_theme(self.kpis_fig_main, ax_main, theme_mode)
        apply_mpl_theme(self.kpis_fig_clients, ax_clients, theme_mode)
        apply_mpl_theme(self.kpis_fig_providers, ax_providers, theme_mode)
        
        # Redibujar Idle
        self.kpis_canvas_main.draw_idle()
        self.kpis_canvas_clients.draw_idle()
        self.kpis_canvas_providers.draw_idle()

    def _prompt_for_rfc(self):
        # Si ya existe RFC en settings, no preguntar
        if self.settings.rfc:
            return
        from PySide6.QtWidgets import QInputDialog
        while True:
            rfc, ok = QInputDialog.getText(self, "RFC requerido", "¿Cuál es tu RFC?")
            if not ok:
                QMessageBox.warning(self, "RFC requerido", "Debes proporcionar un RFC para usar la aplicación.")
                continue
            if validate_rfc(rfc):
                self.settings.rfc = rfc.upper()
                break
            else:
                QMessageBox.warning(self, "RFC inválido", "El RFC ingresado no es válido. Intenta nuevamente.")

    def _on_theme_changed(self, index):
        modes = ["system", "light", "dark"]
        mode = modes[index]
        self.settings.theme_mode = mode
        
        # Reaplicar tema (settings.theme resuelve automáticamente sies system)
        new_theme = self.settings.theme
        apply_theme(QApplication.instance(), new_theme)
        
        # Refrescar UI (gráficas) para adaptar colores
        self._update_kpis_ui()

    # El método local apply_theme se ha eliminado en favor de la función global en utils

    def _on_load_clicked(self):
        # Menú unificado para cargar archivos o carpeta
        menu = QMenu(self)
        action_files = QAction("Seleccionar archivos XML...", self)
        action_folder = QAction("Seleccionar carpeta completa...", self)
        
        menu.addAction(action_files)
        menu.addAction(action_folder)
        
        # Mostrar menú debajo del cursor
        action = menu.exec(QCursor.pos())
        
        paths = []
        if action == action_files:
            files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos XML", "", "Archivos XML (*.xml)")
            if files:
                paths = files
        elif action == action_folder:
            directory = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con XML")
            if directory:
                paths = [directory]
        
        if not paths:
            return
        # Iniciar escaneo
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.label_total.setText("Total: 0")
        self.label_invalid.setText("Inválidos: 0")
        self.label_duplicates.setText("Duplicados: 0")
        self.label_cfdi33.setText("CFDI 3.3: 0")
        # Reset data
        self.cfdis = []
        self.concepts = []
        # Crear scanner
        scanner = XMLScanner(paths, self.settings.rfc or "")
        self._scanner = scanner  # guardar referencia para evitar GC
        scanner.progress.connect(self._on_scan_progress)
        scanner.finished.connect(self._on_scan_finished)
        scanner.start()

    def _on_scan_progress(self, processed, invalid, duplicates, cfdi33, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(processed)
        self.label_total.setText(f"Total: {total}")
        self.label_invalid.setText(f"Inválidos: {invalid}")
        self.label_duplicates.setText(f"Duplicados: {duplicates}")
        self.label_cfdi33.setText(f"CFDI 3.3: {cfdi33}")

        # Guardar para KPIs
        self.invalid_count = invalid
        self.duplicates_count = duplicates
        self.cfdi33_count = cfdi33

    def _on_scan_finished(self, cfdis: List[CFDI], concepts: List):
        self.progress_bar.setVisible(False)
        self.cfdis = cfdis
        self.concepts = concepts
        
        # Clasificar robustamente
        self.ingresos = [c for c in cfdis if c.clasificacion == "Ingresos"]
        self.egresos = [c for c in cfdis if c.clasificacion == "Egresos"]
        
        # Actualizar modelos de tablas
        df = cfdis_to_dataframe(self.cfdis)
        df_ingresos = df[df["Clasificación"] == "Ingresos"].copy()
        df_egresos = df[df["Clasificación"] == "Egresos"].copy()
        self.tab_ingresos._model.set_source(df_ingresos)
        self.tab_egresos._model.set_source(df_egresos)
        
        # Recalcular KPIs
        self.kpis_data = compute_kpis(cfdis, self.invalid_count, self.duplicates_count, self.cfdi33_count)
        self._update_kpis_ui()
        QMessageBox.information(self, "Procesamiento finalizado", f"Se procesaron {len(cfdis)} CFDI.")



    def _export_excel(self):
        if not self.cfdis:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "CFDI_report.xlsx", "Archivo Excel (*.xlsx)")
        if not filename:
            return
        try:
            export_to_excel(filename, self.cfdis, self.concepts, self.kpis_data)
            QMessageBox.information(self, "Éxito", f"Archivo Excel guardado en {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Excel: {e}")

    def _export_pdf(self):
        if not self.cfdis:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "CFDI_report.pdf", "Archivo PDF (*.pdf)")
        if not filename:
            return
        try:
            generate_report(filename, self.cfdis, self.kpis_data, self.settings.rfc or "")
            QMessageBox.information(self, "Éxito", f"Reporte PDF guardado en {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {e}")


def run_app():
    app = QApplication([])
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    return app.exec()