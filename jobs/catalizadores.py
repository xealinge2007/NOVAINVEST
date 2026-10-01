# -*- coding: utf-8 -*-
"""Carga `db/semillas/catalizadores.csv` en `catalizadores` y marca
`score_valor.tiene_catalizador_vivo` (Pilar 3, W4).

Un catalizador es un evento puntual (OPA, escision, recompra...) que alguien debe
registrar con su fuente: no se calcula. El CSV lo cura Alex desde "informacion
relevante" de la Superfinanciera; este job solo valida, carga y deriva la puerta
con `app.services.catalizador` (criterio y umbrales documentados alli).

Uso:
  python jobs/catalizadores.py              # prueba en seco: valida y muestra, no escribe
  python jobs/catalizadores.py --aplicar    # inserta eventos nuevos y actualiza score_valor

Idempotente: un evento ya cargado (mismo emisor, tipo, fecha_anuncio y descripcion)
no se duplica. No toca `trampa_descuento` ni `cuadrante`: eso necesita el Pilar R y
el valor (W5).
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.services.catalizador import evaluar_catalizadores, validar_evento  # noqa: E402

CSV = Path(__file__).resolve().parents[1] / "db" / "semillas" / "catalizadores.csv"
NUMERICOS = ("precio_oferta_por_accion", "prima_sobre_mercado_pct", "fraccion_descuento_capturada")


def _vacio_a_none(valor):
    valor = (valor or "").strip()
    return valor or None


def _fila_db(fila: dict, emisor_id: int) -> dict:
    out = {
        "emisor_id": emisor_id,
        "tipo_evento": fila["tipo_evento"],
        "estado": _vacio_a_none(fila.get("estado")) or "anunciado",
        "fecha_anuncio": fila["fecha_anuncio"].strip(),
        "fecha_evento": _vacio_a_none(fila.get("fecha_evento")),
        "descripcion": fila["descripcion"].strip(),
        "fuente": fila["fuente"].strip(),
        "url_fuente": _vacio_a_none(fila.get("url_fuente")),
        "nota_historial_controlante": _vacio_a_none(fila.get("nota_historial_controlante")),
    }
    for c in NUMERICOS:
        v = _vacio_a_none(fila.get(c))
        out[c] = float(v) if v else None
    fm = (_vacio_a_none(fila.get("favorece_minoritario")) or "").lower()
    out["favorece_minoritario"] = {"true": True, "false": False}.get(fm)
    return out


def _clave(r: dict):
    return (r["emisor_id"], r["tipo_evento"], str(r["fecha_anuncio"]), r["descripcion"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true",
                        help="escribe en Supabase (por defecto, solo prueba en seco)")
    args = parser.parse_args()

    with CSV.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    print(f"{len(filas)} fila(s) en {CSV.name}")

    from app.database import cliente_servicio
    cliente = cliente_servicio()
    slugs = {e["slug"]: e["id"] for e in cliente.table("emisores").select("id,slug").execute().data}

    validas, malas = [], 0
    for n, f in enumerate(filas, start=2):
        errores = validar_evento(f)
        if not errores and f["emisor_slug"].strip() not in slugs:
            errores = [f"emisor_slug desconocido: {f['emisor_slug']!r}"]
        if errores:
            malas += 1
            print(f"  fila {n}: RECHAZADA -- {'; '.join(errores)}")
        else:
            validas.append(_fila_db(f, slugs[f["emisor_slug"].strip()]))
    if malas:
        print(f"{malas} fila(s) rechazada(s); corrige el CSV. No se escribe nada.")
        sys.exit(1)

    existentes = cliente.table("catalizadores").select("*").execute().data
    ya = {_clave(r) for r in existentes}
    nuevas = [r for r in validas if _clave(r) not in ya]
    print(f"{len(nuevas)} evento(s) nuevo(s), {len(validas) - len(nuevas)} ya cargado(s)")

    por_emisor: dict = {}
    for r in existentes + nuevas:
        por_emisor.setdefault(r["emisor_id"], []).append(r)
    slug_de = {v: k for k, v in slugs.items()}
    for emisor_id, evs in sorted(por_emisor.items(), key=lambda kv: slug_de[kv[0]]):
        ev = evaluar_catalizadores(evs)
        print(f"  {slug_de[emisor_id]:26s} {ev['nivel']:8s} {ev['motivo']}")

    if not args.aplicar:
        print("\nPrueba en seco: no se escribio nada. Usa --aplicar para cargar.")
        return

    if nuevas:
        cliente.table("catalizadores").insert(nuevas).execute()
    # Un emisor sin eventos queda en False (valor por defecto de la columna).
    score = cliente.table("score_valor").select("id,emisor_id,tiene_catalizador_vivo").execute().data
    cambios = 0
    for s in score:
        vivo = evaluar_catalizadores(por_emisor.get(s["emisor_id"], []))["tiene_catalizador_vivo"]
        if vivo != s["tiene_catalizador_vivo"]:
            cliente.table("score_valor").update({"tiene_catalizador_vivo": vivo}).eq("id", s["id"]).execute()
            cambios += 1
    print(f"\nInsertados {len(nuevas)} evento(s); score_valor actualizado en {cambios} fila(s).")


if __name__ == "__main__":
    main()
