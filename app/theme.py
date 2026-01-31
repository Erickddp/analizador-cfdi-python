"""Gestión y detección del tema (claro/oscuro) de la aplicación.

Este módulo centraliza la lógica de estilos, paletas de colores y detección
automática del tema del sistema operativo Windows.
"""
from __future__ import annotations

import platform
import winreg
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt


def detect_windows_theme() -> str:
    """Retorna 'dark' o 'light' leyendo el registro de Windows.
    
    Busca en HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize
    "AppsUseLightTheme" (0=oscuro, 1=claro).
    Si falla o no es Windows, retorna 'light'.
    """
    if platform.system() != "Windows":
        return "light"

    try:
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        # 0 = Dark, 1 = Light
        return "dark" if value == 0 else "light"
    except Exception:
        return "light"


class ThemeManager:
    """Gestor centralizado de temas."""
    
    @staticmethod
    def apply_theme(app: QApplication, theme: str) -> None:
        """Aplica el tema visual completo a la aplicación.
        
        Args:
            app: Instancia de QApplication.
            theme: 'dark' o 'light'.
        """
        app.setStyle("Fusion")
        
        # Ajuste de fuente global
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        palette = QPalette()
        if theme == "dark":
            # Base colors - Using a slightly refined palette for "premium" feel
            dark_bg = QColor(32, 33, 36)      # Google Dark / VS Code-ish
            dark_panel = QColor(44, 45, 48)   # Lighter panel
            text_white = QColor(240, 240, 240)
            accent_blue = QColor(64, 156, 255) # Bright premium blue
            
            palette.setColor(QPalette.Window, dark_bg)
            palette.setColor(QPalette.WindowText, text_white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25)) # Input fields darker
            palette.setColor(QPalette.AlternateBase, dark_panel)
            palette.setColor(QPalette.ToolTipBase, text_white)
            palette.setColor(QPalette.ToolTipText, text_white)
            palette.setColor(QPalette.Text, text_white)
            palette.setColor(QPalette.Button, dark_panel)
            palette.setColor(QPalette.ButtonText, text_white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, accent_blue)
            palette.setColor(QPalette.Highlight, accent_blue)
            palette.setColor(QPalette.HighlightedText, Qt.black)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
        else:
            # Clean Light Palette
            light_bg = QColor(250, 250, 250)
            light_panel = QColor(255, 255, 255)
            text_black = QColor(32, 33, 36)
            accent_blue_light = QColor(0, 120, 215) # Windows Blue
            
            palette.setColor(QPalette.Window, light_bg)
            palette.setColor(QPalette.WindowText, text_black)
            palette.setColor(QPalette.Base, light_panel)
            palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ToolTipBase, text_black)
            palette.setColor(QPalette.ToolTipText, text_black)
            palette.setColor(QPalette.Text, text_black)
            palette.setColor(QPalette.Button, QColor(245, 245, 245))
            palette.setColor(QPalette.ButtonText, text_black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, accent_blue_light)
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(160, 160, 160))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(160, 160, 160))

        app.setPalette(palette)
        app.setStyleSheet(ThemeManager.get_stylesheet(theme))

    @staticmethod
    def get_stylesheet(theme: str) -> str:
        """Retorna la hoja de estilos CSS refinada."""
        if theme == "dark":
            return """
            QWidget {
                outline: none;
            }
            QMainWindow {
                background-color: #202124;
            }
            QTabWidget::pane {
                border: 1px solid #3C4043;
                background: #202124;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #2D2E31;
                color: #BDC1C6;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected {
                background: #202124;
                color: #8AB4F8; /* Google Blue Light */
                border-bottom: 2px solid #8AB4F8;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #35363A;
            }
            QTableView {
                background-color: #202124;
                alternate-background-color: #2D2E31;
                gridline-color: #3C4043;
                color: #BDC1C6;
                selection-background-color: #8AB4F8;
                selection-color: #202124;
                border: 1px solid #3C4043;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2D2E31;
                color: #BDC1C6;
                padding: 6px;
                border: none;
                border-right: 1px solid #3C4043;
                border-bottom: 1px solid #3C4043;
                font-weight: bold;
            }
            QHeaderView::section:horizontal {
                border-top: 1px solid #3C4043;
            }
            QLineEdit, QDateEdit {
                background-color: #171717;
                border: 1px solid #3C4043;
                color: #E8EAED;
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 1px solid #8AB4F8;
            }
            QPushButton {
                background-color: #8AB4F8;
                color: #202124;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #AECBFA;
            }
            QPushButton:pressed {
                background-color: #669DF6;
            }
            QScrollBar:vertical {
                border: none;
                background: #202124;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #5F6368;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #202124;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #5F6368;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QMenu {
                background-color: #2D2E31;
                color: #E8EAED;
                border: 1px solid #3C4043;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px; 
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #3C4043;
            }
            QComboBox {
                background-color: #2D2E31;
                border: 1px solid #3C4043;
                border-radius: 4px;
                padding: 5px;
                color: #E8EAED;
                min-width: 6em;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 0px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            """
        else:
            return """
            QWidget {
                outline: none;
            }
            QMainWindow {
                background-color: #FAFAFA;
            }
            QTabWidget::pane {
                border: 1px solid #DADCE0;
                background: #FFFFFF;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #F1F3F4;
                color: #5F6368;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #1A73E8; /* Google Blue */
                border-bottom: 2px solid #1A73E8;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #E8EAED;
            }
            QTableView {
                background-color: #FFFFFF;
                alternate-background-color: #F8F9FA;
                gridline-color: #DADCE0;
                color: #202124;
                selection-background-color: #E8F0FE;
                selection-color: #1967D2;
                border: 1px solid #DADCE0;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #F8F9FA;
                color: #5F6368;
                padding: 6px;
                border: none;
                border-right: 1px solid #DADCE0;
                border-bottom: 1px solid #DADCE0;
                font-weight: bold;
            }
            QHeaderView::section:horizontal {
                border-top: 1px solid #DADCE0;
            }
            QLineEdit, QDateEdit {
                background-color: #FFFFFF;
                border: 1px solid #DADCE0;
                color: #202124;
                padding: 6px;
                border-radius: 4px;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 1px solid #1A73E8;
            }
            QPushButton {
                background-color: #1A73E8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #185ABC;
            }
            QPushButton:pressed {
                background-color: #174EA6;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F3F4;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #BDC1C6;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background: #F1F3F4;
                height: 10px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #BDC1C6;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QMenu {
                background-color: #FFFFFF;
                color: #202124;
                border: 1px solid #DADCE0;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 20px; 
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #F1F3F4;
            }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #DADCE0;
                border-radius: 4px;
                padding: 5px;
                color: #202124;
                min-width: 6em;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 0px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            """
