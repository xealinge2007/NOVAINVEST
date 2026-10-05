"""Semáforo de liquidez simplificado para F3 (§3.5, §3.7.6): antes de emitir
una señal diaria sobre un instrumento BVC se exige un monto promedio
negociado mínimo en las últimas 20 sesiones — sin él, un descuento grande
puede ser puro efecto de iliquidez, no una oportunidad real (regla de la
casa). El panel completo de liquidez (spread típico, días sin negociación,
tamaño máximo de posición) es de §3.7.6/F5; esto es solo el gate binario que
pide el criterio de aceptación de F3.

Piso elegido a criterio (documentado, no medido): 500M COP/día de monto
promedio negociado. Es conservador frente a los emisores más líquidos del
COLCAP (Ecopetrol negoció ~24.7M acciones x ~2.750 COP ≈ 68.000M COP en una
sola sesión medida el 01-sep-2026) pero deja fuera, a propósito, a las
especies de cola del índice — ajustable por Alex sin tocar el resto del
motor de señales.
"""

import pandas as pd

MIN_MONTO_NEGOCIADO_20D_COP = 500_000_000


def monto_promedio_negociado(df: pd.DataFrame, dias: int = 20) -> float | None:
    """Monto promedio negociado (volumen × cierre) en las últimas `dias`
    filas. None si no hay suficientes datos de volumen para calcularlo."""
    if df.empty or "volumen" not in df.columns or "cierre" not in df.columns:
        return None
    ventana = df.tail(dias)
    montos = ventana["volumen"] * ventana["cierre"]
    if montos.dropna().empty:
        return None
    return float(montos.mean())


def volumen_suficiente(df: pd.DataFrame, minimo_cop: float = MIN_MONTO_NEGOCIADO_20D_COP, dias: int = 20) -> bool:
    monto = monto_promedio_negociado(df, dias)
    return monto is not None and monto >= minimo_cop


# ---------------------------------------------------------------------------
# Puerta de liquidez del ranking de valor (decisión de Alex, 03-oct-2026). Distinta del gate de
# señales de arriba (que sigue en media >= 500 M): aquí importa cuánto se puede negociar un día
# CUALQUIERA, no el promedio que inflan unos pocos bloques (Promigas: media 1.462 M, mediana 311 M).
# ---------------------------------------------------------------------------
MIN_MEDIANA_VALOR_COP = 150_000_000
MIN_SESIONES_CON_NEGOCIACION = 18   # de las últimas 20
FACTOR_TAMANO_MAXIMO = 0.5          # 5 sesiones al 10 % de la mediana diaria


def liquidez_valor(df: pd.DataFrame, dias: int = 20) -> dict:
    """{ok, mediana_cop, sesiones_con_negociacion, sesiones, tamano_maximo_cop}. `df` con `volumen` y
    `cierre` de las últimas `dias` sesiones. Pasa si la mediana del monto negociado es >=
    `MIN_MEDIANA_VALOR_COP` y hubo negociación en al menos `MIN_SESIONES_CON_NEGOCIACION` sesiones.
    `tamano_maximo_cop` = `FACTOR_TAMANO_MAXIMO` x mediana: lo que se puede deshacer en ~5 sesiones sin
    pasar del 10 % del volumen diario."""
    vacio = {"ok": False, "mediana_cop": None, "sesiones_con_negociacion": 0, "sesiones": 0, "tamano_maximo_cop": None}
    if df is None or df.empty or "volumen" not in df.columns or "cierre" not in df.columns:
        return vacio
    ventana = df.head(dias) if len(df) > dias else df
    montos = (ventana["volumen"].fillna(0) * ventana["cierre"].fillna(0))
    mediana = float(montos.median())
    con_neg = int((ventana["volumen"].fillna(0) > 0).sum())
    ok = mediana >= MIN_MEDIANA_VALOR_COP and con_neg >= MIN_SESIONES_CON_NEGOCIACION
    return {"ok": ok, "mediana_cop": mediana, "sesiones_con_negociacion": con_neg, "sesiones": len(ventana),
            "tamano_maximo_cop": mediana * FACTOR_TAMANO_MAXIMO}
