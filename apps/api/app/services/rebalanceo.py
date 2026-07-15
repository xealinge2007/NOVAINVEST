"""Asignación estratégica por perfil (§3.4) y rebalanceo por bandas neto de
fricción colombiana (GMF 4×1000 + comisión de broker, parametrizables).
"""

ASIGNACION_POR_PERFIL = {
    "conservador": {"renta_fija": 70, "etf_global": 20, "acciones": 0, "cripto": 0, "efectivo": 10},
    "moderado": {"renta_fija": 50, "etf_global": 30, "acciones": 10, "cripto": 5, "efectivo": 5},
    "crecimiento": {"renta_fija": 30, "etf_global": 40, "acciones": 20, "cripto": 5, "efectivo": 5},
    "agresivo": {"renta_fija": 15, "etf_global": 45, "acciones": 30, "cripto": 10, "efectivo": 0},
}

MAPA_CLASE_A_GRUPO = {
    "renta_fija": "renta_fija",
    "fx": "renta_fija",
    "etf": "etf_global",
    "indice_proxy": "etf_global",
    "accion": "acciones",
    "cripto": "cripto",
    "efectivo": "efectivo",
}

BANDA_PCT = 5.0
GMF_PCT_DEFAULT = 0.004  # 4x1000
COMISION_PCT_DEFAULT = 0.001  # 0.1%, parametrizable por broker


def _valor_actual(posicion: dict, precio_actual: float | None) -> float:
    precio = precio_actual if precio_actual is not None else posicion["precio_promedio_compra"]
    return posicion["cantidad"] * precio


def calcular_asignacion_actual(posiciones: list[dict], precios_actuales: dict[str, float]) -> dict:
    """Solo posiciones de horizonte 'largo' entran a la asignación estratégica
    (corto plazo es un cajón aparte, sin renta variable — §3.4)."""
    valor_por_grupo = {g: 0.0 for g in ASIGNACION_POR_PERFIL["moderado"]}
    for pos in posiciones:
        if pos.get("horizonte") != "largo":
            continue
        grupo = MAPA_CLASE_A_GRUPO[pos["clase"]]
        valor_por_grupo[grupo] += _valor_actual(pos, precios_actuales.get(pos["ticker"]))

    total = sum(valor_por_grupo.values())
    if total == 0:
        return {"total": 0, "valor_por_grupo": valor_por_grupo, "pct_por_grupo": {g: 0 for g in valor_por_grupo}}
    pct_por_grupo = {g: round(v / total * 100, 2) for g, v in valor_por_grupo.items()}
    return {"total": total, "valor_por_grupo": valor_por_grupo, "pct_por_grupo": pct_por_grupo}


def generar_ordenes_rebalanceo(
    posiciones: list[dict],
    precios_actuales: dict[str, float],
    perfil: str,
    comision_pct: float = COMISION_PCT_DEFAULT,
    gmf_pct: float = GMF_PCT_DEFAULT,
) -> dict:
    if perfil not in ASIGNACION_POR_PERFIL:
        raise ValueError(f"Perfil desconocido: {perfil}")

    target = ASIGNACION_POR_PERFIL[perfil]
    actual = calcular_asignacion_actual(posiciones, precios_actuales)
    total = actual["total"]

    desviaciones = {g: round(actual["pct_por_grupo"][g] - target[g], 2) for g in target}
    grupos_desviados = {g: d for g, d in desviaciones.items() if abs(d) > BANDA_PCT}

    ordenes = []
    for grupo, desviacion_pct in grupos_desviados.items():
        monto_objetivo = target[grupo] / 100 * total
        monto_actual_grupo = actual["valor_por_grupo"][grupo]
        diferencia = monto_objetivo - monto_actual_grupo  # >0 = falta comprar, <0 = sobra (vender)

        if diferencia < 0:
            bruto = abs(diferencia)
            neto = bruto * (1 - comision_pct - gmf_pct)
            ordenes.append(
                {
                    "grupo": grupo,
                    "accion": "vender",
                    "desviacion_pct": desviacion_pct,
                    "monto_bruto": round(bruto, 2),
                    "friccion": round(bruto - neto, 2),
                    "monto_neto": round(neto, 2),
                }
            )
        else:
            bruto = diferencia
            costo_total = bruto * (1 + comision_pct)  # el GMF no aplica típicamente a la compra en sí
            ordenes.append(
                {
                    "grupo": grupo,
                    "accion": "comprar",
                    "desviacion_pct": desviacion_pct,
                    "monto_bruto": round(bruto, 2),
                    "friccion": round(costo_total - bruto, 2),
                    "monto_neto": round(costo_total, 2),
                }
            )

    return {
        "asignacion_actual_pct": actual["pct_por_grupo"],
        "asignacion_objetivo_pct": target,
        "desviaciones_pct": desviaciones,
        "banda_pct": BANDA_PCT,
        "requiere_rebalanceo": bool(ordenes),
        "ordenes": ordenes,
        "friccion_aplicada": {"comision_pct": comision_pct, "gmf_pct": gmf_pct},
    }
