"""Job de refresco diario (§1 y §5 del plan): trae 3 años de precios del
universo F0 (10 US + 5 BVC + proxy COLCAP + BTC + TRM) y los deja en Supabase.

Corre en GitHub Actions con SUPABASE_URL/SUPABASE_SERVICE_KEY como secrets.
Si esas variables no están (uso local de verificación), escribe en
jobs/_cache_local/ en vez de fallar, para poder probar el pipeline sin
credenciales de Supabase.

Uso: python jobs/refresco_diario.py [--anios N]
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.datos import (  # noqa: E402
    UNIVERSO_F0,
    DefinicionActivo,
    StooqConector,
    TrmConector,
    YfinanceConector,
)

CONECTORES = {
    "yfinance": YfinanceConector(),
    "stooq": StooqConector(),
    "datos_gov_co": TrmConector(),
}

CACHE_LOCAL = Path(__file__).parent / "_cache_local"


def _supabase_configurado() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


def _obtener_precios_con_fallback(activo: DefinicionActivo, desde: date, hasta: date):
    principal = CONECTORES[activo.fuente_principal]
    precios = principal.obtener_precios(activo.ticker, desde, hasta)
    fuente_usada = activo.fuente_principal
    if not precios and activo.fuente_respaldo:
        respaldo = CONECTORES[activo.fuente_respaldo]
        precios = respaldo.obtener_precios(activo.ticker, desde, hasta)
        fuente_usada = activo.fuente_respaldo
    return precios, fuente_usada


def _upsert_supabase(activo: DefinicionActivo, precios, fuente_usada: str):
    from app.database import cliente_servicio

    cliente = cliente_servicio()
    resp_activo = (
        cliente.table("activos")
        .upsert(
            {
                "ticker": activo.ticker,
                "nombre": activo.nombre,
                "clase": activo.clase,
                "mercado": activo.mercado,
                "moneda": activo.moneda,
                "fuente_principal": activo.fuente_principal,
                "fuente_respaldo": activo.fuente_respaldo,
                "cajon": activo.cajon,
            },
            on_conflict="ticker",
        )
        .execute()
    )
    activo_id = resp_activo.data[0]["id"]
    filas = [
        {
            "activo_id": activo_id,
            "fecha": p.fecha.isoformat(),
            "apertura": p.apertura,
            "alto": p.alto,
            "bajo": p.bajo,
            "cierre": p.cierre,
            "cierre_ajustado": p.cierre_ajustado,
            "volumen": p.volumen,
            "fuente": fuente_usada,
        }
        for p in precios
    ]
    if filas:
        cliente.table("precios").upsert(filas, on_conflict="activo_id,fecha").execute()
    return len(filas)


def _upsert_cache_local(activo: DefinicionActivo, precios, fuente_usada: str):
    import pandas as pd

    CACHE_LOCAL.mkdir(exist_ok=True)
    df = pd.DataFrame([p.__dict__ for p in precios])
    if not df.empty:
        df["fuente"] = fuente_usada
    ruta = CACHE_LOCAL / f"{activo.ticker.replace('/', '_')}.parquet"
    df.to_parquet(ruta, index=False)
    return len(df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anios", type=int, default=3)
    args = parser.parse_args()

    hasta = date.today()
    desde = hasta - timedelta(days=365 * args.anios)
    en_supabase = _supabase_configurado()

    print(f"Refresco diario NOVAINVEST — {len(UNIVERSO_F0)} activos, {desde} a {hasta}")
    print(f"Destino: {'Supabase' if en_supabase else 'cache local (' + str(CACHE_LOCAL) + ')'}")

    resumen = []
    for activo in UNIVERSO_F0:
        try:
            precios, fuente_usada = _obtener_precios_con_fallback(activo, desde, hasta)
            if en_supabase:
                n = _upsert_supabase(activo, precios, fuente_usada)
            else:
                n = _upsert_cache_local(activo, precios, fuente_usada)
            estado = "OK" if n > 0 else "VACIO"
            resumen.append((activo.ticker, estado, n, fuente_usada))
        except Exception as e:  # el job no debe morir por un ticker: se reporta y sigue
            resumen.append((activo.ticker, f"ERROR: {type(e).__name__}", 0, "-"))

    print(f"\n{'ticker':<16}{'estado':<10}{'filas':<8}fuente")
    for ticker, estado, n, fuente in resumen:
        print(f"{ticker:<16}{estado:<10}{n:<8}{fuente}")

    fallidos = [r for r in resumen if r[1] != "OK"]
    if en_supabase:
        _registrar_salud(fuentes_usadas={r[3] for r in resumen if r[1] == "OK"}, fallidos=fallidos)
    if fallidos:
        print(f"\n{len(fallidos)} activo(s) sin datos: {[r[0] for r in fallidos]}")
        sys.exit(1)


def _registrar_salud(fuentes_usadas: set[str], fallidos: list[tuple]):
    from app.database import cliente_servicio

    cliente = cliente_servicio()
    for fuente in fuentes_usadas:
        cliente.table("salud_fuentes").insert(
            {
                "fuente": fuente,
                "estado": "degradado" if fallidos else "ok",
                "detalle": f"{len(fallidos)} activo(s) fallido(s) en el run" if fallidos else None,
                "activos_afectados": len(fallidos),
            }
        ).execute()


if __name__ == "__main__":
    main()
