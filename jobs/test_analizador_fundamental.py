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

reportar_y_salir()
