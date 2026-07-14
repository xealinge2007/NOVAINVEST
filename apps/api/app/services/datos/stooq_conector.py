"""Conector de respaldo (EOD) para tickers de EEUU/globales cuando yfinance falla.

No cubre BVC de forma confiable (Stooq no tiene los emisores colombianos) —
ver NOTAS_F0.md. Se usa solo como fallback del universo no-BVC.
"""

import csv
import io
from datetime import date, datetime

import requests

from .base import FuenteDatos, PrecioDiario

_URL = "https://stooq.com/q/d/l/?s={simbolo}&i=d"


def _a_simbolo_stooq(ticker: str) -> str:
    # Stooq usa sufijo .us para acciones/ETFs de EEUU; los demás formatos
    # (índices, cripto) se pasan tal cual y se filtran aguas arriba.
    return f"{ticker.lower()}.us"


class StooqConector(FuenteDatos):
    nombre = "stooq"

    def obtener_precios(self, ticker: str, desde: date, hasta: date) -> list[PrecioDiario]:
        simbolo = _a_simbolo_stooq(ticker)
        resp = requests.get(_URL.format(simbolo=simbolo), timeout=20)
        resp.raise_for_status()
        texto = resp.text.strip()
        if not texto or texto.startswith("No data") or "<html" in texto.lower():
            return []
        precios = []
        lector = csv.DictReader(io.StringIO(texto))
        for fila in lector:
            try:
                fecha = datetime.strptime(fila["Date"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            if fecha < desde or fecha > hasta:
                continue
            precios.append(
                PrecioDiario(
                    fecha=fecha,
                    apertura=float(fila["Open"]) if fila.get("Open") else None,
                    alto=float(fila["High"]) if fila.get("High") else None,
                    bajo=float(fila["Low"]) if fila.get("Low") else None,
                    cierre=float(fila["Close"]),
                    volumen=int(float(fila["Volume"])) if fila.get("Volume") else None,
                )
            )
        return sorted(precios, key=lambda p: p.fecha)

    def disponible(self) -> bool:
        try:
            return len(self.obtener_precios("AAPL", date(2026, 1, 1), date(2026, 1, 10))) > 0
        except Exception:
            return False
