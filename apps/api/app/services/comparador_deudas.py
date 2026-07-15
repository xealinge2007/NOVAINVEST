"""Comparador de estrategias de pago de deuda (§3.2B.1): bola de nieve,
avalancha e híbrida. Simulación mes a mes con efecto cascada (el pago mínimo
de una deuda ya liquidada se suma al extra disponible del mes siguiente).

Para perfiles de deuda realistas (pago mínimo como fracción pequeña del
saldo, tipo tarjeta de crédito colombiana) avalancha paga igual o menos
interés total que nieve — verificado con 200 escenarios aleatorios y con el
caso de prueba de 3 deudas del criterio de aceptación de F1. **No es una ley
matemática universal**: con pagos mínimos anormalmente grandes frente al
saldo (creados a propósito en el stress test, no representativos de deuda
real), el orden de cuándo se libera cada pago mínimo puede hacer que nieve
gane por poco — el comparador lo maneja bien igual, porque `recomendada` se
calcula comparando los intereses reales de la corrida, nunca asumiendo cuál
estrategia "debería" ganar.
"""

MAX_MESES_SIMULACION = 600  # 50 años, tope de seguridad


def _orden_avalancha(deudas: list[dict]) -> list:
    return [d["id"] for d in sorted(deudas, key=lambda d: (-d["tasa_anual_pct"], d["saldo"]))]


def _orden_nieve(deudas: list[dict]) -> list:
    return [d["id"] for d in sorted(deudas, key=lambda d: (d["saldo"], -d["tasa_anual_pct"]))]


def _orden_hibrida(deudas: list[dict]) -> list:
    tasas = [d["tasa_anual_pct"] for d in deudas]
    saldos = [d["saldo"] for d in deudas]
    min_tasa, max_tasa = min(tasas), max(tasas)
    min_saldo, max_saldo = min(saldos), max(saldos)

    def score(d: dict) -> float:
        norm_tasa = (d["tasa_anual_pct"] - min_tasa) / (max_tasa - min_tasa) if max_tasa > min_tasa else 1.0
        norm_saldo_inv = (max_saldo - d["saldo"]) / (max_saldo - min_saldo) if max_saldo > min_saldo else 1.0
        return 0.5 * norm_tasa + 0.5 * norm_saldo_inv

    return [d["id"] for d in sorted(deudas, key=lambda d: (-score(d), d["saldo"]))]


def _simular(deudas: list[dict], orden: list, extra_mensual: float) -> dict:
    saldos = {d["id"]: float(d["saldo"]) for d in deudas}
    tasa_mensual = {d["id"]: d["tasa_anual_pct"] / 100 / 12 for d in deudas}
    minimo = {d["id"]: float(d["pago_minimo"]) for d in deudas}
    interes_total = {d["id"]: 0.0 for d in deudas}
    mes_liberacion = {}

    extra_actual = float(extra_mensual)
    activos = set(saldos.keys())
    mes = 0

    while activos and mes < MAX_MESES_SIMULACION:
        mes += 1
        for did in activos:
            interes = saldos[did] * tasa_mensual[did]
            interes_total[did] += interes
            saldos[did] += interes

        for did in list(activos):
            pago = min(saldos[did], minimo[did])
            saldos[did] -= pago

        for did in orden:
            if did in activos and saldos[did] > 1e-6:
                pago_extra = min(saldos[did], extra_actual)
                saldos[did] -= pago_extra
                break

        recien_pagadas = [did for did in activos if saldos[did] <= 1e-6]
        for did in recien_pagadas:
            activos.discard(did)
            mes_liberacion[did] = mes
            extra_actual += minimo[did]

    return {
        "meses_totales": mes,
        "sin_terminar": bool(activos),
        "interes_total": round(sum(interes_total.values()), 2),
        "interes_por_deuda": {did: round(v, 2) for did, v in interes_total.items()},
        "mes_liberacion_por_deuda": mes_liberacion,
        "orden_pago": orden,
    }


def comparar_estrategias(deudas: list[dict], extra_mensual: float) -> dict:
    if not deudas:
        raise ValueError("Se necesita al menos una deuda")
    if extra_mensual < 0:
        raise ValueError("extra_mensual no puede ser negativo")

    estrategias = {
        "avalancha": _orden_avalancha(deudas),
        "nieve": _orden_nieve(deudas),
        "hibrida": _orden_hibrida(deudas),
    }
    resultados = {nombre: _simular(deudas, orden, extra_mensual) for nombre, orden in estrategias.items()}

    interes_avalancha = resultados["avalancha"]["interes_total"]
    interes_nieve = resultados["nieve"]["interes_total"]
    recomendada = "nieve" if interes_nieve - interes_avalancha < 0.02 * interes_avalancha else "avalancha"

    return {
        "resultados": resultados,
        "recomendada": recomendada,
        "razon": (
            "La diferencia de intereses entre nieve y avalancha es pequeña (<2%) — "
            "la nieve gana por adherencia (criterio conductual)."
            if recomendada == "nieve"
            else "Avalancha ahorra intereses de forma significativa frente a nieve."
        ),
    }
