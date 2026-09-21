# -*- coding: utf-8 -*-
"""Prueba de `valor_engine.calcular_holding` contra un caso real de NAV
conocido a mano (W3a, 21-sep-2026): GRUPO_SURA al 31-dic-2025.

Sin pytest a proposito -- correrse solo: `python jobs/test_valor_engine.py`.
Necesita Supabase alcanzable y los datos de GRUPO_SURA ya cargados
(`jobs/ingesta_participaciones.py --emisor GRUPO_SURA` seguido de
`jobs/valor_engine.py --emisor GRUPO_SURA`) -- se salta con aviso si no
estan.

Las cifras esperadas se calcularon a mano leyendo la Nota 9 (Inversiones en
asociadas y subsidiarias) y el Estado de situacion financiera separado del
informe 2025-ANUAL de Grupo Sura -- ver `db/DOCTRINA_VALOR.md` (seccion
W3a) para el detalle linea por linea. Esta prueba no vuelve a leer el PDF:
solo verifica que lo que quedo en `valor_estimado` coincide con lo
calculado a mano, para detectar una regresion futura en la aritmetica del
motor, no un error de lectura del documento.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from _prueba_utils import revisar, reportar_y_salir  # noqa: E402

try:
    from app.database import cliente_servicio
except Exception:
    print("AVISO: no se pudo importar app.database -- prueba saltada, no falla.")
    sys.exit(0)

try:
    cliente = cliente_servicio()
    emisor = cliente.table("emisores").select("id").eq("slug", "GRUPO_SURA").execute().data[0]
    fila = cliente.table("valor_estimado").select("*").eq("emisor_id", emisor["id"]).eq(
        "anio", 2025
    ).eq("periodo", "ANUAL").execute().data
except Exception as e:
    print(f"AVISO: Supabase no alcanzable ({e}) -- prueba saltada, no falla.")
    sys.exit(0)

if not fila:
    print("AVISO: GRUPO_SURA 2025-ANUAL no esta en valor_estimado todavia -- prueba saltada, no falla.")
    sys.exit(0)

f = fila[0]

# Calculado a mano (DOCTRINA_VALOR.md, W3a): 2 participaciones cotizadas
# (Cibest 24.65%, Enka 20.76%) + 5 no cotizadas a libro, mas el neto de
# activos/deuda propios del holding separado (-7,796.977 MMM).
revisar("NAV-mercado (solo cotizadas + neto propio)", round(f["nav_mercado_mmm"], 1), 3869.6)
revisar("NAV-lookthrough (todas + neto propio)", round(f["nav_lookthrough_mmm"], 1), 21579.9)
revisar("balance: lookthrough > mercado (mas participaciones suman valor)",
        f["nav_lookthrough_mmm"] > f["nav_mercado_mmm"], True)
revisar("valor_central usa la conservadora (nav_mercado), no la lookthrough",
        f["valor_central_mmm"], f["nav_mercado_mmm"])
revisar("determinable (las 2 cifras principales SI se pudieron calcular)", f["determinable"], True)

reportar_y_salir()
