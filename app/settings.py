"""Manejo de configuración de la aplicación mediante QSettings.

La configuración incluye el RFC del usuario y el tema de la interfaz. Estos
valores se almacenan de forma persistente en el registro (Windows) o en el
archivo de configuración apropiado en otras plataformas.
"""
from __future__ import annotations

from PySide6.QtCore import QSettings


class Settings:
    """Envuelve QSettings para simplificar el acceso a configuraciones de usuario."""

    ORGANIZATION = "EDDP"
    APPLICATION = "Analizador CFDI"

    def __init__(self) -> None:
        self._settings = QSettings(Settings.ORGANIZATION, Settings.APPLICATION)

    @property
    def rfc(self) -> str | None:
        return self._settings.value("rfc", type=str)

    @rfc.setter
    def rfc(self, value: str) -> None:
        self._settings.setValue("rfc", value.upper())

    @property
    def theme_mode(self) -> str:
        """Modo de tema: 'system', 'light', 'dark'."""
        return self._settings.value("theme_mode", "system", type=str)

    @theme_mode.setter
    def theme_mode(self, value: str) -> None:
        if value not in {"system", "light", "dark"}:
            value = "system"
        self._settings.setValue("theme_mode", value)

    @property
    def theme(self) -> str:
        """Tema efectivo ('light' o 'dark') resuelto según la configuración."""
        mode = self.theme_mode
        if mode == "system":
            try:
                from .theme import detect_windows_theme
                return detect_windows_theme()
            except ImportError:
                return "light"
        return mode