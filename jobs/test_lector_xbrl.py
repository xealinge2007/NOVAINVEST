# -*- coding: utf-8 -*-
"""Pruebas del lector de XBRL (canal D, F4a).

Sin pytest, igual que `test_unidad_extractor.py`: `python jobs/test_lector_xbrl.py`.

Los valores esperados NO son inventados. Son los que el canal de PDF ya
extraía bien de ECOPETROL 2022-ANUAL y que se verificaron contra lo que la
compañía reportó. Que los dos canales coincidan al peso es justo la prueba de
que el mapeo de conceptos NIIF y la escala están bien resueltos.

Si el archivo de muestra no está descargado, la prueba se salta con aviso en
vez de fallar -- el corpus XBRL vive fuera del repo.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.extraccion import lector_xbrl as lx  # noqa: E402

MUESTRA = Path(r"C:\Proyectos\BVC\SIMEV_XBRL\ECOPETROL\2022-ANUAL_EEFF-Consolidados-XBRL.xbrl")

# ECOPETROL 2022 consolidado, en miles de millones de pesos.
ESPERADO_2022 = {
    "activos_totales": 306369.50661,
    "pasivos_totales": 187282.455662,
    "patrimonio": 91034.704849,          # atribuible a la controladora
    "ingresos": 159473.954056,
    "utilidad_operacional": 60092.62863,
    "utilidad_neta": 33406.29119,        # atribuible a la controladora
    "flujo_caja_operativo": 36234.569788,
    "acciones_en_circulacion": 41116694690,
}
# El comparativo, que viene en el mismo archivo.
ESPERADO_2021 = {
    "activos_totales": 244250.094193,
    "ingresos": 91744.07972,
    "utilidad_neta": 16694.683909,
}

fallos = []


def revisar(nombre, obtenido, esperado, tolerancia=1e-6):
    if isinstance(obtenido, (int, float)) and isinstance(esperado, (int, float)) and esperado:
        ok = abs(obtenido - esperado) / abs(esperado) <= tolerancia
    else:
        ok = obtenido == esperado
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: esperado={esperado} obtenido={obtenido}")
    if not ok:
        fallos.append(nombre)


if not MUESTRA.is_file():
    print(f"SALTADA: no está {MUESTRA}")
    print("El corpus XBRL vive fuera del repo. Descárgalo y vuelve a correr.")
    sys.exit(0)

print("--- períodos que trae el archivo ---")
periodos = lx.periodos_disponibles(MUESTRA)
revisar("períodos disponibles", str(periodos), "[(1, 2022), (2, 2021)]")

print("\n--- período del informe (2022) ---")
r = lx.leer(MUESTRA, 2022, "ANUAL", indice_periodo=1)
revisar("escala deducida del archivo", r["xbrl"]["escala"], 1000)
revisar("balance cuadra", r["cuadra_balance"], True)
revisar("sin motivos de revisión", r["motivos"], [])
for campo, valor in ESPERADO_2022.items():
    revisar(campo, r["campos"][campo]["valor"], valor)

print("\n--- comparativo (2021), con la escala heredada ---")
r21 = lx.leer(MUESTRA, 2021, "ANUAL", indice_periodo=2)
revisar("escala heredada", r21["xbrl"]["escala"], 1000)
revisar("balance cuadra", r21["cuadra_balance"], True)
for campo, valor in ESPERADO_2021.items():
    revisar(campo, r21["campos"][campo]["valor"], valor)

print("\n--- el año pedido tiene que coincidir con el del archivo ---")
r_mal = lx.leer(MUESTRA, 2019, "ANUAL", indice_periodo=1)
revisar("rechaza un año que no es el del archivo", bool(r_mal["motivos"]), True)
revisar("y no devuelve campos", r_mal["campos"], {})

print("\n--- la escala se deduce, no se supone ---")
revisar("x1000 desde utilidad por acción", lx._escala_del_archivo(33406291190, 41116694690, 813)[0], 1000)
revisar("x1 si ya viene en pesos", lx._escala_del_archivo(33406291190000, 41116694690, 813)[0], 1)
revisar("None sin con qué deducirla", lx._escala_del_archivo(33406291190, None, None)[0], None)
revisar("None si la razón no es una escala", lx._escala_del_archivo(33406291190, 41116694690, 137)[0], None)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
