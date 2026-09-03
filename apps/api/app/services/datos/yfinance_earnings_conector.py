"""Conector de fechas de resultados vía yfinance (F3 §11: sustituye a
Finnhub en el filtro de cuarentena de señales — verificado 01-sep-2026:
yfinance entrega esto gratis y sin key, incluso para tickers `.CL` de la
BVC). Finnhub queda disponible para F6 (titulares de noticias), pero deja de
ser una dependencia del motor de señales.

Se usa `Ticker.calendar["Earnings Date"]` en vez de `Ticker.get_earnings_dates()`:
el segundo mezcla el historial con huecos de cobertura reales — probado con
ISA.CL, que salta de la próxima fecha (2026-11-02, correcta) directo a fechas
de 2011/2010 en el historial, sin nada entre medio. `.calendar` solo trae la
próxima fecha esperada, así que ese salto no puede colarse. Aun así se aplica
un filtro de cordura (`HORIZONTE_MAX_DIAS`) como segunda barrera — "validar
contra el calendario local" que pide el plan: una fecha de resultados
"próxima" que caiga muy en el pasado o muy lejos en el futuro se descarta en
vez de usarse a ciegas.
"""

from datetime import date, timedelta

import yfinance as yf

HORIZONTE_MAX_DIAS = 400  # una fecha de earnings "próxima" no debería estar a más de ~13 meses


class YfinanceEarningsConector:
    nombre = "yfinance_earnings"

    def disponible(self) -> bool:
        return True  # sin API key: siempre se puede intentar

    def proximos_earnings(self, ticker: str, desde: date, hasta: date) -> list[date]:
        """Fechas de earnings esperadas para `ticker` dentro de [desde, hasta].
        Lista vacía si no hay, si la fuente falla, o si la única fecha que
        trae cae fuera de una ventana razonable (cobertura irregular
        conocida) — nunca se propaga la excepción: el filtro de noticias
        debe degradar, no tumbar la generación de señales.
        """
        try:
            calendario = yf.Ticker(ticker).calendar
        except Exception:
            return []
        if not calendario:
            return []
        fechas_crudas = calendario.get("Earnings Date") or []

        hoy = date.today()
        fechas = []
        for f in fechas_crudas:
            if not isinstance(f, date):
                continue
            if f < hoy - timedelta(days=2) or f > hoy + timedelta(days=HORIZONTE_MAX_DIAS):
                continue  # fuera de ventana razonable: se descarta, no se usa a ciegas
            if desde <= f <= hasta:
                fechas.append(f)
        return fechas


def ventana_busqueda_earnings(fecha_referencia: date, horas: int = 48) -> tuple[date, date]:
    dias = horas // 24 + 1
    return fecha_referencia, fecha_referencia + timedelta(days=dias)
