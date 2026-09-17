# -*- coding: utf-8 -*-
"""Prueba del respaldo de "kerning ancho" en `extraer()` (F4a, 17-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_kerning_ancho.py`.

Necesita el PDF real (el bug es de renderizado de fuente, no reproducible con
texto sintetico) -- se salta con aviso si `C:\\Proyectos\\BVC\\SIMEV_BVC` no
esta disponible en esta maquina.

Caso real: BANCO_DE_BOGOTA/2026-T2_..., pagina 9 (indice 8). El PDF usa un
font/kerning donde pdfplumber corta CADA LETRA como palabra aparte con la
tolerancia por defecto ("E s ta d o d e s itu a c i�n..."), asi que ninguna
etiqueta de SINONIMOS_* iguala nunca aunque la pagina, la columna y la unidad
ya se hayan resuelto bien (los regex que las buscan toleran un espacio
insertado entre digitos). Antes de esta sesion el archivo quedaba en
SIN_ETIQUETAS pese a que el balance esta completo y cuadra."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.extraccion.extractor_generico import extraer  # noqa: E402

RUTA = Path(
    r"C:\Proyectos\BVC\SIMEV_BVC\BANCO_DE_BOGOTA"
    r"\2026-T2_Informe-Periodico-Trimestral-Estados-Financieros-Consolidados-y-Separados.pdf"
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


r = extraer(RUTA, sector="financiero", anio=2026, periodo="T2")
campos = r["campos"]

revisar("activos_totales", campos["activos_totales"]["valor"], 142238.3)
revisar("pasivos_totales", campos["pasivos_totales"]["valor"], 125731.6)
revisar("patrimonio", campos["patrimonio"]["valor"], 16506.7)
revisar("cuadra_balance", r["cuadra_balance"], True)

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallaron: {fallos}")
    sys.exit(1)
print("todas las pruebas pasaron")
