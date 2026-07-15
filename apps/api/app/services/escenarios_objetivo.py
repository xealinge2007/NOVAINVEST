"""Cálculo de aporte mensual requerido en 3 escenarios (§3.3) y semáforo de
avance. Supuestos de retorno anual documentados aquí — F4 podrá refinarlos
con el ensamble de modelos, esto es la versión de arranque.
"""

from datetime import date

TASAS_ANUALES = {"pesimista": 0.03, "base": 0.07, "optimista": 0.12}


def _meses_entre(desde: date, hasta: date) -> int:
    return max(1, (hasta.year - desde.year) * 12 + (hasta.month - desde.month))


def aporte_mensual_requerido(monto_objetivo: float, monto_actual: float, fecha_objetivo: date, hoy: date) -> dict:
    n = _meses_entre(hoy, fecha_objetivo)
    resultado = {}
    for escenario, tasa_anual in TASAS_ANUALES.items():
        r_m = (1 + tasa_anual) ** (1 / 12) - 1
        fv_actual = monto_actual * (1 + r_m) ** n
        faltante = monto_objetivo - fv_actual
        if faltante <= 0:
            resultado[escenario] = 0.0
            continue
        if r_m == 0:
            pmt = faltante / n
        else:
            pmt = faltante / (((1 + r_m) ** n - 1) / r_m)
        resultado[escenario] = round(max(pmt, 0.0), 2)
    return resultado


def semaforo_avance(monto_objetivo: float, monto_actual: float, fecha_creacion: date, fecha_objetivo: date, hoy: date) -> str:
    total_meses = _meses_entre(fecha_creacion, fecha_objetivo)
    meses_transcurridos = _meses_entre(fecha_creacion, hoy) if hoy > fecha_creacion else 0
    avance_esperado_pct = min(1.0, meses_transcurridos / total_meses)
    avance_real_pct = monto_actual / monto_objetivo if monto_objetivo > 0 else 0

    if avance_esperado_pct == 0:
        return "verde"
    razon = avance_real_pct / avance_esperado_pct
    if razon >= 0.9:
        return "verde"
    if razon >= 0.6:
        return "amarillo"
    return "rojo"
