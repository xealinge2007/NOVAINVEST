# -*- coding: utf-8 -*-
"""Prueba de `valor_engine.calcular_holding` contra casos reales de NAV
calculados a mano (W3a, 21-sep-2026).

Sin pytest a proposito -- correrse solo: `python jobs/test_valor_engine.py`.
Necesita Supabase alcanzable y los datos de cada holding ya cargados
(`jobs/ingesta_participaciones.py --emisor X` seguido de
`jobs/valor_engine.py --emisor X`) -- cada holding se salta con aviso si
no esta, en vez de fallar toda la prueba.

Las cifras esperadas se calcularon a mano leyendo la Nota de inversiones en
asociadas/subsidiarias y el Estado de situacion financiera separado de cada
informe -- ver `db/DOCTRINA_VALOR.md` (seccion W3a) para el detalle linea
por linea de cada holding. Esta prueba no vuelve a leer los PDF: solo
verifica que lo que quedo en `valor_estimado` coincide con lo calculado a
mano, para detectar una regresion futura en la aritmetica del motor, no un
error de lectura de los documentos.
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
except Exception as e:
    print(f"AVISO: Supabase no alcanzable ({e}) -- prueba saltada, no falla.")
    sys.exit(0)

# slug -> (anio, periodo, nav_mercado esperado, nav_lookthrough esperado)
CASOS = {
    # 2 cotizadas (Cibest a capitalizacion TOTAL, Enka solo directo para no
    # duplicar el 3.70% indirecto ya contado en ICE) + 5 no cotizadas a libro.
    "GRUPO_SURA": (2025, "ANUAL", 12493.0, 30203.3),
    # Cementos Argos (54.98% economico) + Celsia cotizadas + Odinsa/Sator/
    # Summa/Pactia a libro. Grupo Sura ya no aparece (escindida en 2025).
    "GRUPO_ARGOS": (2025, "ANUAL", 11370.3, 14228.6),
    # Banco de Bogota + Corficolombiana (capitalizacion TOTAL, ambas clases)
    # cotizadas + 9 no cotizadas a libro, incluido Grupo Aval Limited con
    # valor en libros NEGATIVO real (patrimonio negativo por perdidas).
    "GRUPO_AVAL": (2025, "ANUAL", 8648.5, 17731.4),
    # Unica cotizada: 2.28% en GEB a valor razonable (FVOCI, ya a mercado) +
    # 12 no cotizadas a libro + residual. NAV-mercado NEGATIVO real: Corfi es
    # estructuralmente un banco (capta depositos) sin holdings cotizados
    # propios significativos -- el pasivo de captacion excede los activos
    # propios no invertidos. NAV-lookthrough coincide exacto con el Total
    # Patrimonio del balance separado (13,198.933), verificacion cruzada.
    "CORFICOLOMBIANA": (2025, "ANUAL", -5564.1, 13198.9),
}

emisores = {e["slug"]: e["id"] for e in cliente.table("emisores").select("id,slug").execute().data}

for slug, (anio, periodo, esperado_mercado, esperado_lookthrough) in CASOS.items():
    if slug not in emisores:
        print(f"AVISO: {slug} no existe en emisores -- prueba saltada, no falla.")
        continue
    fila = cliente.table("valor_estimado").select("*").eq("emisor_id", emisores[slug]).eq(
        "anio", anio
    ).eq("periodo", periodo).execute().data
    if not fila:
        print(f"AVISO: {slug} {anio}-{periodo} no esta en valor_estimado todavia -- prueba saltada, no falla.")
        continue

    f = fila[0]
    revisar(f"{slug}: NAV-mercado", round(f["nav_mercado_mmm"], 1), esperado_mercado)
    revisar(f"{slug}: NAV-lookthrough", round(f["nav_lookthrough_mmm"], 1), esperado_lookthrough)
    revisar(f"{slug}: lookthrough > mercado", f["nav_lookthrough_mmm"] > f["nav_mercado_mmm"], True)
    revisar(f"{slug}: valor_central usa la conservadora (nav_mercado)", f["valor_central_mmm"], f["nav_mercado_mmm"])
    revisar(f"{slug}: determinable", f["determinable"], True)

reportar_y_salir()
