"""Monte Carlo del plan de vida (§8B.2): probabilidad de alcanzar cada
objetivo y sensibilidad (aportar más / más riesgo / correr la fecha).

Supuestos de retorno/volatilidad anual por clase de activo — documentados
aquí como punto de partida; F4 los podrá calibrar con el ensamble de
modelos del §6. La correlación entre clases se aproxima con un valor fijo
(no hay matriz de covarianza real entre clases todavía).
"""

import numpy as np

SUPUESTOS_CLASE = {
    "renta_fija": {"retorno_anual": 0.06, "vol_anual": 0.04},
    "etf_global": {"retorno_anual": 0.09, "vol_anual": 0.15},
    "acciones": {"retorno_anual": 0.11, "vol_anual": 0.25},
    "cripto": {"retorno_anual": 0.25, "vol_anual": 0.65},
    "efectivo": {"retorno_anual": 0.03, "vol_anual": 0.01},
}
CORRELACION_APROXIMADA_ENTRE_CLASES = 0.3
N_SIMULACIONES = 5000


def _retorno_y_vol_portafolio(asignacion_pct: dict) -> tuple[float, float]:
    pesos = {c: p / 100 for c, p in asignacion_pct.items()}
    retorno = sum(pesos[c] * SUPUESTOS_CLASE[c]["retorno_anual"] for c in pesos)

    varianza = 0.0
    clases = list(pesos.keys())
    for c in clases:
        varianza += (pesos[c] ** 2) * (SUPUESTOS_CLASE[c]["vol_anual"] ** 2)
    for i in range(len(clases)):
        for j in range(i + 1, len(clases)):
            ci, cj = clases[i], clases[j]
            varianza += (
                2
                * pesos[ci]
                * pesos[cj]
                * CORRELACION_APROXIMADA_ENTRE_CLASES
                * SUPUESTOS_CLASE[ci]["vol_anual"]
                * SUPUESTOS_CLASE[cj]["vol_anual"]
            )
    return retorno, max(varianza, 0.0) ** 0.5


def simular_probabilidad(
    monto_actual: float,
    monto_objetivo: float,
    aporte_mensual: float,
    meses: int,
    asignacion_pct: dict,
    n_simulaciones: int = N_SIMULACIONES,
    semilla: int | None = None,
) -> dict:
    if meses <= 0:
        return {"probabilidad_pct": 100.0 if monto_actual >= monto_objetivo else 0.0, "meses": meses}

    retorno_anual, vol_anual = _retorno_y_vol_portafolio(asignacion_pct)
    mu_m = retorno_anual / 12
    sigma_m = vol_anual / np.sqrt(12)

    rng = np.random.default_rng(semilla)
    retornos = rng.normal(mu_m, sigma_m, size=(n_simulaciones, meses))

    valores = np.full(n_simulaciones, monto_actual, dtype=float)
    for mes in range(meses):
        valores = valores * (1 + retornos[:, mes]) + aporte_mensual

    exitos = np.sum(valores >= monto_objetivo)
    probabilidad_pct = round(exitos / n_simulaciones * 100, 1)

    return {
        "probabilidad_pct": probabilidad_pct,
        "meses": meses,
        "retorno_anual_supuesto_pct": round(retorno_anual * 100, 2),
        "vol_anual_supuesta_pct": round(vol_anual * 100, 2),
        "valor_mediano_final": round(float(np.median(valores)), 2),
        "valor_p10_final": round(float(np.percentile(valores, 10)), 2),
        "valor_p90_final": round(float(np.percentile(valores, 90)), 2),
        "n_simulaciones": n_simulaciones,
    }


def sensibilidad(
    monto_actual: float,
    monto_objetivo: float,
    aporte_mensual: float,
    meses: int,
    asignacion_pct: dict,
    asignacion_mas_riesgo: dict,
) -> dict:
    base = simular_probabilidad(monto_actual, monto_objetivo, aporte_mensual, meses, asignacion_pct, semilla=42)
    mas_aporte = simular_probabilidad(monto_actual, monto_objetivo, aporte_mensual + 200_000, meses, asignacion_pct, semilla=42)
    mas_riesgo = simular_probabilidad(monto_actual, monto_objetivo, aporte_mensual, meses, asignacion_mas_riesgo, semilla=42)
    mas_tiempo = simular_probabilidad(monto_actual, monto_objetivo, aporte_mensual, meses + 12, asignacion_pct, semilla=42)

    return {
        "base": base,
        "aportar_200k_mas": {"probabilidad_pct": mas_aporte["probabilidad_pct"], "delta_pp": round(mas_aporte["probabilidad_pct"] - base["probabilidad_pct"], 1)},
        "un_nivel_mas_de_riesgo": {"probabilidad_pct": mas_riesgo["probabilidad_pct"], "delta_pp": round(mas_riesgo["probabilidad_pct"] - base["probabilidad_pct"], 1)},
        "correr_fecha_un_anio": {"probabilidad_pct": mas_tiempo["probabilidad_pct"], "delta_pp": round(mas_tiempo["probabilidad_pct"] - base["probabilidad_pct"], 1)},
        "nota": "Supuestos de retorno/volatilidad por clase documentados en monte_carlo_metas.py — punto de partida, no el ensamble de modelos completo (eso es F4).",
    }
