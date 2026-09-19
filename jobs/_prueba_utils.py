# -*- coding: utf-8 -*-
"""Utilidades compartidas por las pruebas ejecutables de `jobs/test_*.py`
(sin pytest a proposito -- cada una explica por que en su propio docstring).

Consolida lo que antes se repetia palabra por palabra en cada archivo: el
bootstrap de `sys.path` para poder importar desde `apps/api`, el acumulador
de fallos, la funcion `revisar()` que compara e imprime, y el cierre con el
codigo de salida (1 si algo fallo, 0 si no) que usa quien corra el archivo
a mano o en CI.

Uso, al principio de un `test_*.py`, ANTES de cualquier `from app...`:

    from _prueba_utils import revisar, reportar_y_salir

    ...pruebas, cada una llamando revisar(nombre, obtenido, esperado)...

    reportar_y_salir()
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

FALLOS: list[str] = []


def revisar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: esperado={esperado} obtenido={obtenido}")
    if not ok:
        FALLOS.append(nombre)


def reportar_y_salir():
    print()
    if FALLOS:
        print(f"{len(FALLOS)} prueba(s) fallaron: {FALLOS}")
        sys.exit(1)
    print("todas las pruebas pasaron")
