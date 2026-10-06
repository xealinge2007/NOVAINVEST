# -*- coding: utf-8 -*-
"""Diagnostico de cambios de perimetro en las series anuales (XBRL radicado), 06-oct-2026.

Cada cierre anual Y trae el valor de Y y, como comparativo, el de Y-1 *en el perimetro de Y*. Un RUPTURA en el año k
ocurre cuando el valor propio de k (informe k) y su version reexpresada (informe k+1) difieren de forma material: el
informe k+1 ya mide otra empresa (operaciones discontinuadas, venta de filiales). La version vigente de cada año y < ultimo
viene del informe y+1, asi que solo los años desde la ultima ruptura comparten perimetro con el ultimo cierre:
`desde` = la ultima ruptura k* (su version reexpresada ya esta en el perimetro vigente). Ver db/CRITERIOS_VALORACION.md.

Uso: python jobs/diagnostico_perimetro.py [--emisor X]   (solo lee el corpus XBRL, no escribe en la base)
"""

import argparse
import glob
import os
import re

CARPETA_XBRL = r"C:\Proyectos\BVC\SIMEV_XBRL"
UMBRAL = 0.10            # variacion relativa que se considera ruptura
CONCEPTOS = {"ingresos": "Revenue", "ebit": "ProfitLossFromOperatingActivities", "neta": "ProfitLoss"}
SERIE_PARALELA = re.compile(r"-XBRL-[A-Z]+\.xbrl$")


def valores_del_anio(ruta: str, anio: int) -> dict:
    """{ingresos, ebit, neta} del año completo `anio` en el XBRL `ruta` (valor no cero; sin contextos dimensionales)."""
    t = open(ruta, encoding="utf-8", errors="ignore").read()
    ctx = set()
    for m in re.finditer(r'<(?:\w+:)?context id="([^"]+)">(.*?)</(?:\w+:)?context>', t, re.S):
        if "Member" in m.group(2):
            continue
        s = re.search(r"startDate>([^<]+)<", m.group(2))
        e = re.search(r"endDate>([^<]+)<", m.group(2))
        if s and e and e.group(1) == f"{anio}-12-31" and s.group(1) in (f"{anio}-01-01", f"{anio - 1}-12-31"):
            ctx.add(m.group(1))
    out = {}
    for campo, concepto in CONCEPTOS.items():
        for m in re.finditer(r'<\w+:%s [^>]*contextRef="([^"]+)"[^>]*>(-?\d+)<' % concepto, t):
            if m.group(1) in ctx and int(m.group(2)) != 0:
                out[campo] = int(m.group(2)) / 1e6
    return out


def variacion(a, b):
    if a is None or b is None or a == 0:
        return None
    return (b - a) / abs(a)


def rupturas_de(emisor: str):
    """[(año k, {campo: (propio, reexpresado, variacion)}, es_ruptura)] y {año: ruta} de los cierres anuales."""
    archivos = {}
    for f in glob.glob(os.path.join(CARPETA_XBRL, emisor, "*-ANUAL_*.xbrl")):
        if SERIE_PARALELA.search(f):
            continue
        archivos[int(re.search(r"(\d{4})-ANUAL", f).group(1))] = f
    filas = []
    for k in sorted(archivos):
        if k + 1 not in archivos:
            continue
        propio, rex = valores_del_anio(archivos[k], k), valores_del_anio(archivos[k + 1], k)
        det = {}
        for c in CONCEPTOS:
            if c in propio and c in rex:
                det[c] = (propio[c], rex[c], variacion(propio[c], rex[c]))
        # Ruptura: ventas o EBIT (o la utilidad neta, que es lo que tiene un banco) cambian mas del umbral.
        ruptura = any(v is not None and abs(v) > UMBRAL for (_, _, v) in (det.get("ingresos", (0, 0, None)),
                                                                          det.get("ebit", (0, 0, None))))
        if not det.get("ingresos") and not det.get("ebit"):
            ruptura = det.get("neta", (0, 0, None))[2] is not None and abs(det["neta"][2]) > UMBRAL
        filas.append((k, det, ruptura))
    return filas, archivos


def ventana_consistente(rupturas: list, primer_anio: int) -> int:
    """Primer año de la ventana que comparte perimetro con el ultimo cierre: la ultima ruptura (su version reexpresada ya
    esta en el perimetro vigente) o, sin rupturas, el primer año con datos."""
    return max(rupturas) if rupturas else primer_anio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emisor")
    args = ap.parse_args()
    emisores = [args.emisor] if args.emisor else sorted(os.listdir(CARPETA_XBRL))
    print(f"{'EMISOR':26s} {'RUPTURAS':28s} {'DESDE':6s} AÑOS (hasta el ultimo cierre)")
    for em in emisores:
        filas, archivos = rupturas_de(em)
        if not filas:
            continue
        ult = max(archivos)
        rup = [k for k, _, r in filas if r]
        desde = ventana_consistente(rup, min(archivos))
        print(f"{em[:26]:26s} {str(rup):28s} {desde!s:6s} {ult - desde + 1}")
        for k, det, r in filas:
            if r:
                print("      " + str(k) + ": " + "; ".join(
                    f"{c} {v[0]:,.1f}->{v[1]:,.1f} ({v[2]:+.0%})" for c, v in det.items() if v[2] is not None))


if __name__ == "__main__":
    main()
