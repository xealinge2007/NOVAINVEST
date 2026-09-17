# -*- coding: utf-8 -*-
"""Prueba del respaldo de "kerning ancho" (`TOLERANCIA_X_LETRA_ESPACIADA`,
F4a, 17-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_kerning_ancho.py`.

Necesita el PDF real (el bug es de renderizado de fuente, no reproducible con
texto sintetico) -- se salta con aviso si `C:\\Proyectos\\BVC\\SIMEV_BVC` no
esta disponible en esta maquina.

Caso real: BANCO_DE_BOGOTA/2026-T2_..., pagina 9 (indice 8). El PDF usa un
font/kerning donde pdfplumber corta CADA LETRA como palabra aparte con la
tolerancia por defecto ("E s ta d o d e s itu a c i�n..."), asi que ninguna
etiqueta de SINONIMOS_* iguala nunca. Con `x_tolerance=8` la etiqueta se
reconstruye limpia.

**Prueba SOLO la reconstruccion del texto, no `extraer()` end-to-end**: este
mismo documento (y su vecino 2026-T1) tienen un bug DISTINTO y sin resolver
en la resolucion de columna -- el encabezado trae columnas "PF" (proforma)
que no respetan el orden visual en el texto plano, ni linea por linea ni
concatenado en bloque (ver DOCTRINA_VALOR.md). Verificado que aunque la
reconstruccion de kerning es correcta, `extraer()` sobre este archivo
todavia no puede resolver CUAL columna es T2-2026 y devuelve `None` --
correcto: mejor no resolver que resolver mal, que es lo que pasaba antes de
encontrar ese segundo bug (esta sesion publico y luego corrigio un falso
"OK" para este mismo archivo con el valor de la columna equivocada)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

RUTA = Path(
    r"C:\Proyectos\BVC\SIMEV_BVC\BANCO_DE_BOGOTA"
    r"\2026-T2_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf"
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


TOLERANCIA_X_LETRA_ESPACIADA = 8.0

with pdfplumber.open(RUTA) as pdf:
    texto_normal = pdf.pages[8].extract_text()
    texto_ancho = pdf.pages[8].extract_text(x_tolerance=TOLERANCIA_X_LETRA_ESPACIADA)

revisar("'Total activos' NO aparece limpio con tolerancia normal (confirma el bug)", "Total activos" in texto_normal, False)
revisar("'Total activos' aparece limpio con tolerancia ancha (confirma el arreglo)", "Total activos" in texto_ancho, True)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
