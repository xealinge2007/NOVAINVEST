"""Siembra emisores + instrumentos BVC (F2b, §3.4 y §11 del plan) a partir
del universo verificado en `app.services.datos.universo`. Idempotente y
re-ejecutable: usa upsert por clave natural (ticker / slug) en todo, así
que correrlo de nuevo tras agregar un emisor nuevo a universo.py no duplica
nada.

Requiere `db/migrate_f2b_bvc_emisores_instrumentos.sql` ya aplicado en
Supabase (crea `emisores` e `instrumentos`, agrega `activos.cajon`).

Uso: python jobs/seed_emisores_instrumentos.py
(necesita SUPABASE_URL / SUPABASE_SERVICE_KEY en el entorno o en .env)
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.datos import (  # noqa: E402
    EMISORES_BVC,
    INSTRUMENTOS_BVC,
    TICKERS_BVC,
)


def main():
    from app.database import cliente_servicio

    cliente = cliente_servicio()

    print(f"1. Asegurando {len(TICKERS_BVC)} activos BVC (metadatos, sin precios)…")
    for activo in TICKERS_BVC:
        cliente.table("activos").upsert(
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
        ).execute()
    print("   OK")

    print(f"2. Sembrando {len(EMISORES_BVC)} emisores…")
    for emisor in EMISORES_BVC:
        cliente.table("emisores").upsert(
            {"slug": emisor.slug, "nombre": emisor.nombre, "sector": emisor.sector},
            on_conflict="slug",
        ).execute()
    print("   OK")

    print(f"3. Sembrando {len(INSTRUMENTOS_BVC)} instrumentos…")
    emisores_resp = cliente.table("emisores").select("id,slug").execute()
    mapa_emisor_id = {e["slug"]: e["id"] for e in emisores_resp.data}

    activos_resp = cliente.table("activos").select("id,ticker").in_(
        "ticker", [i.ticker for i in INSTRUMENTOS_BVC]
    ).execute()
    mapa_activo_id = {a["ticker"]: a["id"] for a in activos_resp.data}

    faltantes = []
    for instrumento in INSTRUMENTOS_BVC:
        emisor_id = mapa_emisor_id.get(instrumento.emisor_slug)
        activo_id = mapa_activo_id.get(instrumento.ticker)
        if emisor_id is None or activo_id is None:
            faltantes.append((instrumento.ticker, instrumento.emisor_slug))
            continue
        cliente.table("instrumentos").upsert(
            {
                "ticker": instrumento.ticker,
                "emisor_id": emisor_id,
                "activo_id": activo_id,
                "clase": instrumento.clase,
            },
            on_conflict="ticker",
        ).execute()

    if faltantes:
        print(f"   ADVERTENCIA — {len(faltantes)} instrumento(s) sin emisor_id/activo_id resuelto: {faltantes}")
    print(f"   OK ({len(INSTRUMENTOS_BVC) - len(faltantes)}/{len(INSTRUMENTOS_BVC)})")

    print("\nListo. Verificar con: select e.slug, i.ticker, i.clase from instrumentos i join emisores e on e.id = i.emisor_id order by e.slug;")


if __name__ == "__main__":
    main()
