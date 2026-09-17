# -*- coding: utf-8 -*-
"""Prueba de `_texto_con_digito_pegado_reparado` (F4a, 17-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_digito_pegado.py`.

Necesita el PDF real (el bug es de kerning/espaciado de fuente, no reproducible
con texto sintetico simple) -- se salta con aviso si `C:\\Proyectos\\BVC\\
SIMEV_BVC` no esta disponible en esta maquina.

Prueba SOLO la reparacion de texto, no el pipeline completo de `extraer()`:
BANCO_DE_BOGOTA/2026-T1_..., pagina 9 (indice 8), es el caso real que expuso
el bug ("Total activos 1 49,583.6 1 56,164.4 1 42,238.3" en vez de
"149,583.6 156,164.4 142,238.3" -- el digito de las centenas de mil se pierde
porque el patron de numero exige separador de miles). La reparacion en si
misma es correcta y esta verificada aqui: las tres cifras de la fila quedan
bien pegadas.

**No se prueba `extraer()` end-to-end contra este archivo**: el mismo
documento tiene un bug DISTINTO y sin resolver en la resolucion de columna
(el encabezado tiene columnas "PF" -- proforma -- que no respetan el orden
visual en el texto plano; ver DOCTRINA_VALOR.md). Verificado que aunque la
reparacion de digito pegado es correcta, `extraer()` sobre este archivo
todavia no puede resolver CUAL de las tres columnas reparadas es T1-2026,
y devuelve `None` (correcto -- mejor no resolver que resolver mal, que es
lo que pasaba antes de detectar ese segundo bug)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.extraccion.extractor_generico import _texto_con_digito_pegado_reparado  # noqa: E402

RUTA = Path(
    r"C:\Proyectos\BVC\SIMEV_BVC\BANCO_DE_BOGOTA"
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
    texto = _texto_con_digito_pegado_reparado(pdf.pages[8])

linea_activos = next((l for l in texto.split("\n") if l.startswith("Total activos")), None)
revisar(
    "linea de Total activos reparada",
    linea_activos.startswith("Total activos 149,583.6 156,164.4 142,238.3") if linea_activos else None,
    True,
)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
