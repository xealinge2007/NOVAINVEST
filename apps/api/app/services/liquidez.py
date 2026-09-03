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
