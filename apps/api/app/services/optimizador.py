"""Optimizador de frontera eficiente (§3.4): herramienta de análisis, nunca
orden automática — el usuario decide qué hacer con la sugerencia.
"""

import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models


def optimizar(historial_precios: dict[str, pd.DataFrame], meta: str = "max_sharpe") -> dict:
    if meta not in ("max_sharpe", "min_volatilidad"):
        raise ValueError("meta debe ser 'max_sharpe' o 'min_volatilidad'")

    series = {t: df.set_index("fecha")["cierre"] for t, df in historial_precios.items() if not df.empty}
    if len(series) < 2:
        raise ValueError("Se necesitan al menos 2 activos con historial de precios")

    precios = pd.DataFrame(series).dropna(how="any")
    if len(precios) < 30:
        raise ValueError("Se necesitan al menos 30 días de historial común entre los activos")

    mu = expected_returns.mean_historical_return(precios)
    S = risk_models.sample_cov(precios)
    ef = EfficientFrontier(mu, S)

    if meta == "max_sharpe":
        ef.max_sharpe()
    else:
        ef.min_volatility()

    pesos = ef.clean_weights()
    retorno_esperado, volatilidad, sharpe = ef.portfolio_performance()

    return {
        "meta": meta,
        "pesos_sugeridos_pct": {t: round(w * 100, 2) for t, w in pesos.items() if w > 0.0001},
        "retorno_esperado_anual_pct": round(retorno_esperado * 100, 2),
        "volatilidad_anual_pct": round(volatilidad * 100, 2),
        "sharpe_esperado": round(sharpe, 2),
        "nota": "Herramienta de análisis (frontera eficiente sobre el historial disponible) — nunca es una orden automática.",
    }
