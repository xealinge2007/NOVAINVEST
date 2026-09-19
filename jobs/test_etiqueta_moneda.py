# -*- coding: utf-8 -*-
"""Pruebas de `separar_etiqueta_y_valores_linea` cuando el simbolo de moneda
queda pegado al final de la etiqueta (F4a, 16-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_etiqueta_moneda.py`.

Los casos son literales reales: PEI ("$", ya cubierto antes de esta sesion) y
GRUPO_AVAL ("Ps.", pagina 169 de 2022-ANUAL_Informe-Fin-Ejercicio-Estados-
Financieros-Consolidados-y-Separados.pdf, via pdfplumber). Antes de esta
sesion "Total activos Ps." no igualaba "total activos" en el match exacto de
`SINONIMOS_ACTIVOS`, y GRUPO_AVAL quedaba en PARCIAL_SIN_BALANCE en sus 3
anuales pese a que el triage ubicaba la pagina correcta.
"""

from _prueba_utils import revisar, reportar_y_salir  # noqa: E402

from app.services.extraccion.pdf_utils import (  # noqa: E402
    normalizar,
    separar_etiqueta_y_valores_linea,
)

for linea, etiqueta_esperada, valores_esperados in [
    # GRUPO_AVAL real, 2022-ANUAL pagina 169 via pdfplumber.
    ("Total activos Ps. 295,591,236 Ps. 366,903,925", "totalactivos", [295591236.0, 366903925.0]),
    # PEI real, ya cubierto -- no debe regresionar.
    ("Total activos $ 7,605,743,284 $ 6,929,937,332", "totalactivos", [7605743284.0, 6929937332.0]),
    # Sin simbolo de moneda: el caso normal del corpus no debe tocarse.
    ("Total pasivos 100,000,000 90,000,000", "totalpasivos", [100000000.0, 90000000.0]),
]:
    etiqueta, valores = separar_etiqueta_y_valores_linea(linea)
    revisar(f"etiqueta de {linea[:35]!r}", normalizar(etiqueta), etiqueta_esperada)
    revisar(f"valores de {linea[:35]!r}", valores, valores_esperados)

reportar_y_salir()
