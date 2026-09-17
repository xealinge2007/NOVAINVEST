# -*- coding: utf-8 -*-
"""Prueba del respaldo de "digito pegado" en `extraer()` (F4a, 17-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_digito_pegado.py`.

Necesita el PDF real (el bug es de kerning/espaciado de fuente, no reproducible
con texto sintetico simple) -- se salta con aviso si `C:\\Proyectos\\BVC\\
SIMEV_BVC` no esta disponible en esta maquina.

Caso real: BANCO_DE_BOGOTA/2026-T1_..., pagina 9 (indice 8). El PDF pone las
centenas de mil ("1") a un cuarto de punto de distancia del resto del numero
("49,583.6"), y pdfplumber los separa en dos palabras -- "Total activos 1
49,583.6 1 56,164.4 1 42,238.3" en vez de "149,583.6 156,164.4 142,238.3".
El patron de numero exige separador de miles, asi que el "1" solo nunca
matchea y desaparece en silencio: el activo total se leia 100.000 unidades
mas chico. Antes de esta sesion el archivo quedaba en BALANCE_NO_CUADRA."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.extraccion.extractor_generico import extraer  # noqa: E402

RUTA = Path(
    r"C:\Proyectos\BVC\SIMEV_BVC\BANCO_DE_BOGOTA"
    r"\2026-T1_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf"
)

if not RUTA.exists():
    print(f"AVISO: {RUTA} no existe en esta maquina -- prueba saltada, no falla.")
    sys.exit(0)

fallos = []


def revisar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: esperado={esperado} obtenido={obtenido}")
    if not ok:
        fallos.append(nombre)


r = extraer(RUTA, sector="financiero", anio=2026, periodo="T1")
campos = r["campos"]

revisar("activos_totales", campos["activos_totales"]["valor"], 149583.6)
revisar("pasivos_totales", campos["pasivos_totales"]["valor"], 133113.4)
revisar("patrimonio", campos["patrimonio"]["valor"], 16470.2)
revisar("cuadra_balance", r["cuadra_balance"], True)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
