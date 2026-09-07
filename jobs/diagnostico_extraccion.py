# -*- coding: utf-8 -*-
"""Diagnostico masivo LOCAL del extractor (F4a). Corre `extractor_generico`
sobre TODO el arbol de PDF de SIMEV, sin tocar Supabase, y clasifica cada
archivo por CAUSA de fallo -- no por sintoma.

Por que existe: la cola de `requiere_revision` (178 archivos) estaba toda
etiquetada con el mismo texto ("no encontro ninguna tabla ancla"), que mezcla
al menos cuatro causas distintas. Investigarlas de a una por sesion no
escala; TERPEL se estudio como si fuera un problema de etiquetas cuando en
realidad fallaba solo por la deteccion de unidad. Esto lo responde de una
corrida y deja un CSV para priorizar.

Uso:
    python jobs/diagnostico_extraccion.py salida.csv [--emisor TERPEL] [--procesos 6]
    python jobs/diagnostico_extraccion.py salida.csv --reintentar previo.csv TIMEOUT --procesos 3

`--reintentar <csv> <CLASE>` rehace SOLO los archivos que en esa corrida
quedaron en esa clase, y copia el resto del CSV tal cual. Existe porque el
paralelismo se cobra su precio en los PDF grandes: con 10 procesos, un
documento de 185-483 paginas tarda mas que el limite y se cuenta como
TIMEOUT aunque a solas corra en 56-96s. Reintentar la clase con menos
procesos separa el limite real del artefacto de medicion.
"""

import concurrent.futures as cf
import csv
import multiprocessing as mp
import os
import re
import sys
import time
import traceback
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_REPO / "apps" / "api"))

RAIZ_PDF = Path(r"C:\Proyectos\BVC\SIMEV_BVC")
TIMEOUT_SEGUNDOS = 240

PATRON_NOMBRE = re.compile(r"^(\d{4})-(ANUAL|T[1-4])_(.+)\.pdf$", re.IGNORECASE)

# Mismo criterio duro de Alex que aplica `extraer_fundamentales._es_separado`:
# solo consolidado. Un nombre que dice "Separados" y NO dice "Consolidados"
# es individual y no entra.
def _es_solo_separado(nombre: str) -> bool:
    n = nombre.lower()
    return ("separad" in n or "individual" in n) and "consolidad" not in n


def _sectores() -> dict:
    from app.services.datos.universo import EMISORES_BVC
    return {e.slug: e.sector for e in EMISORES_BVC}


def _extraer_worker(cola, ruta, sector, anio, periodo):
    try:
        from app.services.extraccion import extractor_generico
        r = extractor_generico.extraer(Path(ruta), sector, anio, periodo)
        cola.put({
            "unidad": r["unidad"],
            "cuadra": r["cuadra_balance"],
            "anclas": r["paginas_usadas"],
            "motivos": r.get("motivos") or [],
            "campos": {k: v["valor"] for k, v in r["campos"].items()},
        })
    except Exception as e:
        cola.put({"excepcion": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-400:]})


def _con_timeout(ruta, sector, anio, periodo):
    cola = mp.Queue()
    proc = mp.Process(target=_extraer_worker, args=(cola, str(ruta), sector, anio, periodo))
    proc.start()
    proc.join(timeout=TIMEOUT_SEGUNDOS)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"excepcion": f"TIMEOUT ({TIMEOUT_SEGUNDOS}s)"}
    return cola.get() if not cola.empty() else {"excepcion": "el proceso murio sin devolver resultado"}


def _clasificar(res: dict) -> str:
    if "excepcion" in res:
        return "TIMEOUT" if res["excepcion"].startswith("TIMEOUT") else "ERROR"
    con_valor = [k for k, v in res["campos"].items() if v is not None]
    if not con_valor:
        motivos = " | ".join(res["motivos"])
        if "no ubico la pagina" in motivos:
            return "SIN_ANCLA_ESCANEADO" if "escaneo" in motivos else "SIN_ANCLA"
        if "unidad no declarada" in motivos:
            return "SIN_UNIDAD"
        if "no se pudo resolver la columna" in motivos:
            return "SIN_COLUMNA"
        return "SIN_ETIQUETAS"
    if res["cuadra"] is False:
        return "BALANCE_NO_CUADRA"
    if res["cuadra"] is None:
        return "PARCIAL_SIN_BALANCE"
    return "OK"


def main():
    destino = Path(sys.argv[1])
    filtro_emisor = None
    if "--emisor" in sys.argv:
        filtro_emisor = sys.argv[sys.argv.index("--emisor") + 1]

    sectores = _sectores()
    tareas = []
    for carpeta in sorted(RAIZ_PDF.iterdir()):
        if not carpeta.is_dir():
            continue
        if filtro_emisor and carpeta.name != filtro_emisor:
            continue
        for pdf in sorted(carpeta.glob("*.pdf")):
            m = PATRON_NOMBRE.match(pdf.name)
            if not m:
                tareas.append((carpeta.name, pdf, None, None, "NOMBRE_NO_PARSEABLE"))
                continue
            if _es_solo_separado(pdf.name):
                tareas.append((carpeta.name, pdf, int(m.group(1)), m.group(2).upper(), "EXCLUIDO_SEPARADO"))
                continue
            tareas.append((carpeta.name, pdf, int(m.group(1)), m.group(2).upper(), None))

    procesos = int(sys.argv[sys.argv.index("--procesos") + 1]) if "--procesos" in sys.argv else max(2, (os.cpu_count() or 4) - 1)
    reintentar_clase = None
    previas: dict = {}
    if "--reintentar" in sys.argv:
        i = sys.argv.index("--reintentar")
        previo, reintentar_clase = Path(sys.argv[i + 1]), sys.argv[i + 2]
        with open(previo, encoding="utf-8-sig") as f:
            previas = {(r["emisor"], r["archivo"]): r for r in csv.DictReader(f)}
        tareas = [t for t in tareas if previas.get((t[0], t[1].name), {}).get("clase") == reintentar_clase]
        print(f"reintentando {len(tareas)} archivos en clase {reintentar_clase}", flush=True)

    print(f"{len(tareas)} archivos, {procesos} en paralelo", flush=True)

    def _una(tarea):
        emisor, pdf, anio, periodo, saltado = tarea
        if saltado:
            return {"emisor": emisor, "archivo": pdf.name, "anio": anio, "periodo": periodo,
                    "clase": saltado, "segundos": 0, "campos": "", "unidad": "", "cuadra": "", "motivo": ""}
        t0 = time.time()
        res = _con_timeout(pdf, sectores.get(emisor, "sin_clasificar"), anio, periodo)
        dt = round(time.time() - t0, 1)
        con_valor = [k for k, v in res.get("campos", {}).items() if v is not None]
        return {
            "emisor": emisor, "archivo": pdf.name, "anio": anio, "periodo": periodo,
            "clase": _clasificar(res), "segundos": dt, "campos": len(con_valor),
            "unidad": res.get("unidad") or "", "cuadra": res.get("cuadra"),
            "motivo": res.get("excepcion") or " | ".join(res.get("motivos") or []),
        }

    # Hilos, no procesos, en este nivel: cada hilo solo espera el `join()` del
    # subproceso que hace el trabajo real, asi que el GIL no estorba y se
    # conserva el timeout matable por archivo.
    filas = []
    with cf.ThreadPoolExecutor(max_workers=procesos) as pool:
        for i, fila in enumerate(pool.map(_una, tareas), 1):
            filas.append(fila)
            print(f"[{i}/{len(tareas)}] {fila['clase']:20s} {fila['segundos']:6.1f}s {fila['emisor']}/{fila['archivo'][:55]}", flush=True)

    if previas:
        por_clave = {(f["emisor"], f["archivo"]): f for f in filas}
        previas.update(por_clave)
        filas = list(previas.values())

    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    from collections import Counter
    print("\n=== RESUMEN POR CLASE ===")
    for clase, n in Counter(f["clase"] for f in filas).most_common():
        print(f"{n:4d}  {clase}")
    print("\n=== FALLOS POR EMISOR ===")
    malos = Counter(f["emisor"] for f in filas if f["clase"] not in ("OK", "EXCLUIDO_SEPARADO"))
    for emisor, n in malos.most_common():
        print(f"{n:4d}  {emisor}")
    print(f"\nCSV: {destino}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
