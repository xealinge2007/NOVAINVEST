"""Score de confluencia −100…+100 (§3.5): combina tendencia (EMA), estructura
de mercado, MACD, RSI y volumen relativo en un solo número con signo. Solo se
genera señal si |score| ≥ 60 (`UMBRAL_SEÑAL`).

Pesos (suman 100 en cada dirección): tendencia EMA 30, estructura 25, MACD 20,
RSI 15, volumen 10. Son pesos declarados a mano, no calibrados — el backtest
por regla (`backtest_regla.py`) es lo que decide si la regla resultante tiene
expectativa positiva, no este score en sí mismo.
"""

UMBRAL_SEÑAL = 60


def _score_tendencia_ema(cierre: float, ema_20: float, ema_50: float, ema_200: float) -> float:
    if cierre > ema_20 > ema_50 > ema_200:
        return 30.0
    if cierre < ema_20 < ema_50 < ema_200:
        return -30.0
    # alineación parcial: cuenta cuántas de las 3 comparaciones apuntan igual
    señales = [cierre > ema_20, ema_20 > ema_50, ema_50 > ema_200]
    alcistas = sum(señales)
    if alcistas == 3:
        return 30.0
    if alcistas == 0:
        return -30.0
    return (alcistas - 1.5) * (30.0 / 1.5)  # -15, 0 o +15 según cuántas coincidan


def _score_estructura(estructura: str) -> float:
    return {"hh_hl": 25.0, "lh_ll": -25.0}.get(estructura, 0.0)


def _score_macd(macd_valor: float, macd_señal: float, macd_histograma: float) -> float:
    if macd_valor > macd_señal and macd_histograma > 0:
        return 20.0
    if macd_valor < macd_señal and macd_histograma < 0:
        return -20.0
    return 0.0


def _score_rsi(rsi_valor: float) -> float:
    if rsi_valor >= 80 or rsi_valor <= 20:
        return 0.0  # sobrecompra/sobreventa extrema: no sumar momentum, evita perseguir el movimiento
    if rsi_valor > 55:
        return 15.0
    if rsi_valor < 45:
        return -15.0
    return 0.0


def _score_volumen(volumen_relativo: float, direccion_previa: float) -> float:
    if volumen_relativo is None or volumen_relativo != volumen_relativo:  # NaN
        return 0.0
    if volumen_relativo >= 1.5:
        return 10.0 if direccion_previa > 0 else -10.0 if direccion_previa < 0 else 0.0
    if volumen_relativo < 0.7:
        return -5.0 if direccion_previa > 0 else 5.0 if direccion_previa < 0 else 0.0
    return 0.0


def calcular_score(fila: dict, estructura: str) -> dict:
    """`fila` es la última fila de `indicadores.calcular_indicadores` como dict
    (cierre, ema_20, ema_50, ema_200, rsi_14, macd, macd_señal, macd_histograma,
    volumen_relativo). Devuelve el score total, el desglose y la dirección.
    """
    parcial_tendencia = _score_tendencia_ema(fila["cierre"], fila["ema_20"], fila["ema_50"], fila["ema_200"])
    parcial_estructura = _score_estructura(estructura)
    parcial_macd = _score_macd(fila["macd"], fila["macd_señal"], fila["macd_histograma"])
    parcial_rsi = _score_rsi(fila["rsi_14"])

    acumulado_sin_volumen = parcial_tendencia + parcial_estructura + parcial_macd + parcial_rsi
    parcial_volumen = _score_volumen(fila.get("volumen_relativo"), acumulado_sin_volumen)

    score_total = acumulado_sin_volumen + parcial_volumen
    score_total = max(-100.0, min(100.0, score_total))

    return {
        "score": round(score_total, 2),
        "direccion": "largo" if score_total > 0 else "corto" if score_total < 0 else None,
        "desglose": {
            "tendencia_ema": parcial_tendencia,
            "estructura": parcial_estructura,
            "macd": parcial_macd,
            "rsi": parcial_rsi,
            "volumen": parcial_volumen,
        },
        "cumple_umbral": abs(score_total) >= UMBRAL_SEÑAL,
    }


def timeframe_superior_confirma(score_menor: float, score_mayor: float | None) -> bool:
    """La señal del timeframe menor (4h) es válida si el timeframe superior
    (1D) no la contradice: mismo signo, o el superior está neutral (<20 en
    valor absoluto). Sin dato del timeframe superior, no se puede confirmar
    ni contradecir — se deja pasar (la señal 1D en sí no tiene superior).
    """
    if score_mayor is None:
        return True
    if abs(score_mayor) < 20:
        return True
    return (score_menor > 0) == (score_mayor > 0)
