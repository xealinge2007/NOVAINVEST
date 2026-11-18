# -*- coding: utf-8 -*-
"""Lista de XBRL por descargar del SIMEV (V1 del plan v4). Solo lectura del corpus local.

Compara el último período que hay en `C:\\Proyectos\\BVC\\SIMEV_XBRL\\<EMISOR>\\` con el período que ya
debería estar publicado hoy (`ranking_valor.periodo_exigible`) y escribe `PEDIDOS_XBRL.csv` con lo que
falta. También lista el próximo período que vence, con su fecha, para planear la siguiente descarga.

Uso: python jobs/pedidos_xbrl.py [--corpus RUTA] [--hoy AAAA-MM-DD]
"""
import argparse
import csv
import re
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))
from app.services import ranking_valor as rk  # noqa: E402

CORPUS = Path(r"C:\Proyectos\BVC\SIMEV_XBRL")
SIN_XBRL = {"PEI"}  # patrimonio autónomo: no reporta XBRL, se carga por PDF
PATRON = re.compile(r"^(\d{4})-(T[1-4]|ANUAL)_")


def nombre(anio: int, trimestre: int) -> str:
    return f"{anio}-ANUAL" if trimestre == 4 else f"{anio}-T{trimestre}"


def siguiente(anio: int, trimestre: int) -> tuple[int, int]:
    return (anio + 1, 1) if trimestre == 4 else (anio, trimestre + 1)


def vence(anio: int, trimestre: int) -> date:
    if trimestre == 4:
        return date(anio, 12, 31) + timedelta(days=rk.DIAS_PUBLICACION_ANUAL)
    fin = date(anio, trimestre * 3 + 1, 1) - timedelta(days=1)
    return fin + timedelta(days=rk.DIAS_PUBLICACION_INTERMEDIO)


def ultimo_local(carpeta: Path) -> tuple[int, int] | None:
    periodos = []
    for f in carpeta.iterdir():
        m = PATRON.match(f.name)
        if m:
            periodos.append((int(m.group(1)), 4 if m.group(2) == "ANUAL" else int(m.group(2)[1])))
    return max(periodos) if periodos else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--hoy", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if not args.corpus.is_dir():
        sys.exit(f"No existe el corpus {args.corpus}")

    exigible = rk.periodo_exigible(args.hoy)
    proximo = siguiente(*exigible)
    filas = []
    for carpeta in sorted(p for p in args.corpus.iterdir() if p.is_dir()):
        if carpeta.name in SIN_XBRL:
            continue
        ultimo = ultimo_local(carpeta)
        p = siguiente(*ultimo) if ultimo else exigible
        while p <= exigible:
            filas.append({"emisor": carpeta.name, "periodo": nombre(*p), "estado": "vencido",
                          "vence": vence(*p).isoformat()})
            p = siguiente(*p)
        filas.append({"emisor": carpeta.name, "periodo": nombre(*proximo), "estado": "proximo",
                      "vence": vence(*proximo).isoformat()})

    destino = RAIZ / "PEDIDOS_XBRL.csv"
    with open(destino, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["emisor", "periodo", "estado", "vence"])
        w.writeheader()
        w.writerows(filas)

    vencidos = [f for f in filas if f["estado"] == "vencido"]
    print(f"Hoy {args.hoy}: exigible {nombre(*exigible)}; próximo {nombre(*proximo)} vence {vence(*proximo)}.")
    print(f"Vencidos sin descargar: {len(vencidos)}")
    for f in vencidos:
        print(f"  {f['emisor']:28s}{f['periodo']}")
    print(f"Escrito {destino.name} ({len(filas)} filas).")


if __name__ == "__main__":
    main()
