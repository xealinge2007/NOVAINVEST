# -*- coding: utf-8 -*-
"""Pruebas de la rúbrica de ventajas competitivas (P3). Sin base de datos; cada caso se calcula a mano."""

from _prueba_utils import revisar, reportar_y_salir

from app.services import ventaja_competitiva as vc  # noqa: E402


def serie(roic, anios=range(2019, 2026), ingresos=1000.0, bruta=400.0):
    """Años con capital 1.000 (patrimonio 600 + deuda 400) y EBIT para dar `roic` con t = 35 %."""
    ebit = roic * 1000.0 / 0.65
    return {y: {"utilidad_operacional": ebit, "patrimonio": 600.0, "deuda_financiera": 400.0,
                "ingresos": ingresos, "utilidad_bruta": bruta} for y in anios}


print("--- ROIC por año ---")
r = vc.roic_por_anio({2025: {"utilidad_operacional": 100.0, "patrimonio": 500.0, "deuda_financiera": 300.0,
                             "interes_minoritario": 100.0, "efectivo": 200.0}})
revisar("capital = patrimonio + minoritarios + deuda - caja = 700 da ROIC 65/700", round(r[2025], 4), round(65 / 700, 4))

print("--- empresa con ventaja amplia ---")
res = vc.evaluar("TERPEL", "real", serie(0.20), 0.10, "franquicia")
revisar("ROIC 20 % vs WACC 10 % todos los años, margen estable, franquicia = 100", res["puntaje"], 100.0)
revisar("nivel amplia", res["nivel"], "amplia")
revisar("tendencia estable", res["tendencia"], "estable")
revisar("fuente declarada (juicio de la casa)", res["fuente_ventaja"], "red")

print("--- commodity que destruye valor ---")
res = vc.evaluar("ECOPETROL", "real", serie(0.05), 0.12, "destruccion_valor")
revisar("ROIC 5 % < WACC 12 %: persistencia 0, spread 0, margen estable 20, EPV 0 = 20", res["puntaje"], 20.0)
revisar("nivel ninguna", res["nivel"], "ninguna")
res = vc.evaluar("ISA", "real", serie(0.05), 0.12, "destruccion_valor")
revisar("regulada sin respaldo numérico se marca", any("SIN respaldo" in a for a in res["evidencia"]["avisos"]), True)

print("--- commodity: el ciclo no es ventaja ---")
res = vc.evaluar("MINEROS", "real", serie(0.30), 0.10, "franquicia")
revisar("retorno altisimo de un commodity se topa en estrecha", (res["puntaje"], res["nivel"]), (100.0, "estrecha"))

print("--- casos que no se evalúan ---")
revisar("menos de 4 años: no evaluable", vc.evaluar("X", "real", serie(0.2, range(2023, 2026)), 0.1)["nivel"], "no_evaluable")
revisar("holding: no aplica", vc.evaluar("GRUPO_SURA", "holding", serie(0.2), 0.1)["nivel"], "no_aplica")
revisar("sin costo de capital: no evaluable", vc.evaluar("X", "real", serie(0.2), None)["nivel"], "no_evaluable")

print("--- banco: ROE contra Ke ---")
banco = {y: {"utilidad_neta": 180.0, "patrimonio": 1000.0} for y in range(2019, 2026)}
res = vc.evaluar("GRUPO_CIBEST_BANCOLOMBIA", "banco", banco, 0.14)
# 50 (todos los años) + 25 * (4 pp / 6 pp) + 25 (ROE sin variación) = 91,7
revisar("ROE 18 % vs Ke 14 %", res["puntaje"], 91.7)
revisar("banco usa ROE", res["evidencia"]["metrica"], "ROE")

print("--- tendencia ---")
revisar("spreads que suben = mejorando", vc.tendencia_de([0.0, 0.02, 0.04, 0.06]), "mejorando")
revisar("spreads que bajan = deteriorando", vc.tendencia_de([0.06, 0.04, 0.02, 0.0]), "deteriorando")
revisar("coeficiente de variación de una serie constante = 0", vc.coeficiente_variacion([5.0, 5.0, 5.0]), 0.0)

reportar_y_salir()
