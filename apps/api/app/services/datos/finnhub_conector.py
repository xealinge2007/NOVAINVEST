"""Conector Finnhub para calendario de earnings (§3.5, filtro de noticias).
Requiere `FINNHUB_API_KEY` (plan free, 60 req/min — ver §5 del plan). Si la
key no está configurada, `disponible()` devuelve False y el llamador debe
tratarlo como "sin datos de earnings" (no bloquea señales, tampoco las
protege — se documenta en `filtro_noticias.py`), igual que un conector de
mercado cualquiera cuando la fuente no responde.
"""

from datetime import date, timedelta

import requests

URL_BASE = "https://finnhub.io/api/v1/calendar/earnings"


class FinnhubConector:
    nombre = "finnhub"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def disponible(self) -> bool:
        return bool(self.api_key)

    def proximos_earnings(self, ticker: str, desde: date, hasta: date) -> list[date]:
        """Fechas de earnings reportadas o esperadas para `ticker` en el rango.
        Lista vacía si no hay o si la fuente falla (no se propaga la excepción:
        el filtro de noticias debe degradar, no tumbar la generación de señales).
        """
        if not self.disponible():
            return []
        try:
            resp = requests.get(
                URL_BASE,
                params={"from": desde.isoformat(), "to": hasta.isoformat(), "symbol": ticker, "token": self.api_key},
                timeout=10,
            )
            resp.raise_for_status()
            datos = resp.json().get("earningsCalendar", [])
        except (requests.RequestException, ValueError):
            return []
        fechas = []
        for item in datos:
            fecha_str = item.get("date")
            if not fecha_str:
                continue
            try:
                fechas.append(date.fromisoformat(fecha_str))
            except ValueError:
                continue
        return fechas


def ventana_busqueda_earnings(fecha_referencia: date, horas: int = 48) -> tuple[date, date]:
    dias = horas // 24 + 1
    return fecha_referencia, fecha_referencia + timedelta(days=dias)
