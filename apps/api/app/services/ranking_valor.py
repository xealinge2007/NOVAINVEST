# -*- coding: utf-8 -*-
"""Ranking por puertas secuenciales (P3, A10 de la auditoría). Lógica pura, sin base de datos.

Puerta 0  liquidez            -- no pasa => excluido
Puerta 1  integridad de datos -- alerta abierta => excluido
Puerta 2  seguridad (Whitman) -- reprueba => excluido ("no invertible"); no evaluable => sigue, marcado
Puerta 3  valor determinable  -- sin valor por acción => excluido
Luego: margen de seguridad del valor central contra el precio, catalizador (Greenblatt) y renta
(Bazin: rendimiento por dividendo >= 6 % con payout <= 100 %).

No es un score promedio que licúe todo: un emisor excluido NO entra al ranking, y la lista de
excluidos con su motivo es parte del producto. Sin backtest: no es una recomendación de compra.
"""

from app.services.liquidez import MIN_MEDIANA_VALOR_COP as LIQUIDEZ_MINIMA_COP  # puerta 0, una sola fuente

UMBRAL_BARATA_PCT = 20.0     # margen de seguridad central mínimo para llamarla "barata"
RENTA_YIELD_MINIMO_PCT = 6.0
RENTA_PAYOUT_MAXIMO_PCT = 100.0
UMBRAL_CAMBIO_VALOR_PCT = 0.5       # por debajo de esto el valor base "no cambió"
ALERTA_LIQUIDEZ = "no pasa la puerta de liquidez"
# Resultados más viejos que el balance por más de esto (en trimestres) = datos desfasados (Codex H7).
DESFASE_MAXIMO_TRIMESTRES = 4
RUTAS_QUE_DEPENDEN_DE_RESULTADOS = ("activos_epv", "banco")

# Categorías descriptivas (Codex P2.4). Dicen qué se verificó, no qué hacer: ninguna es una recomendación.
#   descuento_con_soporte  pasa seguridad, margen >= 20 % y hay catalizador vivo o renta sostenible
#   descuento_sin_soporte  pasa seguridad y margen >= 20 %, pero sin catalizador ni renta sostenible
#   sin_descuento          pasa seguridad y el margen es menor al umbral
#   seguridad_no_evaluada  falta evidencia de seguridad: nunca es una categoría favorable
CON_SOPORTE, SIN_SOPORTE, SIN_DESCUENTO, NO_EVALUADA = (
    "descuento_con_soporte", "descuento_sin_soporte", "sin_descuento", "seguridad_no_evaluada")
ORDEN_CUADRANTE = {CON_SOPORTE: 0, NO_EVALUADA: 1, SIN_SOPORTE: 2, SIN_DESCUENTO: 3}
# Nombres anteriores (filas ya guardadas) -> nombres vigentes.
CUADRANTE_LEGADO = {"safe_cheap": CON_SOPORTE, "trampa_descuento": SIN_SOPORTE, "safe_cara": SIN_DESCUENTO}
CUADRANTE_A_LEGADO = {v: k for k, v in CUADRANTE_LEGADO.items()}  # para una base sin migrate_p6
# score_valor conserva el esquema del plan (migrate_w1_valor.sql).
CUADRANTE_A_SCORE_VALOR = {CON_SOPORTE: "safe_cheap", SIN_SOPORTE: "trampa_descuento", SIN_DESCUENTO: "safe_cara"}

# Horizonte del retorno ilustrativo: un supuesto de la casa, no un pronóstico (Codex H1 / P2.2).
HORIZONTE_ILUSTRATIVO_ANIOS = 3


def _excluido(puerta, motivo):
    return {"excluido": True, "puerta_fallida": puerta, "motivo_exclusion": motivo, "cuadrante": None,
            "tamano_relativo": None, "nivel_evidencia": None}


def evaluar(e: dict, ignorar_liquidez: bool = False) -> dict:
    """Veredicto de un emisor. `e` trae: elegible, motivo_no_elegible, alerta_datos, pilar1 (bool|None),
    pilar1_motivo, valor ({determinable, motivo, margen_seguridad_pct, confianza}),
    catalizador_nivel, dividend_yield_pct, payout_pct."""
    # `ignorar_liquidez` arma el ranking aparte sin la puerta 0 (decisión de Alex, 6-oct-2026): las demás puertas siguen igual y la
    # liquidez pasa a ser un riesgo visible (`riesgos_de`), no un filtro.
    if e.get("elegible") is False and not ignorar_liquidez:
        return _excluido("liquidez", e.get("motivo_no_elegible") or "no pasa la puerta de liquidez")
    alerta = (e.get("alerta_datos") or "").replace(ALERTA_LIQUIDEZ, "").strip(" |")  # la alerta de liquidez no es de datos
    if alerta:
        return _excluido("datos", f"alerta de datos abierta: {alerta[:160]}")
    if e.get("pilar1") is False:
        return _excluido("seguridad", f"no invertible: {e.get('pilar1_motivo') or 'reprueba la puerta de seguridad'}")
    valor = e.get("valor") or {}
    if not valor.get("determinable"):
        return _excluido("valor", valor.get("motivo") or "sin valor por acción determinable")

    # Integridad temporal (Codex H7): si los resultados son mucho más viejos que el balance, una
    # valoración que depende de resultados no se rankea; en las demás rutas la renta queda no evaluable.
    desfase = e.get("desfase_resultados_trimestres")
    desfasado = desfase is not None and desfase > DESFASE_MAXIMO_TRIMESTRES
    if desfasado and e.get("ruta_valor") in RUTAS_QUE_DEPENDEN_DE_RESULTADOS:
        return _excluido("datos", f"resultados {desfase} trimestres más viejos que el balance")

    margen = valor.get("margen_seguridad_pct")
    barata = margen is not None and margen >= UMBRAL_BARATA_PCT
    yld, payout = e.get("dividend_yield_pct"), e.get("payout_pct")
    # Renta sostenible exige payout conocido (Codex H4): sin él, la renta es no evaluable, nunca favorable.
    renta = (not desfasado and yld is not None and payout is not None
             and yld >= RENTA_YIELD_MINIMO_PCT and payout <= RENTA_PAYOUT_MAXIMO_PCT)
    vivo = e.get("catalizador_nivel") in ("fuerte", "debil")

    if e.get("pilar1") is not True:
        # Sin seguridad evaluada no hay cuadrante favorable (Codex H4).
        cuadrante = NO_EVALUADA
    elif not barata:
        cuadrante = SIN_DESCUENTO
    elif vivo or renta:
        cuadrante = CON_SOPORTE
    else:
        cuadrante = SIN_SOPORTE

    # Sin tamaño de posición ligado al cuadrante (Codex P2.5): sin perfil ni cartera del usuario sería una
    # recomendación personal. Lo único que se muestra es el límite de liquidez del mercado.
    nivel = "provisional" if valor.get("confianza") == "baja" else "estructura"
    return {"excluido": False, "puerta_fallida": None, "motivo_exclusion": None, "cuadrante": cuadrante,
            "tamano_relativo": None, "renta_sostenible": renta, "barata": barata, "nivel_evidencia": nivel,
            "riesgos": riesgos_de(e, nivel, desfase if desfasado else None)}


def riesgos_de(e: dict, nivel_evidencia: str, desfase: int | None) -> list[dict]:
    """Riesgos que acompañan a la categoría (Codex P2.4): datos, deuda y liquidez, cada uno con su cifra.
    Informativos: no cambian la categoría ni inventan umbrales nuevos."""
    riesgos = []
    if nivel_evidencia == "provisional":
        riesgos.append({"tipo": "datos", "texto": "evidencia provisional: el valor se calculó con confianza baja"})
    if desfase:
        riesgos.append({"tipo": "datos", "texto": f"resultados {desfase} trimestre(s) más viejos que el balance"})
    if e.get("pilar1") is None:
        riesgos.append({"tipo": "deuda", "texto": "seguridad financiera no evaluable: " + (e.get("pilar1_motivo") or "faltan insumos")})
    elif e.get("pilar1_motivo"):
        riesgos.append({"tipo": "deuda", "texto": str(e["pilar1_motivo"])[:160]})
    mediana = e.get("liquidez_mediana_cop")
    if mediana:
        riesgos.append({"tipo": "liquidez",
                        "texto": f"mediana de {mediana / 1e6:,.0f} M COP al día ({mediana / LIQUIDEZ_MINIMA_COP:.1f}x el mínimo de la puerta)"})
    return riesgos


def retorno_anualizado_ilustrativo(valor_base, precio, renta_sostenible_pct=None,
                                   anios=HORIZONTE_ILUSTRATIVO_ANIOS):
    """Retorno total anualizado SI el precio converge al valor base al final de `anios` (Codex H1 / P2.2).
    Es condicional y aproximado (suma el rendimiento por dividendo solo si es renta sostenible): no es un
    pronóstico, y el horizonte es un supuesto. Devuelve los supuestos junto con la cifra, o None."""
    if valor_base is None or not precio or valor_base <= 0 or anios <= 0:
        return None
    precio_pct = ((valor_base / precio) ** (1 / anios) - 1) * 100
    renta = renta_sostenible_pct or 0.0
    return {"retorno_pct": round(precio_pct + renta, 1), "por_precio_pct": round(precio_pct, 1),
            "por_renta_pct": round(renta, 1), "horizonte_anios": anios,
            "supuestos": (f"el precio converge al valor base en {anios} años; la renta suma solo si es sostenible; "
                          "sin impuestos ni costos de transacción. Ilustrativo, no es un pronóstico")}


INSUMOS_COMPARADOS = (("acciones_total", "conteo de acciones", 0.0), ("wacc_pct", "WACC / costo del patrimonio", 0.005),
                      ("metodo_usado", "método usado", None), ("ebit_normalizado_mmm", "EBIT normalizado", 0.005),
                      ("deuda_neta_mmm", "deuda neta", 0.005))


def _causas_por_insumos(anterior: dict | None, nuevo: dict | None) -> list[str]:
    """Insumos que cambiaron entre dos corridas (acciones, WACC, método, EBIT normalizado, deuda neta). Solo se compara
    lo que ambas corridas guardaron: lo que falta en una de las dos no se declara como cambio."""
    causas = []
    for clave, nombre, tolerancia in INSUMOS_COMPARADOS:
        a, b = (anterior or {}).get(clave), (nuevo or {}).get(clave)
        if a is None or b is None:
            continue
        if tolerancia is None:
            if a != b:
                causas.append(f"{nombre}: {a} -> {b}")
        elif a == 0 and b != 0 or a != 0 and abs(b / a - 1) > tolerancia:
            causas.append(f"{nombre}: {a:,.4g} -> {b:,.4g}")
    return causas


def causa_del_cambio(anterior: dict | None, nuevo: dict) -> dict:
    """Qué cambió entre dos corridas del ranking y a qué se atribuye el cambio del valor (Codex P2.6).
    Cada lado trae valor_central, precio, balance, resultados y, si aplica, ruta. Sin acciones ni supuestos
    guardados no se puede separar esa causa: se declara como residual, no se inventa."""
    if not anterior or anterior.get("valor_central") in (None, 0) or nuevo.get("valor_central") is None:
        return {"valor_cambio_pct": None, "precio_cambio_pct": None,
                "causas": ["primera corrida con historial o sin valor previo comparable"]}
    dv = (nuevo["valor_central"] / anterior["valor_central"] - 1) * 100
    dp = ((nuevo["precio"] / anterior["precio"] - 1) * 100
          if nuevo.get("precio") and anterior.get("precio") else None)
    causas = []
    if abs(dv) < UMBRAL_CAMBIO_VALOR_PCT:
        causas.append("sin cambio relevante en el valor base")
    else:
        if (anterior.get("balance"), anterior.get("resultados")) != (nuevo.get("balance"), nuevo.get("resultados")):
            causas.append(f"estados financieros nuevos (balance {anterior.get('balance')} -> {nuevo.get('balance')}, "
                          f"resultados {anterior.get('resultados')} -> {nuevo.get('resultados')})")
        if nuevo.get("ruta") == "holding" and dp is not None and abs(dp) >= UMBRAL_CAMBIO_VALOR_PCT:
            causas.append("precio vivo de las participaciones cotizadas del holding")
        causas += _causas_por_insumos(anterior.get("insumos"), nuevo.get("insumos"))
        if not causas:
            if anterior.get("insumos") and nuevo.get("insumos"):
                causas.append("mismos estados e insumos guardados: el cambio viene del precio vivo o de una regla del modelo")
            else:
                causas.append("mismos estados financieros: cambió un supuesto, el conteo de acciones o el método "
                              "(la corrida anterior no guardó esos insumos por separado)")
    return {"valor_cambio_pct": round(dv, 1), "precio_cambio_pct": round(dp, 1) if dp is not None else None,
            "causas": causas}


def subida_al_valor(valor_central, precio):
    """Subida hasta el valor estimado, (valor / precio) - 1, en %. NO es retorno esperado: no tiene
    horizonte ni trayectoria (Codex H1). Distinta del margen de seguridad (valor - precio) / valor."""
    if valor_central is None or not precio or valor_central <= 0:
        return None
    return (valor_central / precio - 1) * 100


def ordenar(resultados: list[dict]) -> list[dict]:
    """Asigna `posicion` (1 = primero) a los no excluidos, EN EL LUGAR. Orden: cuadrante, luego mayor
    margen de seguridad, luego mayor puntaje de ventaja competitiva. Una seguridad no evaluada que
    no es barata se ordena con las caras."""
    def clave(r):
        cuad = r["cuadrante"]
        if cuad == NO_EVALUADA and not r.get("barata"):
            cuad_orden = 3
        else:
            cuad_orden = ORDEN_CUADRANTE[cuad]
        margen = r.get("margen_seguridad_pct")
        return (cuad_orden, -(margen if margen is not None else -1e9), -(r.get("ventaja_puntaje") or 0))
    ranked = sorted((r for r in resultados if not r["excluido"]), key=clave)
    for i, r in enumerate(ranked, start=1):
        r["posicion"] = i
    for r in resultados:
        if r["excluido"]:
            r["posicion"] = None
    return ranked
