"""Backtest de la regla de confluencia (§3.5: "backtest obligatorio con
vectorbt (≥3 años, ≥30 trades, neto de fricción) antes de habilitar cada
regla"). Import de vectorbt es perezoso (dentro de la función) porque esta
dependencia NO vive en `apps/api/requirements.txt` — solo la usa el job
`jobs/backtest_reglas.py` (ver ese archivo y `jobs/requirements_backtest.txt`
para el porqué: vectorbt/numba son pesados y este servicio nunca corre
dentro del proceso web de Render).

Nota de diseño — por qué el score aquí NO es el mismo `score_confluencia.py`
bar a bar: ese módulo usa `estructura_mercado.detectar_estructura`, que se
apoya en pivotes con ventana CENTRADA (`indicadores.pivotes`, `center=True`).
Un pivote en la barra i solo se confirma con datos hasta i+ventana — correcto
en vivo (nunca se usa una barra que aún no existe), pero si se corriera igual
sobre todo el histórico de una sola vez para backtestear, en las barras
cercanas al "presente" de cada punto de decisión se estaría usando
información del futuro (look-ahead bias). Por eso la estructura de este
backtest se calcula con ventanas TRAILING (`rolling` sin centrar + `shift`),
100% causales, en vez de reusar `estructura_mercado` tal cual. Se documenta
como simplificación deliberada, no como bug.
"""

import numpy as np
import pandas as pd

from app.services.indicadores import ema, macd, rsi, volumen_relativo

UMBRAL_ENTRADA = 60
UMBRAL_SALIDA = 20
MIN_TRADES_CONFIABLE = 30
VENTANA_ESTRUCTURA_CAUSAL = 10


def _estructura_causal(df: pd.DataFrame, ventana: int = VENTANA_ESTRUCTURA_CAUSAL) -> pd.Series:
    """+25 alcista / -25 bajista / 0 indefinida, por barra, sin look-ahead:
    compara el máximo/mínimo de los últimos `ventana` bloques de `ventana`
    barras contra el bloque anterior (proxy causal de HH/HL vs LH/LL).
    """
    alto_trailing = df["alto"].rolling(ventana).max()
    bajo_trailing = df["bajo"].rolling(ventana).min()
    alto_prev = alto_trailing.shift(ventana)
    bajo_prev = bajo_trailing.shift(ventana)
    alcista = (alto_trailing > alto_prev) & (bajo_trailing > bajo_prev)
    bajista = (alto_trailing < alto_prev) & (bajo_trailing < bajo_prev)
    return pd.Series(np.where(alcista, 25.0, np.where(bajista, -25.0, 0.0)), index=df.index)


def calcular_score_serie(df: pd.DataFrame) -> pd.Series:
    """Score −100..100 vectorizado sobre todo el histórico (para backtest).
    Mismos pesos que `score_confluencia.calcular_score` (30/25/20/15/10).
    """
    cierre = df["cierre"]
    ema_20, ema_50, ema_200 = ema(cierre, 20), ema(cierre, 50), ema(cierre, 200)

    alineadas = pd.concat([cierre > ema_20, ema_20 > ema_50, ema_50 > ema_200], axis=1).sum(axis=1)
    score_tendencia = pd.Series(np.select([alineadas == 3, alineadas == 0], [30.0, -30.0], default=(alineadas - 1.5) * 20.0), index=df.index)

    score_estructura = _estructura_causal(df)

    macd_df = macd(cierre)
    score_macd = pd.Series(
        np.select(
            [
                (macd_df["macd"] > macd_df["señal"]) & (macd_df["histograma"] > 0),
                (macd_df["macd"] < macd_df["señal"]) & (macd_df["histograma"] < 0),
            ],
            [20.0, -20.0],
            default=0.0,
        ),
        index=df.index,
    )

    rsi_14 = rsi(cierre, 14)
    score_rsi = pd.Series(
        np.select([(rsi_14 >= 80) | (rsi_14 <= 20), rsi_14 > 55, rsi_14 < 45], [0.0, 15.0, -15.0], default=0.0),
        index=df.index,
    )

    sin_volumen = score_tendencia + score_estructura + score_macd + score_rsi
    vol_rel = volumen_relativo(df, 20)
    score_volumen = pd.Series(
        np.select(
            [(vol_rel >= 1.5) & (sin_volumen > 0), (vol_rel >= 1.5) & (sin_volumen < 0), (vol_rel < 0.7) & (sin_volumen > 0), (vol_rel < 0.7) & (sin_volumen < 0)],
            [10.0, -10.0, -5.0, 5.0],
            default=0.0,
        ),
        index=df.index,
    )

    return (sin_volumen + score_volumen).clip(-100, 100)


def correr_backtest(
    df: pd.DataFrame,
    regla: str,
    fees_pct: float = 0.001,
    slippage_pct: float = 0.0005,
    capital_inicial: float = 10_000_000,
) -> dict:
    """`regla` es 'confluencia_largo' o 'confluencia_corto'. Devuelve las
    métricas listas para insertar en la tabla `backtests`, incluyendo
    `habilitada` (bool) — la regla se auto-deshabilita si hay menos de
    `MIN_TRADES_CONFIABLE` trades (muestra insuficiente) o si la expectativa
    neta de fricción es <= 0.
    """
    import vectorbt as vbt  # import perezoso: ver docstring del módulo

    if regla not in ("confluencia_largo", "confluencia_corto"):
        raise ValueError("regla debe ser 'confluencia_largo' o 'confluencia_corto'")

    score = calcular_score_serie(df)
    cierre = df["cierre"]

    if regla == "confluencia_largo":
        entradas = score >= UMBRAL_ENTRADA
        salidas = score < UMBRAL_SALIDA
    else:
        entradas = score <= -UMBRAL_ENTRADA
        salidas = score > -UMBRAL_SALIDA

    valido = score.notna()
    entradas, salidas = entradas & valido, salidas & valido

    pf = vbt.Portfolio.from_signals(
        cierre,
        entradas,
        salidas,
        direction="longonly" if regla == "confluencia_largo" else "shortonly",
        fees=fees_pct,
        slippage=slippage_pct,
        init_cash=capital_inicial,
    )

    n_trades = int(pf.trades.count())
    if n_trades == 0:
        return {
            "n_trades": 0, "win_rate_pct": None, "expectancy": None, "retorno_neto_pct": None,
            "max_drawdown_pct": None, "habilitada": False, "motivo": "cero trades generados en el período",
        }

    win_rate = float(pf.trades.win_rate()) * 100
    expectancy = float(pf.trades.expectancy())
    retorno_neto_pct = float(pf.total_return()) * 100
    max_dd_pct = float(pf.max_drawdown()) * 100

    if n_trades < MIN_TRADES_CONFIABLE:
        habilitada, motivo = False, f"muestra insuficiente: {n_trades} trades (mínimo {MIN_TRADES_CONFIABLE})"
    elif expectancy <= 0:
        habilitada, motivo = False, f"expectativa negativa neta de fricción: {expectancy:.2f} por trade"
    else:
        habilitada, motivo = True, f"{n_trades} trades, expectativa positiva ({expectancy:.2f}/trade)"

    return {
        "n_trades": n_trades,
        "win_rate_pct": round(win_rate, 2),
        "expectancy": round(expectancy, 4),
        "retorno_neto_pct": round(retorno_neto_pct, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "habilitada": habilitada,
        "motivo": motivo,
    }
