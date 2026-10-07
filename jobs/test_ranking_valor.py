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
revisar("segura, barata y con catalizador = descuento_con_soporte", r["cuadrante"], "descuento_con_soporte")
revisar("no se sugiere tamano de posicion", r["tamano_relativo"], None)
r = rk.evaluar(e(dividend_yield_pct=7.0, payout_pct=60.0))
revisar("segura, barata, solo renta con payout = descuento_con_soporte", r["cuadrante"], "descuento_con_soporte")
r = rk.evaluar(e(dividend_yield_pct=7.6, payout_pct=None))
revisar("rendimiento alto SIN payout no es renta (caso PEI)", (r["cuadrante"], r["renta_sostenible"]), ("descuento_sin_soporte", False))
r = rk.evaluar(e())
revisar("barata sin catalizador ni renta = descuento sin soporte", r["cuadrante"], "descuento_sin_soporte")
r = rk.evaluar(e(dividend_yield_pct=8.0, payout_pct=120.0))
revisar("dividendo por encima de la utilidad no es renta sostenible", r["cuadrante"], "descuento_sin_soporte")
r = rk.evaluar(e(valor={"determinable": True, "margen_seguridad_pct": 5.0, "confianza": "media"}))
revisar("margen menor al umbral = sin_descuento", r["cuadrante"], "sin_descuento")
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
revisar("descuento_con_soporte con mas margen primero", (pos["B"], pos["A"]), (1, 2))
revisar("una trampa con 90 % de margen queda detras de las descuento_con_soporte", pos["C"], 3)
revisar("la cara va despues de la trampa", pos["E"], 4)
revisar("la excluida no tiene posicion", pos["D"], None)

print("--- riesgos que acompanan a la categoria (P2.4) ---")
r = rk.evaluar(e(valor={"determinable": True, "margen_seguridad_pct": 30.0, "confianza": "baja"}, pilar1=None,
                 pilar1_motivo="sin EBITDA", liquidez_mediana_cop=300_000_000, desfase_resultados_trimestres=6,
                 ruta_valor="inmobiliario"))
tipos = [x["tipo"] for x in r["riesgos"]]
revisar("riesgos: datos (provisional + desfase), deuda no evaluable y liquidez", sorted(tipos), ["datos", "datos", "deuda", "liquidez"])
liq = [x["texto"] for x in r["riesgos"] if x["tipo"] == "liquidez"][0]
revisar("liquidez dice cuantas veces supera la puerta de 150 M", "2.0x" in liq, True)
r = rk.evaluar(e())
revisar("sin riesgos de datos no se inventan", [x["tipo"] for x in r["riesgos"]], ["deuda"])

print("--- retorno anualizado ilustrativo (P2.2) ---")
x = rk.retorno_anualizado_ilustrativo(133.1, 100.0, None, anios=3)
revisar("converger a 133,1 desde 100 en 3 anios = 10 % anual", x["retorno_pct"], 10.0)
x = rk.retorno_anualizado_ilustrativo(133.1, 100.0, 5.0, anios=3)
revisar("suma la renta sostenible", (x["por_precio_pct"], x["por_renta_pct"], x["retorno_pct"]), (10.0, 5.0, 15.0))
revisar("declara horizonte y supuestos", (x["horizonte_anios"], "no es un pronóstico" in x["supuestos"]), (3, True))
revisar("valor negativo: sin retorno", rk.retorno_anualizado_ilustrativo(-5.0, 100.0), None)
revisar("sin precio: sin retorno", rk.retorno_anualizado_ilustrativo(50.0, None), None)
x = rk.retorno_anualizado_ilustrativo(50.0, 100.0, None)
revisar("valor menor al precio da retorno negativo, no se oculta", x["retorno_pct"] < 0, True)

print("--- historial: causa del cambio (P2.6) ---")
ant = {"valor_central": 100.0, "precio": 80.0, "balance": "2026-T1", "resultados": "anual 2025"}
revisar("sin corrida previa se dice", rk.causa_del_cambio(None, {"valor_central": 100.0, "precio": 80.0})["valor_cambio_pct"], None)
c = rk.causa_del_cambio(ant, {**ant, "valor_central": 100.2})
revisar("cambio menor al umbral = sin cambio relevante", c["causas"], ["sin cambio relevante en el valor base"])
c = rk.causa_del_cambio(ant, {**ant, "balance": "2026-T2", "valor_central": 120.0})
revisar("estados nuevos se atribuyen a los estados", (c["valor_cambio_pct"], "estados financieros nuevos" in c["causas"][0]), (20.0, True))
c = rk.causa_del_cambio(ant, {**ant, "valor_central": 90.0, "precio": 85.0})
revisar("mismos estados: residual declarado, no inventado", "mismos estados financieros" in c["causas"][0], True)
c = rk.causa_del_cambio(ant, {**ant, "valor_central": 90.0, "precio": 85.0, "ruta": "holding"})
revisar("holding: precio vivo de cotizadas", any("precio vivo" in x for x in c["causas"]), True)

print("--- historial: causas por insumos guardados ---")
ins = {"acciones_total": 100.0, "wacc_pct": 11.1, "metodo_usado": "epv", "ebit_normalizado_mmm": 1000.0, "deuda_neta_mmm": 500.0}
ant2 = {**ant, "insumos": ins}
c = rk.causa_del_cambio(ant2, {**ant2, "valor_central": 90.0, "insumos": {**ins, "acciones_total": 120.0}})
revisar("cambio de acciones se atribuye al conteo de acciones", [x for x in c["causas"] if "acciones" in x], ["conteo de acciones: 100 -> 120"])
c = rk.causa_del_cambio(ant2, {**ant2, "valor_central": 90.0, "insumos": {**ins, "metodo_usado": "dcf", "wacc_pct": 12.0}})
revisar("cambio de metodo y WACC", sorted(x.split(":")[0] for x in c["causas"]), ["WACC / costo del patrimonio", "método usado"])
c = rk.causa_del_cambio(ant2, {**ant2, "valor_central": 90.0, "insumos": {**ins, "deuda_neta_mmm": 500.5}})
revisar("variacion de deuda dentro de la tolerancia no cuenta", "residual" in str(c["causas"]) or "mismos estados e insumos" in c["causas"][0], True)
c = rk.causa_del_cambio(ant, {**ant, "valor_central": 90.0, "precio": 85.0, "insumos": ins})
revisar("si la corrida anterior no guardo insumos no se inventa causa", "no guardó esos insumos" in c["causas"][0], True)

print("--- nombres vigentes y legado ---")
revisar("mapa legado", rk.CUADRANTE_LEGADO["safe_cheap"], "descuento_con_soporte")
revisar("score_valor conserva su esquema", rk.CUADRANTE_A_SCORE_VALOR[rk.SIN_SOPORTE], "trampa_descuento")

reportar_y_salir()
