"""Interfaz común que deben implementar todos los conectores de datos.

Regla del pipeline (PLAN-ASESOR-FINANCIERO.md §5): dato sin fecha = rechazado.
Por eso PrecioDiario exige fecha y cierre; el resto es opcional según la fuente.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PrecioDiario:
    fecha: date
    cierre: float
    apertura: float | None = None
    alto: float | None = None
    bajo: float | None = None
    cierre_ajustado: float | None = None
    volumen: int | None = None


@dataclass(frozen=True)
class Vela4h:
    """Vela intradía de 4h (§3.5 F3). Separada de `PrecioDiario` porque lleva
    hora, no solo fecha, y porque yfinance solo la cubre ~2 años atrás (no 3
    como el EOD) — límite de la API gratuita para datos intradía.
    """

    fecha_hora: datetime
    cierre: float
    apertura: float | None = None
    alto: float | None = None
    bajo: float | None = None
    volumen: int | None = None


class FuenteDatos(ABC):
    """Contrato común de los conectores (yfinance, stooq, coingecko, datos_gov_co, ...)."""

    nombre: str

    @abstractmethod
    def obtener_precios(self, ticker: str, desde: date, hasta: date) -> list[PrecioDiario]:
        """Devuelve precios diarios ordenados por fecha ascendente. Lista vacía si no hay dato."""

    @abstractmethod
    def disponible(self) -> bool:
        """Chequeo rápido de que la fuente responde (para salud_fuentes)."""
