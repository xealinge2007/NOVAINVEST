# -*- coding: utf-8 -*-
"""Pruebas de `app.services.valoracion` (P2). Sin pytest ni base de datos; los números se
calculan a mano en cada caso para que la prueba sea una comprobación independiente."""

from _prueba_utils import revisar, reportar_y_salir

from app.services import valoracion as v  # noqa: E402

print("--- EBIT normalizado ---")
ciclico = {2019: 100.0, 2020: 20.0, 2021: 180.0, 2022: 40.0, 2023: 160.0}
ebit, metodo, r2, plano, ult3 = v.normalizar_ebit(ciclico, "X")
revisar("serie cíclica usa el promedio de todo el período", round(ebit, 1), 100.0)
tendencia = {2019: 10.0, 2020: 20.0, 2021: 30.0, 2022: 40.0, 2023: 50.0}
ebit, metodo, r2, _, _ = v.normalizar_ebit(tendencia, "X")
revisar("tendencia limpia usa los últimos 3 años", round(ebit, 1), 40.0)
ebit, metodo, _, _, _ = v.normalizar_ebit(tendencia, "MINEROS")
revisar("commodity puro ignora la tendencia", round(ebit, 1), 30.0)

print("--- EPV por acción ---")
# EBIT 1000, WACC 10 %, g 3 %, t 35 % => EV 650 / 0,07 = 9.285,7; deuda neta 1.500 y minoritarios 500
ev, eq = v.valor_epv(1000.0, 0.10, 1500.0, 500.0)
revisar("EPV EV = NOPAT / (WACC - g)", round(ev, 1), 9285.7)
revisar("EPV patrimonio", round(eq, 1), 7285.7)
revisar("WACC - g demasiado chico no se valora", v.valor_epv(1000.0, 0.04, 0.0, 0.0), (None, None))
esc = v.escenarios_epv(1000.0, 1000.0, 1000.0, 0.10, 1500.0, 500.0, 900_000_000)
revisar("por acción central = 7.285,7 mil millones / 900 M acciones", round(esc["central"]["por_accion"], 1), 8095.2)
revisar("el bajo no supera al central", esc["bajo"]["patrimonio"] < esc["central"]["patrimonio"], True)
revisar("el alto no es menor al central", esc["alto"]["patrimonio"] > esc["central"]["patrimonio"], True)
esc_ttm = v.escenarios_epv(1000.0, 1000.0, 1000.0, 0.10, 1500.0, 500.0, 900_000_000, ebit_ttm=2000.0)
revisar("el EBIT TTM solo sube el escenario alto", (esc_ttm["central"]["patrimonio"] == esc["central"]["patrimonio"],
        esc_ttm["alto"]["patrimonio"] > esc["alto"]["patrimonio"]), (True, True))
revisar("sensibilidad: 9 celdas", len(v.sensibilidad_epv(1000.0, 0.10, 1500.0, 500.0, 900_000_000)), 9)
# EV de mercado = EPV => el mercado descuenta exactamente crecimiento por inflación (real ~0)
g = v.crecimiento_implicito(9285.7, 1000.0, 0.10)
revisar("si el precio iguala al EPV el crecimiento nominal implícito = inflación", round(g, 3), v.CRECIMIENTO_INFLACION)
revisar("pagar el doble descuenta crecimiento real positivo", v.crecimiento_implicito(18571.4, 1000.0, 0.10) - v.CRECIMIENTO_INFLACION > 0.03, True)

print("--- diagnóstico Greenwald ---")
revisar("EPV 20 % sobre el capital = franquicia", v.diagnostico_greenwald(1200.0, 1000.0), "franquicia")
revisar("EPV 20 % bajo el capital = destrucción", v.diagnostico_greenwald(800.0, 1000.0), "destruccion_valor")
revisar("EPV ~ capital = commodity", v.diagnostico_greenwald(1000.0, 1000.0), "commodity")

print("--- banco: P/VL justificado ---")
revisar("ROE 16 %, Ke 14 %, g 4 % => 1,2", round(v.pvl_justificado(0.16, 0.14), 3), 1.2)
revisar("ROE 4 % = g => vale cero", v.pvl_justificado(0.04, 0.14), 0.0)
revisar("ROE bajo g nunca da negativo", v.pvl_justificado(0.02, 0.14), 0.0)
revisar("Ke <= g no tiene sentido", v.pvl_justificado(0.16, 0.04), None)
b = v.escenarios_banco([0.10, 0.12, 0.14], 0.14, 1000.0, 100_000_000)
revisar("ROE central = mediana", b["roe_central"], 0.12)
revisar("banco: bajo < central < alto", b["bajo"]["patrimonio"] < b["central"]["patrimonio"] < b["alto"]["patrimonio"], True)

print("--- holding: NAV con rango y LTV ---")
r = v.rango_nav_holding(1000.0, 400.0, -300.0)
revisar("bajo = cotizadas + 50 % libro + neto", r["bajo"], 900.0)
revisar("central = cotizadas + 75 % libro + neto", r["central"], 1000.0)
revisar("alto = cotizadas + 100 % libro + neto", r["alto"], 1100.0)
revisar("LTV = deuda neta propia / participaciones brutas", v.ltv_holding(-300.0, 1400.0), 300.0 / 1400.0)
revisar("holding con caja neta: LTV cero", v.ltv_holding(100.0, 1400.0), 0.0)
revisar("margen de seguridad", round(v.margen_seguridad(100.0, 70.0), 1), 30.0)
revisar("sin valor positivo no hay margen", v.margen_seguridad(-5.0, 70.0), None)

print("--- seguridad por tipo (criterio aprobado 02-oct-2026) ---")
ok, _ = v.evaluar_seguridad("real", "energia_infraestructura", deuda_neta_ebitda=3.5, cobertura=2.8, ebitda=100.0)
revisar("ISA: regulado 3,5x neto con cobertura 2,8x pasa", ok, True)
ok, _ = v.evaluar_seguridad("real", "energia_utilities", deuda_neta_ebitda=4.7, cobertura=1.7, ebitda=100.0)
revisar("regulado hasta 5x pasa (GEB)", ok, True)
ok, _ = v.evaluar_seguridad("real", "cemento_construccion", deuda_neta_ebitda=3.2, cobertura=3.0, ebitda=100.0)
revisar("cíclico por encima de 3x neto no pasa", ok, False)
ok, m = v.evaluar_seguridad("real", "petroleo_gas", deuda_neta_ebitda=1.0, cobertura=1.2, ebitda=100.0)
revisar("poca deuda pero cobertura < 1,5x no pasa", ok, False)
ok, _ = v.evaluar_seguridad("real", "cemento_construccion", deuda_neta_ebitda=-4.3, cobertura=1.6, ebitda=100.0)
revisar("caja neta pasa", ok, True)
ok, _ = v.evaluar_seguridad("real", "consumo", deuda_ebitda=2.0, ebitda=100.0)
revisar("sin deuda neta cae a la bruta", ok, True)
ok, _ = v.evaluar_seguridad("real", "consumo", ebitda=-5.0)
revisar("sin datos suficientes no es evaluable", ok, None)
ok, _ = v.evaluar_seguridad("holding", "holding", ltv=None)
revisar("holding sin LTV no es evaluable (no se usa el consolidado)", ok, None)
ok, _ = v.evaluar_seguridad("holding", "holding", ltv=0.26)
revisar("holding con LTV 26 % pasa", ok, True)
ok, _ = v.evaluar_seguridad("holding", "holding", ltv=0.45)
revisar("holding con LTV 45 % no pasa", ok, False)
ok, _ = v.evaluar_seguridad("vehiculo_inmobiliario", "inmobiliario", deuda_patrimonio=0.37)
revisar("PEI usa deuda/patrimonio", ok, True)

print("--- bancos: seguridad con indicadores regulatorios ---")
ok, _ = v.evaluar_seguridad_banco(solvencia_total=14.9, cartera_vencida_90=3.6, costo_riesgo=2.1)
revisar("Banco de Bogota (14,9 % / 3,6 % / 2,1 %) pasa", ok, True)
ok, _ = v.evaluar_seguridad_banco(cet1=12.13, costo_riesgo=2.14)
revisar("solo CET1 y costo del riesgo alcanzan", ok, True)
ok, m = v.evaluar_seguridad_banco(solvencia_total=11.9, cartera_vencida_90=3.0)
revisar("solvencia por debajo de 12,5 % no pasa", ok, False)
ok, _ = v.evaluar_seguridad_banco(solvencia_total=15.0, cartera_vencida_90=6.5)
revisar("cartera vencida por encima de 5 % no pasa", ok, False)
ok, _ = v.evaluar_seguridad_banco(cartera_vencida_90=2.0, costo_riesgo=1.0)
revisar("sin indicador de capital no es evaluable", ok, None)

print("--- metodos no aplicables ---")
revisar("GEB queda no determinable con motivo (el EPV da un artefacto)", "asociadas" in v.NO_DETERMINABLE_POR_METODO.get("GEB", ""), True)

print("--- vehiculo inmobiliario: sensibilidad del NAV ---")
# Inmuebles 1.000, NOI 70 (cap 7 %), deuda 300 => NAV 700 con 10 M de titulos (70.000 por titulo).
sn = v.sensibilidad_nav_inmobiliario(noi_anual=70.0, valor_inmuebles=1000.0, nav_total=700.0, titulos=10_000_000,
                                     precio=35_000.0, ingresos_anuales=95.0, vacancia_economica_pct=5.0)
revisar("cap rate de los libros = NOI / inmuebles", sn["cap_rate_libros_pct"], 7.0)
revisar("NAV base por titulo", sn["nav_por_titulo_base"], 70000.0)
# +100 pb: cap 8 % => V = 70 / 0,08 = 875 => NAV = 700 - 125 = 575 => 57.500 por titulo
f100 = [f for f in sn["matriz"] if f["delta_bps"] == 100][0]
revisar("+100 pb de cap rate: NAV 57.500 por titulo", f100["vacancia_mas_0pp"], 57500.0)
# +3 pp de vacancia: ingresos potenciales 100 => NOI 67 => V = 67/0,07 = 957,14 => NAV 657,14
f0 = [f for f in sn["matriz"] if f["delta_bps"] == 0][0]
revisar("+3 pp de vacancia al mismo cap rate: NAV 65.714 por titulo", f0["vacancia_mas_3pp"], 65714.0)
# precio 35.000 x 10 M = 350 => V* = 1000 - (700 - 350) = 650 => cap implicito 70/650 = 10,77 %
revisar("cap rate implicito en el precio", sn["cap_rate_implicito_en_precio_pct"], 10.77)
revisar("brecha en pb frente al libro", sn["brecha_bps"], 377)
revisar("un cap rate mayor siempre baja el NAV",
        sn["matriz"][0]["vacancia_mas_0pp"] > sn["matriz"][-1]["vacancia_mas_0pp"], True)

reportar_y_salir()
