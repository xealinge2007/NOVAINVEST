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

print("\n--- deuda financiera: una fórmula por emisor, cada una contra su nota ---")
# Cada cifra esperada sale de la nota de obligaciones financieras del informe
# ANUAL CONSOLIDADO 2025 del propio emisor, no de lo que dé el código. Son los
# seis casos que demuestran que NO existe una lista de conceptos común:
#   CELSIA        `Borrowings` sola ya trae el total (bonos incluidos)
#   CEMENTOS_ARGOS `Borrowings` = 0 y las obligaciones EXCLUYEN los bonos
#   GEB           `Borrowings` = solo la porción corriente (22x de menos)
#   MINEROS       `Borrowings` = solo la porción no corriente
#   PROMIGAS      no etiqueta `Borrowings`; solo el par de obligaciones
#   TERPEL        ni lo uno ni lo otro: va en `Other*FinancialLiabilities`
DEUDA_2025 = {
    # emisor: (esperado en MMM, tolerancia relativa, de dónde sale)
    "CELSIA":         (5010.913365, 0.0,     "Nota 18, corriente 1.084,895 + no corriente 3.926,018"),
    "CEMENTOS_ARGOS": (2801.211,    0.0001,  "Nota 20 (854,879) + Nota 26 (1.946,332); la diferencia "
                                             "son 0,091 de acciones preferenciales fuera de BondsIssued"),
    "CONSTRUCTORA_CONCONCRETO": (264.230452, 0.0, "Nota 7.13 consolidada"),
    "ETB":            (852.889908,  0.0,     "Nota 17, corto 176,310 + largo 676,580"),
    "GEB":            (20692.784,   0.0,     "Nota 19, corriente 929,806 + no corriente 19.762,978"),
    "GRUPO_ARGOS":    (9686.308076, 0.0,     "Nota 21 (4.722,405) + Nota 26 (4.963,903)"),
    "MINEROS":        (57.853052,   0.0,     "Nota 27, corriente 40,615 + no corriente 17,238"),
    "PROMIGAS":       (5558.356583, 0.0,     "Nota 19, corriente 767,982 + no corriente 4.790,375"),
    "TERPEL":         (3651.381242, 0.0,     "Nota 24, corriente 623,333 + no corriente 3.028,048"),
}
CORPUS = Path(r"C:\Proyectos\BVC\SIMEV_XBRL")
for emisor, (esperado, tol, origen) in DEUDA_2025.items():
    arch = CORPUS / emisor / "2025-ANUAL_EEFF-Consolidados-XBRL.xbrl"
    if not arch.is_file():
        print(f"SALTADA {emisor}: falta {arch}")
        continue
    obtenido = lx.leer(arch, 2025, "ANUAL", emisor=emisor)["campos"]["deuda_financiera"]["valor"]
    if obtenido is not None and tol and abs(obtenido - esperado) / esperado <= tol:
        print(f"OK   deuda {emisor}: nota={esperado} obtenido={obtenido} (dentro de {tol:.2%}) -- {origen}")
    else:
        revisar(f"deuda {emisor} ({origen})", obtenido, esperado)

print("\n--- la deuda que no se pudo verificar se declara, no se inventa ---")
sin_verificar = lx.leer(CORPUS / "TERPEL" / "2025-ANUAL_EEFF-Consolidados-XBRL.xbrl",
                        2025, "ANUAL", emisor="EMISOR_QUE_NO_EXISTE")
revisar("emisor desconocido -> deuda None",
        sin_verificar["campos"]["deuda_financiera"]["valor"], None)
revisar("y se dice por qué en motivos",
        any("DEUDA_FINANCIERA_POR_EMISOR" in m for m in sin_verificar["motivos"]), True)

hueco = lx.leer(CORPUS / "GRUPO_SURA" / "2025-ANUAL_EEFF-Consolidados-XBRL.xbrl",
                2025, "ANUAL", emisor="GRUPO_SURA")
revisar("emisor con hueco declarado -> None",
        hueco["campos"]["deuda_financiera"]["valor"], None)

print("\n--- el control contra los pasivos descarta las sumas con doble conteo ---")
# ISA: sumar `BondsIssued` aparte de las obligaciones da 62.210 MMM contra unos
# pasivos totales de 47.823 -- es imposible, y es justo la firma de que los
# bonos YA estaban dentro. La fórmula inventada tiene que quedar descartada.
isa = CORPUS / "ISA" / "2025-ANUAL_EEFF-Consolidados-XBRL.xbrl"
if isa.is_file():
    guardado = lx.DEUDA_FINANCIERA_POR_EMISOR["ISA"]
    lx.DEUDA_FINANCIERA_POR_EMISOR["ISA"] = (
        [["ObligacionesFinancierasCorrientes", "ObligacionesFinancierasNoCorrientes", "BondsIssued"]],
        "prueba", "fórmula con doble conteo, a propósito")
    try:
        r_isa = lx.leer(isa, 2025, "ANUAL", emisor="ISA")
        revisar("una suma mayor que los pasivos no se escribe",
                r_isa["campos"]["deuda_financiera"]["valor"], None)
        revisar("y queda dicho en motivos",
                any("exceder los pasivos" in m for m in r_isa["motivos"]), True)
    finally:
        lx.DEUDA_FINANCIERA_POR_EMISOR["ISA"] = guardado
    revisar("con su fórmula real ISA sí trae deuda",
            lx.leer(isa, 2025, "ANUAL", emisor="ISA")["campos"]["deuda_financiera"]["valor"],
            33790.917489)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
