# -*- coding: utf-8 -*-
"""Cruce standalone del Bloque 2 XBRL (2021-2024 T1-T3) contra lector_xbrl.py.
No toca Supabase (sigue inaccesible por SSL). Reporta, por archivo:
  - si lector_xbrl.leer() logra sacar campos para el periodo propio (indice 1)
  - si cuadra_balance
  - la escala deducida por archivo
para poder saber la cobertura real del Bloque 2 antes de cargarlo.
"""
import io
import re
import sys
from pathlib import Path
from collections import defaultdict

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(r"C:\Proyectos\novainvest")
sys.path.insert(0, str(RAIZ / "apps" / "api"))
from app.services.extraccion import lector_xbrl  # noqa: E402

CARPETA_XBRL = Path(r"C:\Proyectos\BVC\SIMEV_XBRL")
PATRON_NOMBRE = re.compile(r"^(\d{4})-(ANUAL|T[1-4])_", re.IGNORECASE)
PATRON_SERIE_PARALELA = re.compile(r"-XBRL-(.+)\.xbrl$", re.IGNORECASE)
BLOQUE2_ANIOS = {2021, 2022, 2023, 2024}
BLOQUE2_PERIODOS = {"T1", "T2", "T3"}

CAMPOS_NUMERICOS = [
    "ingresos", "utilidad_operacional", "utilidad_neta", "ebitda",
    "activos_totales", "pasivos_totales", "patrimonio", "flujo_caja_operativo",
    "deuda_financiera", "acciones_en_circulacion", "dividendos_decretados",
]


def escala_del_emisor(archivos):
    deducidas = set()
    for arch in archivos:
        m = PATRON_NOMBRE.match(arch.name)
        if not m:
            continue
        try:
            e = lector_xbrl.leer(arch, int(m.group(1)), m.group(2).upper())["xbrl"].get("escala")
            if e:
                deducidas.add(e)
        except Exception:
            continue
    if len(deducidas) == 1:
        return deducidas.pop(), None
    if len(deducidas) > 1:
        return None, f"escalas contradictorias {sorted(deducidas)}"
    return None, None


resumen = defaultdict(int)
detalle_fallas = []
detalle_ok = []
por_emisor = defaultdict(lambda: {"ok": 0, "total": 0})

carpetas = sorted(p for p in CARPETA_XBRL.iterdir() if p.is_dir())
for carpeta in carpetas:
    slug = carpeta.name
    archivos_todos = sorted(carpeta.glob("*.xbrl"))
    if not archivos_todos:
        continue
    escala, aviso = escala_del_emisor(archivos_todos)
    if aviso:
        print(f"  [{slug}] AVISO ESCALA: {aviso}")

    for arch in archivos_todos:
        m = PATRON_NOMBRE.match(arch.name)
        if not m:
            continue
        anio, periodo = int(m.group(1)), m.group(2).upper()
        if not (anio in BLOQUE2_ANIOS and periodo in BLOQUE2_PERIODOS):
            continue
        if PATRON_SERIE_PARALELA.search(arch.name):
            continue

        por_emisor[slug]["total"] += 1
        resumen["total_bloque2"] += 1
        try:
            r = lector_xbrl.leer(arch, anio, periodo, indice_periodo=1, escala_conocida=escala)
        except Exception as e:
            resumen["error_excepcion"] += 1
            detalle_fallas.append(f"{slug} {anio}-{periodo}: EXCEPCION {type(e).__name__}: {e}")
            continue

        campos = {c: r["campos"][c]["valor"] for c in CAMPOS_NUMERICOS
                  if c in r["campos"] and r["campos"][c]["valor"] is not None}

        if not campos:
            resumen["sin_cifras"] += 1
            motivo = r.get("motivo") or "sin motivo reportado"
            detalle_fallas.append(f"{slug} {anio}-{periodo}: SIN_CIFRAS ({motivo})")
            continue

        if r.get("cuadra_balance") is False:
            resumen["balance_no_cuadra"] += 1
            detalle_fallas.append(f"{slug} {anio}-{periodo}: BALANCE_NO_CUADRA ({len(campos)} campos)")
            continue

        resumen["ok"] += 1
        por_emisor[slug]["ok"] += 1
        cuadra = r.get("cuadra_balance")
        detalle_ok.append(f"{slug} {anio}-{periodo}: {len(campos)} campos, cuadra_balance={cuadra}, escala={r['xbrl'].get('escala')}")

print("\n" + "=" * 76)
print("RESUMEN BLOQUE 2 (2021-2024 T1-T3), periodo propio, sin tocar Supabase")
print("=" * 76)
for k, v in sorted(resumen.items(), key=lambda x: -x[1]):
    print(f"  {v:4d}  {k}")

print(f"\nCobertura por emisor (ok/total esperado de hasta 12 periodos T1-T3 x 2021-2024):")
for slug in sorted(por_emisor):
    d = por_emisor[slug]
    marca = "  " if d["ok"] == d["total"] else " <-- incompleto"
    print(f"  {slug:26s} {d['ok']:2d}/{d['total']:2d}{marca}")

if detalle_fallas:
    print(f"\n{len(detalle_fallas)} fallas:")
    for f in detalle_fallas:
        print(f"   {f}")

print(f"\n{len(detalle_ok)} OK (primeros 20):")
for o in detalle_ok[:20]:
    print(f"   {o}")
