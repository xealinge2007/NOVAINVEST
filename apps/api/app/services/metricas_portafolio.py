"""Métricas de portafolio (§3.4): TWR, volatilidad, drawdown, Sharpe,
exposición COP/USD, concentración, correlaciones.

Simplificación documentada: no llevamos un ledger de transacciones (solo el
snapshot de posiciones vigentes), así que el "TWR" es un retorno simple
sobre el historial de precios disponible para las posiciones actuales, no
un cálculo de flujos de caja reales. Se declara en cada respuesta.
"""

import numpy as np
import pandas as pd

UMBRAL_CONCENTRACION_PCT = 15.0
DIAS_TRADING_ANIO = 252


def _serie_valor_portafolio(posiciones: list[dict], historial_precios: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = {}
    for pos in posiciones:
        ticker = pos["ticker"]
        df = historial_precios.get(ticker)
        if df is None or df.empty:
            continue
        s = df.set_index("fecha")["cierre"] * pos["cantidad"]
        series[ticker] = s
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).dropna(how="any")


def calcular_metricas(posiciones: list[dict], historial_precios: dict[str, pd.DataFrame]) -> dict:
    valores = _serie_valor_portafolio(posiciones, historial_precios)
    if valores.empty or len(valores) < 5:
        return {"suficiente_historial": False, "detalle": "Menos de 5 días de historial común entre las posiciones."}

    valor_total = valores.sum(axis=1)
    retornos = valor_total.pct_change().dropna()

    twr_aproximado = (valor_total.iloc[-1] / valor_total.iloc[0]) - 1
    volatilidad_anualizada = retornos.std() * np.sqrt(DIAS_TRADING_ANIO) if len(retornos) > 1 else None
    cummax = valor_total.cummax()
    drawdown = valor_total / cummax - 1
    max_drawdown = drawdown.min()
    sharpe = (
        (retornos.mean() * DIAS_TRADING_ANIO) / volatilidad_anualizada
        if volatilidad_anualizada and volatilidad_anualizada > 0
        else None
    )

    ultimo_valor_por_ticker = valores.iloc[-1]
    total_actual = ultimo_valor_por_ticker.sum()
    concentracion = {
        ticker: round(float(v / total_actual * 100), 2) for ticker, v in ultimo_valor_por_ticker.items()
    }
    alertas_concentracion = [t for t, pct in concentracion.items() if pct > UMBRAL_CONCENTRACION_PCT]

    exposicion_moneda = {"COP": 0.0, "USD": 0.0}
    mapa_moneda = {p["ticker"]: p.get("moneda_compra", "COP") for p in posiciones}
    for ticker, v in ultimo_valor_por_ticker.items():
        moneda = mapa_moneda.get(ticker, "COP")
        exposicion_moneda[moneda] = exposicion_moneda.get(moneda, 0.0) + float(v)
    if total_actual > 0:
        exposicion_moneda_pct = {k: round(v / total_actual * 100, 2) for k, v in exposicion_moneda.items()}
    else:
        exposicion_moneda_pct = exposicion_moneda

    correlaciones = None
    if valores.shape[1] >= 2:
        matriz = valores.pct_change().dropna().corr().round(3)
        correlaciones = matriz.to_dict()

    return {
        "suficiente_historial": True,
        "dias_historial_comun": len(valores),
        "twr_aproximado_pct": round(float(twr_aproximado) * 100, 2),
        "volatilidad_anualizada_pct": round(float(volatilidad_anualizada) * 100, 2) if volatilidad_anualizada else None,
        "drawdown_maximo_pct": round(float(max_drawdown) * 100, 2),
        "sharpe_aproximado": round(float(sharpe), 2) if sharpe is not None else None,
        "concentracion_pct_por_ticker": concentracion,
        "alertas_concentracion": alertas_concentracion,
        "exposicion_moneda_pct": exposicion_moneda_pct,
        "correlaciones": correlaciones,
        "nota": "TWR aproximado sobre el historial de precios disponible, no sobre flujos de caja reales (no hay ledger de transacciones aún).",
    }
