"""Job de refresco de velas 4h (§3.5, F3): trae velas intradía de 4h del
universo F0 (solo los activos cuya fuente principal es yfinance — TRM no
aplica, es EOD de datos.gov.co) y las deja en `velas_4h`.

yfinance topa el histórico intradía en ~730 días (~2 años), no 3 como el EOD
de `precios` — límite documentado de la API gratuita, no del código.

Corre en GitHub Actions cada 4h en horario de mercado, con SUPABASE_URL/
SUPABASE_SERVICE_KEY como secrets. Sin esas variables (uso local de
verificación), escribe en jobs/_cache_local/ igual que refresco_diario.py.

Uso: python jobs/refresco_4h.py [--dias N]
"""

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.datos import UNIVERSO_F0, YfinanceConector  # noqa: E402

CONECTOR = YfinanceConector()
CACHE_LOCAL = Path(__file__).parent / "_cache_local"
UNIVERSO_4H = [a for a in UNIVERSO_F0 if a.fuente_principal == "yfinance"]


def _supabase_configurado() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


def _upsert_supabase(ticker: str, velas) -> int:
    from app.database import cliente_servicio

    cliente = cliente_servicio()
    resp_activo = cliente.table("activos").select("id").eq("ticker", ticker).execute()
    if not resp_activo.data:
        return 0  # el activo debe existir ya (lo crea refresco_diario.py)
    activo_id = resp_activo.data[0]["id"]
    filas = [
        {
            "activo_id": activo_id,
            "fecha_hora": v.fecha_hora.isoformat(),
            "apertura": v.apertura,
            "alto": v.alto,
            "bajo": v.bajo,
            "cierre": v.cierre,
            "volumen": v.volumen,
            "fuente": "yfinance",
        }
        for v in velas
    ]
    if filas:
        cliente.table("velas_4h").upsert(filas, on_conflict="activo_id,fecha_hora").execute()
    return len(filas)


def _upsert_cache_local(ticker: str, velas) -> int:
    import pandas as pd

    CACHE_LOCAL.mkdir(exist_ok=True)
    df = pd.DataFrame([v.__dict__ for v in velas])
    ruta = CACHE_LOCAL / f"{ticker.replace('/', '_')}_4h.parquet"
    df.to_parquet(ruta, index=False)
    return len(df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dias", type=int, default=730)
    args = parser.parse_args()

    en_supabase = _supabase_configurado()
    print(f"Refresco 4h NOVAINVEST — {len(UNIVERSO_4H)} activos, ventana {args.dias}d")
    print(f"Destino: {'Supabase' if en_supabase else 'cache local (' + str(CACHE_LOCAL) + ')'}")

    resumen = []
    for activo in UNIVERSO_4H:
        try:
            velas = CONECTOR.obtener_velas_4h(activo.ticker, args.dias)
            n = _upsert_supabase(activo.ticker, velas) if en_supabase else _upsert_cache_local(activo.ticker, velas)
            resumen.append((activo.ticker, "OK" if n > 0 else "VACIO", n))
        except Exception as e:  # un ticker fallido no debe tumbar el job completo
            resumen.append((activo.ticker, f"ERROR: {type(e).__name__}", 0))

    print(f"\n{'ticker':<16}{'estado':<10}filas")
    for ticker, estado, n in resumen:
        print(f"{ticker:<16}{estado:<10}{n}")

    fallidos = [r for r in resumen if r[1] != "OK"]
    if fallidos:
        print(f"\n{len(fallidos)} activo(s) sin velas 4h: {[r[0] for r in fallidos]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
