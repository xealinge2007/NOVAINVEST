# -*- coding: utf-8 -*-
"""Corre todas las pruebas ejecutables de `jobs/test_*.py` (sin pytest a proposito,
ver `_prueba_utils.py`) y resume el resultado. Sale con 1 si alguna falla.

    python jobs/correr_pruebas.py

Las pruebas que necesitan el corpus local (`C:\\Proyectos\\BVC`) se saltan solas con
aviso cuando no esta; este runner cuenta cuantas se saltaron para que un "todo OK" en
CI no se confunda con una verificacion completa contra los informes reales.
"""

import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def main() -> int:
    archivos = sorted(AQUI.glob("test_*.py"))
    resultados = []
    for arch in archivos:
        p = subprocess.run(
            [sys.executable, str(arch)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        salida = p.stdout + p.stderr
        saltadas = sum(1 for linea in salida.splitlines() if linea.startswith("SALTADA"))
        resultados.append((arch.name, p.returncode, saltadas, salida))

    fallidas = [r for r in resultados if r[1] != 0]
    for nombre, codigo, saltadas, salida in resultados:
        estado = "OK   " if codigo == 0 else "FALLA"
        extra = f"  ({saltadas} saltada(s): falta el corpus local)" if saltadas else ""
        print(f"{estado} {nombre}{extra}")
        if codigo != 0:
            print(salida)

    total_saltadas = sum(r[2] for r in resultados)
    print(f"\n{len(resultados) - len(fallidas)}/{len(resultados)} archivos OK, "
          f"{total_saltadas} comprobacion(es) saltada(s) por falta de corpus")
    return 1 if fallidas else 0


if __name__ == "__main__":
    sys.exit(main())
