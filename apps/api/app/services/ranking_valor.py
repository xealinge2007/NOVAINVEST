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

UMBRAL_BARATA_PCT = 20.0     # margen de seguridad central mínimo para llamarla "barata"
RENTA_YIELD_MINIMO_PCT = 6.0
RENTA_PAYOUT_MAXIMO_PCT = 100.0
ALERTA_LIQUIDEZ = "no pasa la puerta de liquidez"

ORDEN_CUADRANTE = {"safe_cheap": 0, "seguridad_no_evaluada": 1, "trampa_descuento": 2, "safe_cara": 3}


def _excluido(puerta, motivo):
    return {"excluido": True, "puerta_fallida": puerta, "motivo_exclusion": motivo, "cuadrante": None,
            "tamano_relativo": None, "nivel_evidencia": None}


def evaluar(e: dict) -> dict:
    """Veredicto de un emisor. `e` trae: elegible, motivo_no_elegible, alerta_datos, pilar1 (bool|None),
    pilar1_motivo, valor ({determinable, motivo, margen_seguridad_pct, confianza}),
    catalizador_nivel, dividend_yield_pct, payout_pct."""
    if e.get("elegible") is False:
        return _excluido("liquidez", e.get("motivo_no_elegible") or "no pasa la puerta de liquidez")
    alerta = (e.get("alerta_datos") or "").replace(ALERTA_LIQUIDEZ, "").strip(" |")
    if alerta:
        return _excluido("datos", f"alerta de datos abierta: {alerta[:160]}")
    if e.get("pilar1") is False:
        return _excluido("seguridad", f"no invertible: {e.get('pilar1_motivo') or 'reprueba la puerta de seguridad'}")
    valor = e.get("valor") or {}
    if not valor.get("determinable"):
        return _excluido("valor", valor.get("motivo") or "sin valor por acción determinable")

    margen = valor.get("margen_seguridad_pct")
    barata = margen is not None and margen >= UMBRAL_BARATA_PCT
    yld, payout = e.get("dividend_yield_pct"), e.get("payout_pct")
    renta = yld is not None and yld >= RENTA_YIELD_MINIMO_PCT and (payout is None or payout <= RENTA_PAYOUT_MAXIMO_PCT)
    vivo = e.get("catalizador_nivel") in ("fuerte", "debil")

    if e.get("pilar1") is not True:
        cuadrante = "seguridad_no_evaluada"
        tamano = "minima" if barata else "ninguna"
    elif not barata:
        cuadrante, tamano = "safe_cara", "ninguna"
    elif vivo or renta:
        cuadrante = "safe_cheap"
        tamano = "normal" if e.get("catalizador_nivel") == "fuerte" else "minima"
    else:
        cuadrante, tamano = "trampa_descuento", "ninguna"

    return {"excluido": False, "puerta_fallida": None, "motivo_exclusion": None, "cuadrante": cuadrante,
            "tamano_relativo": tamano, "renta_sostenible": renta, "barata": barata,
            "nivel_evidencia": "provisional" if valor.get("confianza") == "baja" else "estructura"}


def ordenar(resultados: list[dict]) -> list[dict]:
    """Asigna `posicion` (1 = primero) a los no excluidos, EN EL LUGAR. Orden: cuadrante, luego mayor
    margen de seguridad, luego mayor puntaje de ventaja competitiva. Una seguridad_no_evaluada que
    no es barata se ordena con las caras."""
    def clave(r):
        cuad = r["cuadrante"]
        if cuad == "seguridad_no_evaluada" and not r.get("barata"):
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
