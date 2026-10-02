# -*- coding: utf-8 -*-
"""Pruebas de la capa de valoración de `analizador_fundamental.py` (auditoría 01-oct-2026:
las pruebas existentes solo cubrían la extracción). Sin pytest ni base de datos."""

from _prueba_utils import revisar, reportar_y_salir

import analizador_fundamental as a  # noqa: E402

print("--- capitalización por clase (E2) ---")
# Cibest: 509.704.584 ordinarias a 90.000 + 444.271.389 preferenciales a 78.820
revisar("Cibest suma las dos clases", a.capitalizacion_total(90000, 509_704_584, 78820, 444_271_389),
        round((509_704_584 * 90000 + 444_271_389 * 78820) / 1e9, 3))
revisar("sin preferenciales, solo ordinaria", a.capitalizacion_total(10, 1_000_000_000, None, 0), 10.0)
revisar("preferencial sin precio propio usa el de la ordinaria", a.capitalizacion_total(10, 1_000_000_000, None, 500_000_000), 15.0)
revisar("sin precio no hay capitalización", a.capitalizacion_total(None, 1_000, 5, 5), None)
revisar("Cibest con las dos clases ya no sale en P/E 7,5", a.capitalizacion_total(90000, 509_704_584, 78820, 444_271_389) > 45873.413 * 1.5, True)

print("--- períodos duplicados (E3) ---")
f = lambda anio, per, ing, ut: {"anio": anio, "periodo": per, "ingresos": ing, "utilidad_neta": ut}
revisar("T2 2025 idéntico al ANUAL 2024 se marca",
        "2025-T2" in a.revisar_periodos_duplicados([f(2024, "ANUAL", 7363.3, 1056.7), f(2025, "T2", 7363.3, 1056.7)]), True)
revisar("ANUAL y su T4 pueden coincidir",
        a.revisar_periodos_duplicados([f(2022, "ANUAL", 100.0, 10.0), f(2022, "T4", 100.0, 10.0)]), "")
revisar("períodos distintos sin coincidencia no alertan",
        a.revisar_periodos_duplicados([f(2024, "ANUAL", 7363.3, 1056.7), f(2025, "ANUAL", 7337.6, 1073.9)]), "")

print("--- ingresos en cero (E4) ---")
revisar("ANUAL en cero con trimestres con ingresos se marca",
        bool(a.revisar_ingresos_en_cero([f(2024, "ANUAL", 0, 5), f(2024, "T2", 513.0, 2)])), True)
revisar("ANUAL en cero sin trimestres no alerta", a.revisar_ingresos_en_cero([f(2024, "ANUAL", 0, 5)]), "")

print("--- el ranking excluye alertas e ilíquidos (E5) ---")
filas = [
    {"emisor": "A", "spread_valor": 5.0, "alerta_multiplos": ""},
    {"emisor": "B", "spread_valor": 9.0, "alerta_multiplos": "ingresos inconsistentes"},
    {"emisor": "C", "spread_valor": 7.0, "alerta_multiplos": ""},
    {"emisor": "D", "spread_valor": 1.0, "alerta_multiplos": ""},
    {"emisor": "E", "spread_valor": None, "alerta_multiplos": ""},
]
a.calcular_estrellas(filas, frozenset({"C"}))
rk = {r["emisor"]: r["ranking_estrella"] for r in filas}
revisar("con alerta no entra", rk["B"], None)
revisar("ilíquido no entra", rk["C"], None)
revisar("sin spread no entra", rk["E"], None)
revisar("el resto se ordena por spread", (rk["A"], rk["D"]), (1, 2))
revisar("el descarte por liquidez queda dicho", "liquidez" in filas[2]["alerta_multiplos"], True)

print("--- métricas ampliadas P1 ---")
m = a.metricas_ampliadas(
    fco=2552.3, capex=1706.3, utilidad=2420.3, ebitda=7922.2, operacional=6842.0, ingresos=15918.0,
    bruta=8207.3, gasto_fin=2513.9, uai=5020.3, impuesto=1111.1, efectivo=4466.1, minoritarios=10457.8,
    deuda=33790.9, patrimonio=17098.3, capitalizacion=31568.8, tasa_nominal=0.35)
revisar("FCF = FCO - capex", m["fcf_ttm_mmm"], 846.0)
revisar("deuda neta = deuda - caja", m["deuda_neta_mmm"], 29324.8)
revisar("deuda neta / EBITDA", m["deuda_neta_ebitda"], 3.70)
revisar("cobertura = EBIT / gasto financiero", m["cobertura_intereses"], 2.7)
revisar("tasa efectiva = impuesto / UAI", m["tasa_efectiva_pct"], 22.1)
revisar("capital invertido suma minoritarios y resta caja", m["capital_invertido_mmm"], 56880.9)
revisar("margen bruto", m["margen_bruto"], 51.6)
revisar("FCF yield sobre capitalización", m["fcf_yield_pct"], 2.7)
sin = a.metricas_ampliadas(
    fco=100.0, capex=None, utilidad=50.0, ebitda=None, operacional=80.0, ingresos=500.0, bruta=None,
    gasto_fin=None, uai=None, impuesto=None, efectivo=None, minoritarios=None, deuda=200.0,
    patrimonio=300.0, capitalizacion=400.0, tasa_nominal=0.35)
revisar("sin capex no hay FCF (no se inventa)", sin["fcf_ttm_mmm"], None)
revisar("sin caja no hay deuda neta ni ROIC ajustado", (sin["deuda_neta_mmm"], sin["roic_ajustado"]), (None, None))
revisar("pérdida antes de impuestos no da tasa efectiva",
        a.metricas_ampliadas(fco=1, capex=1, utilidad=1, ebitda=1, operacional=1, ingresos=1, bruta=1,
                             gasto_fin=1, uai=-5.0, impuesto=2.0, efectivo=1, minoritarios=0, deuda=1,
                             patrimonio=1, capitalizacion=1, tasa_nominal=0.35)["tasa_efectiva_pct"], None)
revisar("EV real = cap + deuda neta + minoritarios", a.ev_real(1000.0, 500.0, 200.0, 100.0), 1400.0)
revisar("EV sin caja usa deuda bruta", a.ev_real(1000.0, 500.0, None, 100.0), 1600.0)

reportar_y_salir()
