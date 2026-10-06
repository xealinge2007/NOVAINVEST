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
revisar("GEB ya no esta en la lista de no determinables: su EPV incluye asociadas", "GEB" in v.NO_DETERMINABLE_POR_METODO, False)
revisar("GEB esta marcado para sumar el resultado de asociadas", "GEB" in v.EMISORES_CON_ASOCIADAS, True)
# EBIT 100 (NOPAT 65) + asociadas 65 ya netas de impuesto => NOPAT total 130 => EBIT equivalente 200.
eq = v.ebit_equivalente(100.0, 65.0)
revisar("EBIT equivalente = EBIT + asociadas / (1 - tasa)", round(eq, 6), 200.0)
revisar("su NOPAT es el operativo mas las asociadas, sin gravarlas otra vez", round(eq * (1 - v.TASA_NOMINAL), 6), 130.0)
revisar("sin asociadas el EBIT no cambia", v.ebit_equivalente(100.0, 0.0), 100.0)
revisar("una perdida de asociadas lo reduce", round(v.ebit_equivalente(100.0, -32.5), 6), 50.0)

print("--- perfil de deuda de un vehiculo inmobiliario ---")
# PEI 30-jun-2026, nota 12 de los EEFF (miles de millones): bancaria CP 170,894 al 13,05 %, bancaria LP 1.743,854 al
# 12,92 %, bonos 761,223 al 9,26 %; EBITDA del 2T 141,414.
pd = v.perfil_deuda_vehiculo([(170.894306, 13.05), (1743.853844, 12.92), (761.223030, 9.26)], 141.414)
revisar("capital = suma de tramos", pd["capital"], 2675.971)
revisar("interes anual = 22,30 + 225,31 + 70,49 (318,097 exacto)", pd["interes_anual"], 318.097)
revisar("tasa ponderada = 318,10 / 2.675,97", pd["tasa_ponderada_pct"], 11.89)
revisar("deuda / EBITDA anualizado = 2.675,97 / 565,656", pd["deuda_ebitda_x"], 4.73)
revisar("cobertura = 565,656 / 318,10", pd["cobertura_x"], 1.78)
revisar("sin deuda no hay perfil", v.perfil_deuda_vehiculo([], 141.4), None)

print("--- perimetro vigente ---")
from diagnostico_perimetro import ventana_consistente  # noqa: E402
revisar("la ventana arranca en la ultima ruptura", ventana_consistente([2023, 2024], 2017), 2024)
revisar("sin rupturas, desde el primer año con datos", ventana_consistente([], 2019), 2019)
revisar("una sola ruptura (Mineros 2022)", ventana_consistente([2022], 2019), 2022)
revisar("Cementos Argos: 2024-2025 son 2 años y no alcanzan los 4 minimos",
        2025 - v.PERIMETRO_DESDE["CEMENTOS_ARGOS"] + 1 < v.ANIOS_MINIMOS_EBIT, True)
revisar("Mineros: 2022-2025 son justo los 4 minimos", 2025 - v.PERIMETRO_DESDE["MINEROS"] + 1 >= v.ANIOS_MINIMOS_EBIT, True)
revisar("Terpel no tiene ruptura: no figura", "TERPEL" in v.PERIMETRO_DESDE, False)

print("--- minoritario a mercado ---")
# Ultimos 3 anios: (60 + 100 + 140) / 3 = 100; Ke 13 %, g 3 % => 100 / 0,10 = 1.000. El 2022 (900) no entra.
vm, un = v.minoritario_a_mercado({2022: 900.0, 2023: 60.0, 2024: 100.0, 2025: 140.0}, 0.13)
revisar("valor = utilidad promedio de 3 anios / (Ke - g)", (round(vm, 6), round(un, 6)), (1000.0, 100.0))
revisar("utilidad no positiva => sin valor", v.minoritario_a_mercado({2024: -10.0, 2025: 5.0}, 0.13), (None, None))
revisar("sin utilidades => sin valor", v.minoritario_a_mercado({}, 0.13), (None, None))
revisar("spread Ke - g demasiado chico => sin valor", v.minoritario_a_mercado({2025: 100.0}, 0.031), (None, None))
revisar("GEB marcado para minoritario a mercado", "GEB" in v.EMISORES_MINORITARIO_A_MERCADO, True)

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

print("--- DCF explicito de dos etapas (P1) ---")
# Ingresos 1.000, margen 10 %, WACC 10 %, ROIC 20 %, g 3 %, tasa 35 %, 5 anios. NOPAT0 = 65; FCFF_k = 65 x 1,03^k x 0,85.
# VP explicito = 227,78; terminal con ROIC = WACC: NOPAT_6 / WACC = 65 x 1,03^6 / 0,10 = 776,13 -> VP 481,92; EV = 709,70.
d = v.dcf_dos_etapas(1000.0, 0.10, 0.10, 0.20, 300.0, 100.0, 50_000_000)
revisar("DCF EV = VP explicito + VP terminal", round(d["ev"], 1), 709.7)
revisar("DCF patrimonio por accion (409,7 mil millones / 50 M acciones)", round(d["por_accion"], 0), 6194.0)
revisar("peso del terminal", round(d["peso_terminal"], 3), 0.679)
revisar("5 flujos explicitos", len(d["flujos"]), 5)
# ROIC por debajo del WACC se trata como WACC: reinversion g / WACC = 30 % del NOPAT => EV = 669,5
d2 = v.dcf_dos_etapas(1000.0, 0.10, 0.10, 0.05, 300.0, 100.0, 50_000_000)
revisar("ROIC < WACC se piso al WACC (crecimiento neutro, no destructor)", round(d2["ev"], 1), 669.5)
revisar("margen no positivo no se valora", v.dcf_dos_etapas(1000.0, -0.01, 0.10, 0.20, 0.0, 0.0, 1e6)["por_accion"], None)
revisar("WACC - g terminal demasiado chico no se valora", v.dcf_dos_etapas(1000.0, 0.10, 0.05, 0.20, 0.0, 0.0, 1e6)["ev"], None)
revisar("sin ROIC no se valora", v.dcf_dos_etapas(1000.0, 0.10, 0.10, None, 0.0, 0.0, 1e6)["ev"], None)
revisar("el terminal es NOPAT / WACC: sin reinversion explicita el EV sube",
        v.dcf_dos_etapas(1000.0, 0.10, 0.10, 1e9, 0.0, 0.0, 1e6)["ev"] > d["ev"], True)

print("--- margen EBIT normalizado ---")
ing = {2019: 1000.0, 2020: 500.0, 2021: 1000.0, 2022: 1000.0, 2023: 1000.0}
ebt = {2019: 30.0, 2020: 5.0, 2021: 30.0, 2022: 40.0, 2023: 50.0}
m = v.margenes_ebit(ing, ebt)
revisar("margenes anuales", [round(m[a], 3) for a in sorted(m)], [0.03, 0.01, 0.03, 0.04, 0.05])
bajo, central, alto, det = v.margenes_escenarios(m)
# promedio de todos = 3,2 %; moviles de 3 anios: 2,33 / 2,67 / 4,0 %
revisar("central = promedio de TODA la ventana, no la tendencia", round(central, 4), 0.032)
revisar("bajo = peor promedio movil de 3 anios", round(bajo, 4), 0.0233)
revisar("alto = mejor promedio movil de 3 anios", round(alto, 4), 0.04)
revisar("menos de 4 anios no se normaliza", v.margenes_escenarios({2022: 0.03, 2023: 0.04, 2024: 0.05})[1], None)
revisar("anios sin ingresos se omiten", sorted(v.margenes_ebit({2020: 0.0, 2021: 100.0}, {2020: 5.0, 2021: 10.0})), [2021])
esc, det = v.escenarios_dcf(1000.0, m, 0.10, 0.20, 0.0, 0.0, 50_000_000)
revisar("escenarios DCF ordenados bajo < central < alto", esc["bajo"]["por_accion"] < esc["central"]["por_accion"] < esc["alto"]["por_accion"], True)
revisar("sin margen normalizable no hay escenarios", v.escenarios_dcf(1000.0, {2023: 0.03}, 0.10, 0.20, 0.0, 0.0, 1e6)[0], None)

print("--- conciliacion EPV / DCF (menor de los dos) ---")
epv = {"bajo": 100.0, "central": 200.0, "alto": 400.0}
dcf = {"bajo": 40.0, "central": 120.0, "alto": 300.0}
met, pa, av = v.conciliar_epv_dcf(epv, dcf)
revisar("rige el DCF si su central es menor, con su propio rango", (met, pa["bajo"], pa["central"], pa["alto"]), ("dcf", 40.0, 120.0, 300.0))
revisar("difieren mas de 25 %: avisa", len(av), 1)
met, pa, av = v.conciliar_epv_dcf({"bajo": 1.0, "central": 100.0, "alto": 200.0}, {"bajo": 1.0, "central": 110.0, "alto": 200.0})
revisar("rige el EPV si es menor; diferencia < 25 % no avisa", (met, pa["central"], av), ("epv", 100.0, []))
met, pa, av = v.conciliar_epv_dcf(epv, None)
revisar("sin DCF rige el EPV", (met, pa["central"]), ("epv", 200.0))
revisar("sin EPV no se valora (el DCF no lo sustituye)", v.conciliar_epv_dcf(None, dcf)[0], None)
met, pa, av = v.conciliar_epv_dcf(epv, {"bajo": -50.0, "central": 120.0, "alto": 300.0})
revisar("el bajo negativo se lleva a 0 (responsabilidad limitada)", pa["bajo"], 0.0)
met, pa, av = v.conciliar_epv_dcf(epv, {"bajo": -50.0, "central": -10.0, "alto": 30.0})
revisar("DCF central <= 0: el valor queda en 0 y se dice", (met, pa["central"], len(av)), ("dcf", 0.0, 1))
met, pa, av = v.conciliar_epv_dcf(epv, dcf, politica="epv")
revisar("la politica 'epv' revierte al comportamiento anterior", (met, pa["central"]), ("epv", 200.0))

print("--- ROE de bancos sobre patrimonio promedio y sin rupturas (P1) ---")
un = {2021: 100.0, 2022: 120.0, 2023: 130.0, 2024: 140.0, 2025: 150.0}
pat = {2020: 800.0, 2021: 1000.0, 2022: 1100.0, 2023: 1200.0, 2024: 1300.0, 2025: 800.0}
roes, avisos = v.roes_banco(un, pat)
# 2025: patrimonio 800 vs 1300 (-38 %) => ruptura, excluido. 2021: 100 / prom(1000, 800) = 11,11 %; 2022: 120 / 1050 = 11,43 %
revisar("anios validos: 2025 se excluye por ruptura de patrimonio", [a for a, _ in roes], [2021, 2022, 2023, 2024])
revisar("ROE 2021 sobre patrimonio promedio", round(dict(roes)[2021], 4), 0.1111)
revisar("ROE 2022 sobre patrimonio promedio", round(dict(roes)[2022], 4), 0.1143)
revisar("el aviso nombra el anio y el salto", ("2025" in avisos[0], "-38%" in avisos[0]), (True, True))
roes, _ = v.roes_banco({2024: 100.0, 2025: 110.0}, {2024: 1000.0, 2025: 1000.0})
revisar("sin patrimonio previo se usa el de cierre", round(dict(roes)[2024], 3), 0.1)
un2 = {2019: 50.0, 2020: 10.0, 2021: 100.0, 2022: 120.0, 2023: 130.0, 2024: 140.0}
pat2 = {2018: 900.0, 2019: 950.0, 2020: 960.0, 2021: 1000.0, 2022: 1100.0, 2023: 1200.0, 2024: 1300.0}
revisar("la ventana son 5 anios calendario, no 5 validos", [a for a, _ in v.roes_banco(un2, pat2)[0]], [2020, 2021, 2022, 2023, 2024])
revisar("un solo ROE: lista vacia sin datos", v.roes_banco({}, {}), ([], []))
revisar("crecimiento sostenible = ROE x (1 - payout)", round(v.crecimiento_sostenible(0.10, 60.0), 3), 0.04)
revisar("sin payout no hay crecimiento sostenible", v.crecimiento_sostenible(0.10, None), None)

reportar_y_salir()
