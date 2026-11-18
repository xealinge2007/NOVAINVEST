# -*- coding: utf-8 -*-
"""Recalcula el ranking de valor completo, en orden (V1 del plan v4).

Corre, con los precios ya cargados por `refresco_diario.py`:
  analizador_fundamental -> evolucion_fundamental -> solidez_financiera
  -> valoracion_por_accion -> valor_engine (cada holding) -> ranking_valor

Se detiene en el primer paso que falle y sale con código distinto de 0, para que el
workflow quede en rojo y no se publique un ranking a medias.

Uso: python jobs/recalcular_ranking.py
"""
import subprocess
import sys
import time
from pathlib import Path

JOBS = Path(__file__).resolve().parent
sys.path.insert(0, str(JOBS.parent / "apps" / "api"))

PASOS = [
    ["analizador_fundamental.py"],
    ["evolucion_fundamental.py"],
    ["solidez_financiera.py"],
    ["valoracion_por_accion.py"],
]


def holdings() -> list[str]:
    """Holdings que se valoran por suma de partes. Excluye los que `valoracion.ARQUETIPO_VALORACION`
    reclasifica (GEB es holding en la tabla pero se valora como operativa con EPV/DCF)."""
    from app.database import cliente_servicio
    from app.services.valoracion import ARQUETIPO_VALORACION
    filas = cliente_servicio().table("emisores").select("slug,arquetipo").execute().data
    return sorted(f["slug"] for f in filas
                  if ARQUETIPO_VALORACION.get(f["slug"], f.get("arquetipo")) == "holding")


def correr(args: list[str]) -> None:
    inicio = time.time()
    print(f"\n=== {' '.join(args)}", flush=True)
    r = subprocess.run([sys.executable, str(JOBS / args[0]), *args[1:]], cwd=JOBS.parent)
    if r.returncode != 0:
        print(f"FALLÓ {' '.join(args)} (código {r.returncode}); el ranking no se recalculó.", flush=True)
        sys.exit(r.returncode)
    print(f"--- ok en {time.time() - inicio:.0f} s", flush=True)


def main() -> None:
    for paso in PASOS:
        correr(paso)
    lista = holdings()
    if not lista:
        print("FALLÓ: no hay emisores con arquetipo 'holding'; revisar la tabla emisores.")
        sys.exit(1)
    for slug in lista:
        correr(["valor_engine.py", "--emisor", slug])
    correr(["ranking_valor.py"])


if __name__ == "__main__":
    main()
