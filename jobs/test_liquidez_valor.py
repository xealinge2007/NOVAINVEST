# -*- coding: utf-8 -*-
"""Pruebas de la puerta de liquidez del ranking (mediana, sesiones con negociacion y tamano maximo)."""

import pandas as pd

from _prueba_utils import revisar, reportar_y_salir

from app.services.liquidez import liquidez_valor  # noqa: E402


def serie(montos_millones, cierre=1000.0):
    return pd.DataFrame({"cierre": [cierre] * len(montos_millones),
                         "volumen": [m * 1e6 / cierre for m in montos_millones]})


r = liquidez_valor(serie([200.0] * 20))
revisar("mediana de 200 M con 20 sesiones pasa", r["ok"], True)
revisar("tamano maximo = 0,5 x mediana", round(r["tamano_maximo_cop"] / 1e6, 1), 100.0)

r = liquidez_valor(serie([100.0] * 20))
revisar("mediana de 100 M no pasa", r["ok"], False)

# Media alta por bloques, mediana baja (el caso Promigas): no pasa
r = liquidez_valor(serie([20.0] * 17 + [3000.0, 3000.0, 3000.0]))
revisar("media inflada por bloques pero mediana de 20 M no pasa", r["ok"], False)

# Conconcreto: mediana 248 M, media 496 M -> pasa con el piso de mediana
conc = [27, 55, 205, 195, 112, 291, 100, 297, 96, 183, 517, 561, 194, 128, 384, 1871, 1433, 766, 817, 1690]
r = liquidez_valor(serie([float(x) for x in conc]))
revisar("Conconcreto: mediana 248 M pasa", (r["ok"], round(r["mediana_cop"] / 1e6)), (True, 248))

# Buena mediana pero pocas sesiones con negociacion
r = liquidez_valor(serie([300.0] * 10 + [0.0] * 10))
revisar("solo 10 de 20 sesiones con negociacion no pasa", r["ok"], False)
revisar("sin datos no pasa", liquidez_valor(pd.DataFrame())["ok"], False)

reportar_y_salir()
