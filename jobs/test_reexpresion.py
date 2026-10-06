# -*- coding: utf-8 -*-
"""Pruebas de la politica de reexpresion de cierres anuales (extraer_xbrl.decidir_reexpresion). Sin base de datos."""

from _prueba_utils import revisar, reportar_y_salir

from extraer_xbrl import decidir_reexpresion  # noqa: E402

print("--- correccion contable: manda el comparativo (Conconcreto 2021, nota 2.7 de los EEFF 2022) ---")
original = {"ingresos": 754.151, "utilidad_operacional": 74.254, "utilidad_neta": 48.3, "patrimonio": 1607.7,
            "acciones_en_circulacion": 1_134_254_939}
reexpresado = {"ingresos": 812.246, "utilidad_operacional": -250.236, "utilidad_neta": -200.4, "patrimonio": 1358.1,
               "acciones_en_circulacion": 1_100_000_000}
f, estado, detalle = decidir_reexpresion(original, reexpresado)
revisar("estado aplicada (ventas +7,7 %, por debajo del umbral)", estado, "aplicada")
revisar("el EBIT es el reexpresado", f["utilidad_operacional"], -250.236)
revisar("el patrimonio tambien", f["patrimonio"], 1358.1)
revisar("el conteo de acciones NO se reexpresa", f["acciones_en_circulacion"], 1_134_254_939)
revisar("el detalle dice el cambio de EBIT", "utilidad_operacional 74.3 -> -250.2" in detalle, True)

print("--- cambio de perimetro: se conserva el original (Cementos Argos 2023) ---")
orig = {"ingresos": 12717.3, "utilidad_operacional": 1640.4, "utilidad_neta": 319.9}
nuevo = {"ingresos": 3916.0, "utilidad_operacional": 467.3, "utilidad_neta": 241.5}
f, estado, _ = decidir_reexpresion(orig, nuevo)
revisar("ventas -69 %: no se aplica", estado, "no_aplicada")
revisar("queda el EBIT original", f["utilidad_operacional"], 1640.4)
revisar("justo en el umbral (10 %) todavia se aplica", decidir_reexpresion({"ingresos": 100.0}, {"ingresos": 110.0})[1], "aplicada")
revisar("apenas por encima del umbral no se aplica", decidir_reexpresion({"ingresos": 100.0}, {"ingresos": 110.5})[1], "no_aplicada")

print("--- financieros: el umbral mira la utilidad neta ---")
revisar("banco con neta -65 %: no se aplica", decidir_reexpresion({"utilidad_neta": 4086.8}, {"utilidad_neta": 1444.7}, financiero=True)[1], "no_aplicada")
revisar("banco sin ventas: un cambio de EBIT no dispara el umbral", decidir_reexpresion({"utilidad_operacional": 100.0, "utilidad_neta": 50.0},
                                                                                      {"utilidad_operacional": 300.0, "utilidad_neta": 50.0}, financiero=True)[1], "aplicada")

print("--- sin cambios ni huecos ---")
f, estado, _ = decidir_reexpresion({"ingresos": 100.0, "utilidad_neta": 10.0}, {"ingresos": 100.5, "utilidad_neta": 10.0})
revisar("diferencia menor al 2 %: sin cambio", estado, "sin_cambio")
f, estado, _ = decidir_reexpresion({"ingresos": 100.0, "utilidad_neta": 10.0, "efectivo": 5.0}, {"ingresos": 100.0})
revisar("el comparativo mas pobre no borra lo que el original traia", (f["utilidad_neta"], f["efectivo"]), (10.0, 5.0))
f, estado, _ = decidir_reexpresion({}, {"ingresos": 100.0})
revisar("sin original previo toma el comparativo", (f["ingresos"], estado), (100.0, "sin_cambio"))

reportar_y_salir()
