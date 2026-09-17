# -*- coding: utf-8 -*-
"""Prueba de `_indice_columna_por_coordenadas` (F4a, 17-sep-2026).

Sin pytest a proposito -- correrse solo:
`python jobs/test_columna_por_coordenadas.py`.

A diferencia de las otras pruebas de este modulo, esta necesita un objeto
`pagina` real de pdfplumber (la funcion agrupa por coordenada x0/top, no
sobre texto plano) -- se abre el archivo real del corpus en vez de simular
un caso sintetico. Se salta con aviso (no falla) si el archivo no esta
disponible localmente, para no romper una corrida en una maquina sin
`C:\\Proyectos\\BVC\\SIMEV_BVC`.

Caso real: CORFICOLOMBIANA/2026-T1_..., pagina 89 (indice 88). El encabezado
de fecha llega intercalado letra por letra entre las dos columnas ("Al 31 d",
"0 2", "a rzo de Al 31", "e mbre") -- ni `extract_text()` ni
`extract_text(layout=True)` lo resuelven. Antes de esta sesion el documento
completo (3 periodos: 2025-ANUAL, 2026-T1, 2026-T2) quedaba en
PARCIAL_SIN_BALANCE con "no se pudo resolver la columna" pese a que el
triage ya ubicaba bien la pagina."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.extraccion.extractor_generico import _indice_columna_por_coordenadas  # noqa: E402

RUTA = Path(
    r"C:\Proyectos\BVC\SIMEV_BVC\CORFICOLOMBIANA"
    r"\2026-T1_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf"
)

if not RUTA.exists():
    print(f"AVISO: {RUTA} no existe en esta maquina -- prueba saltada, no falla.")
    sys.exit(0)

import pdfplumber  # noqa: E402

fallos = []


def revisar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: esperado={esperado} obtenido={obtenido}")
    if not ok:
        fallos.append(nombre)


with pdfplumber.open(RUTA) as pdf:
    pagina = pdf.pages[88]  # ancla real del triage para este documento
    revisar("columna de T1 2026 (izquierda, marzo)", _indice_columna_por_coordenadas(pagina, 2026, "T1"), 0)
    revisar("columna de ANUAL 2025 (derecha, diciembre)", _indice_columna_por_coordenadas(pagina, 2025, "ANUAL"), 1)
    revisar("año que no aparece en el encabezado", _indice_columna_por_coordenadas(pagina, 2019, "ANUAL"), None)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
