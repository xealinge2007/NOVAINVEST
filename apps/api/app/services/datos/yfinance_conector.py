"""Conector primario para acciones, ETFs, cripto (vía ticker -USD) y BVC.

Verificación F0 (14-jul-2026): a diferencia de lo previsto en el plan, yfinance
SÍ cubre BVC de forma confiable usando el sufijo '.CL' (currency=COP,
exchange=BVC en los metadatos) — no se necesitó conector propio a bvc.com.co.
Ver novainvest/db/NOTAS_F0.md para el detalle de la verificación.
"""

from datetime import date

import yfinance as yf

from .base import FuenteDatos, PrecioDiario


class YfinanceConector(FuenteDatos):
    nombre = "yfinance"

    def obtener_precios(self, ticker: str, desde: date, hasta: date) -> list[PrecioDiario]:
        hist = yf.Ticker(ticker).history(start=desde, end=hasta, auto_adjust=False)
        if hist.empty:
            return []
        precios = []
        for fecha_ts, fila in hist.iterrows():
            cierre = fila.get("Close")
            if cierre != cierre:  # NaN: la sesión del día aún no cierra (visto en BVC intradía) — se descarta
                continue
            volumen = fila.get("Volume")
            precios.append(
                PrecioDiario(
                    fecha=fecha_ts.date(),
                    apertura=float(fila["Open"]) if fila.get("Open") == fila.get("Open") else None,
                    alto=float(fila["High"]) if fila.get("High") == fila.get("High") else None,
                    bajo=float(fila["Low"]) if fila.get("Low") == fila.get("Low") else None,
                    cierre=float(fila["Close"]),
                    cierre_ajustado=float(fila["Adj Close"]) if "Adj Close" in fila and fila["Adj Close"] == fila["Adj Close"] else None,
                    volumen=int(volumen) if volumen == volumen else None,
                )
            )
        return precios

    def disponible(self) -> bool:
        try:
            hist = yf.Ticker("AAPL").history(period="5d")
            return not hist.empty
        except Exception:
            return False
