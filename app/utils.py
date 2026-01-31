"""Funciones de utilidad para la aplicación CFDI Analyzer.

Este módulo centraliza funcionalidades auxiliares como validación de RFC,
conversión de fechas y formateo de valores monetarios.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

def validate_rfc(rfc: str) -> bool:
    """Valida un RFC de manera básica.

    Un RFC válido tiene entre 12 y 13 caracteres alfanuméricos y puede
    contener la letra Ñ. Este método no verifica el dígito verificador, pero
    sirve para una validación superficial.
    """
    if not rfc:
        return False
    rfc = rfc.strip().upper()
    return bool(re.fullmatch(r"[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{2,3}", rfc))


def format_currency(value: float, currency: str = "MXN") -> str:
    """Devuelve una cadena formateada de valor monetario con dos decimales.

    Si no se puede convertir el valor a decimal, devuelve '0.00'.
    """
    try:
        val = Decimal(value)
    except (InvalidOperation, TypeError):
        val = Decimal(0)
    # Formatear con separador de miles y dos decimales
    formatted = f"{val:,.2f}"
    return f"{currency} {formatted}"


def parse_iso_datetime(dt_str: str) -> datetime | None:
    """Parsa una cadena de fecha ISO (del atributo Fecha del CFDI) a datetime.

    Algunas versiones del CFDI incluyen la fecha con zona horaria, pero para
    fines de esta aplicación se ignora la información de zona.
    """
    if not dt_str:
        return None
    try:
        # El formato típico del CFDI es '2023-01-31T12:34:56'
        # Eliminar zona horaria si existe
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1]
        # Ignorar fracciones de segundo
        if '.' in dt_str:
            dt_str = dt_str.split('.')[0]
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def month_key(date: datetime | None) -> str:
    """Devuelve una clave YYYY-MM para agrupar valores por mes."""
    if date is None:
        return ""
    return f"{date.year:04d}-{date.month:02d}"


from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from .theme import ThemeManager

def apply_theme(app: QApplication, theme: str = "light") -> None:
    """Delegates theme application to ThemeManager."""
    ThemeManager.apply_theme(app, theme)


# -----------------------------------------------------------------------------
# Charting Helpers
# -----------------------------------------------------------------------------
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from dataclasses import asdict

def build_monthly_series(ingresos_list: list, egresos_list: list) -> pd.DataFrame:
    """Construye un DataFrame con totales mensuales de Ingresos y Egresos.
    
    Args:
        ingresos_list: Lista de objetos CFDI (Ingresos)
        egresos_list: Lista de objetos CFDI (Egresos)
        
    Returns:
        pd.DataFrame: Index=YYYY-MM, Columns=[Ingresos, Egresos], Values=float (fill=0).
                      Ordenado cronológicamente.
    """
    def to_df(lst, label):
        if not lst:
            return pd.DataFrame(columns=["fecha", "total", "tipo"])
        # Asumimos que los objetos tienen atributos 'fecha' y 'total'
        # Usamos asdict si es dataclass, o getattr
        data = []
        for c in lst:
            data.append({
                "fecha": c.fecha,
                "total": float(c.total) if c.total else 0.0
            })
        df = pd.DataFrame(data)
        df["tipo"] = label
        return df

    df_in = to_df(ingresos_list, "Ingresos")
    df_out = to_df(egresos_list, "Egresos")
    
    combined = pd.concat([df_in, df_out], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=["Ingresos", "Egresos"])

    # Conversión robusta de fecha
    combined["fecha"] = pd.to_datetime(combined["fecha"], errors="coerce")
    combined = combined.dropna(subset=["fecha"])
    
    # Crear periodo YYYY-MM
    combined["mes"] = combined["fecha"].dt.to_period("M").astype(str)
    
    # Pivotar
    pivot = combined.pivot_table(
        index="mes", 
        columns="tipo", 
        values="total", 
        aggfunc="sum", 
        fill_value=0
    )
    
    # Asegurar columnas
    for col in ["Ingresos", "Egresos"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
            
    # Ordenar índice (meses)
    pivot = pivot.sort_index()
    return pivot


def format_currency_axis(x, pos):
    """Formateador para eje Y de matplotlib ($ + miles)."""
    return f"${x:,.0f}"

def apply_mpl_theme(fig, ax_choices, theme_mode: str):
    """Aplica tema visual a figuras de matplotlib.
    
    Args:
        fig: Objeto Figure
        ax_choices: Lista de Axes o un solo Axes
        theme_mode: 'dark' o 'light' (o 'system' mapeado a uno de ellos)
    """
    is_dark = (theme_mode == "dark")
    
    # Colores
    text_color = "white" if is_dark else "#333333"
    grid_color = "white" if is_dark else "black"
    spine_color = "white" if is_dark else "#AAAAAA"
    
    # Fondo transparente de la figura para integrarse a la UI
    fig.patch.set_alpha(0)
    
    if not isinstance(ax_choices, list):
        ax_choices = [ax_choices]
        
    for ax in ax_choices:
        ax.set_facecolor("none") # Fondo del plot transparente
        
        # Textos y Ticks
        ax.tick_params(axis='x', colors=text_color, labelcolor=text_color)
        ax.tick_params(axis='y', colors=text_color, labelcolor=text_color)
        
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        
        # Bordes (spines)
        for spine in ax.spines.values():
            spine.set_color(spine_color)
            
        # Grid suave
        ax.grid(True, linestyle='--', alpha=0.15, color=grid_color)
        
        # Leyenda (si existe)
        legend = ax.get_legend()
        if legend:
            plt.setp(legend.get_text(), color=text_color)
            legend.get_frame().set_facecolor("none")
            legend.get_frame().set_edgecolor("none")