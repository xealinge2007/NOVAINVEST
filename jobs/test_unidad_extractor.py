# -*- coding: utf-8 -*-
"""Pruebas de la resolucion de unidad del extractor generico (F4a).

Sin pytest a proposito -- el repo no tiene infraestructura de pruebas y esto
tiene que poder correrse solo: `python jobs/test_unidad_extractor.py`.

Cubre lo que hizo que TERPEL se investigara mal durante sesiones: la unidad no
siempre esta en el membrete de la pagina del balance. Los casos son los
literales reales de TERPEL 2023-ANUAL (pagina 283 de leyenda, 284 de balance),
no ejemplos inventados.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.extraccion import extractor_generico as eg  # noqa: E402

NL = chr(10)

LEYENDA_TERPEL = NL.join([
    "COP$ : Cifras expresadas en pesos colombianos",
    "USD : Cifras expresadas en dolares estadounidenses",
    "M$ : Cifras expresadas en miles de pesos colombianos",
    "MM$ : Cifras expresadas en millones de pesos colombianos",
    "MUSD : Cifras expresadas en miles de dolares estadounidenses",
])

fallos = []


def revisar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: esperado={esperado} obtenido={obtenido}")
    if not ok:
        fallos.append(nombre)


def _balance(encabezado):
    return NL.join([
        "ORGANIZACION TERPEL S.A. Y SUBORDINADAS",
        "Estados Consolidados de Situacion Financiera, Clasificados",
        "Al 31 de diciembre de 2023 y 2022",
        "Notas 2023 2022",
        encabezado,
        "Total activos 9.337.716.408 10.238.949.515",
    ])


# --- unidad por simbolo de columna, resuelta contra la leyenda ---------------
for encabezado, esperado in [
    ("Activos M$ M$", 0.000001),
    ("Activos MM$ MM$", 0.001),
    ("Activos COP$ COP$", 0.000000001),
    # moneda extranjera: NO se resuelve a proposito -- mejor revision que
    # publicar una tabla en dolares como si fueran pesos.
    ("Activos MUSD MUSD", None),
    # sin simbolo en el encabezado no hay nada que resolver por esta via
    ("Activos corrientes:", None),
]:
    b = _balance(encabezado)
    r = eg._detectar_factor_unidad_por_simbolo(b, [LEYENDA_TERPEL, b], 1)
    revisar(f"simbolo {encabezado!r}", r[0] if r else None, esperado)

# --- la pagina de glosario es ambigua y se descarta --------------------------
revisar("glosario con varias unidades es ambiguo", eg._declara_mas_de_una_unidad(LEYENDA_TERPEL), True)
revisar("declaracion unica no es ambigua",
        eg._declara_mas_de_una_unidad("estados financieros expresados en miles de pesos colombianos"), False)
# "millones de pesos" es substring de "miles de millones de pesos": no debe
# contar como dos unidades distintas.
revisar("miles de millones no cuenta doble",
        eg._declara_mas_de_una_unidad("cifras expresadas en miles de millones de pesos"), False)

# --- el respaldo por prosa salta la pagina ambigua y toma la univoca ---------
paginas = [
    "",
    "estados financieros intermedios consolidados expresados en miles de pesos colombianos",
    LEYENDA_TERPEL,          # ambigua: se salta
    _balance("Activos M$ M$"),
]
r = eg._detectar_factor_unidad_documento(paginas, 3)
revisar("respaldo por prosa salta el glosario", r[0] if r else None, 0.000001)

# --- el membrete clasico sigue igual que siempre (sin regresion) -------------
for texto, esperado in [
    ("Cifras expresadas en miles de millones de pesos", 1.0),
    ("(Valores expresados en millones de pesos colombianos)", 0.001),
    ("Cifras expresadas en miles de pesos", 0.000001),
    ("Estado de situacion financiera", None),
]:
    r = eg._detectar_factor_unidad(NL.join(["TITULO LARGO DEL EMISOR", "Al 31 de diciembre", texto]))
    revisar(f"membrete {texto[:40]!r}", r[0] if r else None, esperado)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
