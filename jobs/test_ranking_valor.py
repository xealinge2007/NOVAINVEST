# -*- coding: utf-8 -*-
"""Pruebas del ranking por puertas (P3). Sin base de datos."""

from _prueba_utils import revisar, reportar_y_salir

from app.services import ranking_valor as rk  # noqa: E402


def e(**kw):
    base = {"elegible": True, "alerta_datos": "", "pilar1": True, "pilar1_motivo": "ok",
            "valor": {"determinable": True, "margen_seguridad_pct": 30.0, "confianza": "media"},
            "catalizador_nivel": "ninguno", "dividend_yield_pct": None, "payout_pct": None}
    base.update(kw)
    return base


print("--- puertas: cada una excluye y dice por que ---")
r = rk.evaluar(e(elegible=False, motivo_no_elegible="liquidez insuficiente: X"))
revisar("liquidez", (r["excluido"], r["puerta_fallida"]), (True, "liquidez"))
r = rk.evaluar(e(alerta_datos="P/VL 14.5 fuera de rango"))
revisar("alerta de datos", (r["excluido"], r["puerta_fallida"]), (True, "datos"))
r = rk.evaluar(e(alerta_datos="no pasa la puerta de liquidez"))
revisar("la alerta de liquidez sola no cuenta como alerta de datos", r["excluido"], False)
r = rk.evaluar(e(pilar1=False, pilar1_motivo="cobertura 1.2x < 1.5x"))
revisar("seguridad reprobada: no invertible", (r["excluido"], r["puerta_fallida"]), (True, "seguridad"))
r = rk.evaluar(e(valor={"determinable": False, "motivo": "EBIT negativo"}))
revisar("sin valor determinable", (r["excluido"], r["motivo_exclusion"]), (True, "EBIT negativo"))

print("--- cuadrantes ---")
r = rk.evaluar(e(catalizador_nivel="fuerte"))
revisar("segura, barata y con catalizador = safe_cheap", r["cuadrante"], "safe_cheap")
revisar("no se sugiere tamano de posicion", r["tamano_relativo"], None)
r = rk.evaluar(e(dividend_yield_pct=7.0, payout_pct=60.0))
revisar("segura, barata, solo renta con payout = safe_cheap", r["cuadrante"], "safe_cheap")
r = rk.evaluar(e(dividend_yield_pct=7.6, payout_pct=None))
revisar("rendimiento alto SIN payout no es renta (caso PEI)", (r["cuadrante"], r["renta_sostenible"]), ("trampa_descuento", False))
r = rk.evaluar(e())
revisar("barata sin catalizador ni renta = trampa de descuento", r["cuadrante"], "trampa_descuento")
r = rk.evaluar(e(dividend_yield_pct=8.0, payout_pct=120.0))
revisar("dividendo por encima de la utilidad no es renta sostenible", r["cuadrante"], "trampa_descuento")
r = rk.evaluar(e(valor={"determinable": True, "margen_seguridad_pct": 5.0, "confianza": "media"}))
revisar("margen menor al umbral = safe_cara", r["cuadrante"], "safe_cara")
r = rk.evaluar(e(pilar1=None, catalizador_nivel="fuerte"))
revisar("seguridad no evaluada nunca es favorable", (r["cuadrante"], r["tamano_relativo"]), ("seguridad_no_evaluada", None))
r = rk.evaluar(e(valor={"determinable": True, "margen_seguridad_pct": 30.0, "confianza": "baja"}))
revisar("confianza baja = evidencia provisional", r["nivel_evidencia"], "provisional")
revisar("la evidencia verificada no se asigna sin auditoria externa", r["nivel_evidencia"] != "verificado", True)

print("--- integridad temporal ---")
r = rk.evaluar(e(desfase_resultados_trimestres=6, ruta_valor="activos_epv"))
revisar("EPV con resultados desfasados se excluye por datos", (r["excluido"], r["puerta_fallida"]), (True, "datos"))
r = rk.evaluar(e(desfase_resultados_trimestres=6, ruta_valor="inmobiliario", dividend_yield_pct=8.0, payout_pct=50.0))
revisar("NAV con resultados desfasados sigue, pero sin renta", (r["excluido"], r["renta_sostenible"]), (False, False))
r = rk.evaluar(e(desfase_resultados_trimestres=0, ruta_valor="activos_epv"))
revisar("resultados al dia no excluyen", r["excluido"], False)

print("--- subida vs margen ---")
revisar("subida = valor/precio - 1", round(rk.subida_al_valor(150.0, 100.0), 1), 50.0)
revisar("sin valor positivo no hay subida", rk.subida_al_valor(-5.0, 100.0), None)

print("--- orden ---")
lista = [
    {**rk.evaluar(e(catalizador_nivel="fuerte")), "margen_seguridad_pct": 25.0, "ventaja_puntaje": 10, "id": "A"},
    {**rk.evaluar(e(catalizador_nivel="fuerte")), "margen_seguridad_pct": 40.0, "ventaja_puntaje": 5, "id": "B"},
    {**rk.evaluar(e()), "margen_seguridad_pct": 90.0, "ventaja_puntaje": 99, "id": "C"},
    {**rk.evaluar(e(elegible=False)), "margen_seguridad_pct": None, "id": "D"},
    {**rk.evaluar(e(valor={"determinable": True, "margen_seguridad_pct": 2.0, "confianza": "media"})),
     "margen_seguridad_pct": 2.0, "ventaja_puntaje": 50, "id": "E"},
]
rk.ordenar(lista)
pos = {r["id"]: r["posicion"] for r in lista}
revisar("safe_cheap con mas margen primero", (pos["B"], pos["A"]), (1, 2))
revisar("una trampa con 90 % de margen queda detras de las safe_cheap", pos["C"], 3)
revisar("la cara va despues de la trampa", pos["E"], 4)
revisar("la excluida no tiene posicion", pos["D"], None)

reportar_y_salir()
