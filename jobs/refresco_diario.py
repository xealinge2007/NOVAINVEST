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
    """Mira la configuración de la app, no `os.environ` a secas.

    Leyendo el entorno directamente, el job no veía el `.env` de `apps/api` y
    se iba a la caché local sin que las credenciales faltaran de verdad: decía
    "Destino: cache local" y llenaba un directorio que nadie lee, mientras
    `precios` en Supabase se quedaba viejo. Es el mismo error que ya había en
    `config.py` con `env_file=".env"` relativo al cwd, en otro sitio."""
    from app.config import settings

    return bool(settings.supabase_url and settings.supabase_service_key)


def _obtener_precios_con_fallback(activo: DefinicionActivo, desde: date, hasta: date):
    principal = CONECTORES[activo.fuente_principal]
    precios = principal.obtener_precios(activo.ticker, desde, hasta)
    fuente_usada = activo.fuente_principal
    if not precios and activo.fuente_respaldo:
        respaldo = CONECTORES[activo.fuente_respaldo]
        precios = respaldo.obtener_precios(activo.ticker, desde, hasta)
        fuente_usada = activo.fuente_respaldo
    return precios, fuente_usada


UMBRAL_SALTO_SOSPECHOSO = 0.30


def _filtrar_saltos_espurios(precios, ticker: str):
    """Descarta un cierre si se aparta más de 30% del día anterior Y el día
    SIGUIENTE vuelve a estar cerca de ese mismo día anterior -- una ida y
    vuelta de un solo día, la firma de un dato malo de la fuente y no de un
    movimiento de mercado real (que no "revierte" al día siguiente).

    Verificado real: ENKA.CL trajo de Yahoo 19,5 -> 0,0103 -> 19,7 los días
    2025-09-01/02/03 -- un factor de ~1.900x en un día y de vuelta al
    siguiente. Sin este filtro, ese 0,0103 se usaba como retorno diario para
    el beta (salía en 51 en vez de ~0,13) y quedaba como el cierre oficial de
    ese día en `precios`.

    El primer y el último día de la serie no se pueden confirmar (falta un
    vecino) y se dejan tal cual -- mejor no filtrar por falta de evidencia
    que inventar una regla sin poder verificarla."""
    ordenados = sorted(precios, key=lambda p: p.fecha)
    descartar = set()
    for i in range(1, len(ordenados) - 1):
        anterior, actual, siguiente = ordenados[i - 1], ordenados[i], ordenados[i + 1]
        if not (anterior.cierre and actual.cierre and siguiente.cierre):
            continue
        salto_ida = abs(actual.cierre / anterior.cierre - 1)
        salto_vuelta = abs(siguiente.cierre / anterior.cierre - 1)
        if salto_ida > UMBRAL_SALTO_SOSPECHOSO and salto_vuelta <= UMBRAL_SALTO_SOSPECHOSO:
            descartar.add(actual.fecha)
            print(f"  [{ticker}] AVISO: cierre descartado en {actual.fecha} "
                  f"({anterior.cierre:.4g} -> {actual.cierre:.4g} -> {siguiente.cierre:.4g}) "
                  f"-- ida y vuelta de un solo día, dato de la fuente, no de mercado")
    if not descartar:
        return precios
    return [p for p in precios if p.fecha not in descartar]


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
    parser.add_argument(
        "--ticker", type=str, default=None,
        help="uno o varios tickers separados por coma. Sin esto se refresca el universo completo. "
             "Existe para el caso de agregar un activo nuevo: bajar 3 años de un ticker no debería "
             "obligar a rebajar los otros 25.",
    )
    args = parser.parse_args()

    hasta = date.today()
    desde = hasta - timedelta(days=365 * args.anios)
    en_supabase = _supabase_configurado()

    universo = UNIVERSO_F0
    if args.ticker:
        pedidos = {t.strip().upper() for t in args.ticker.split(",")}
        universo = [a for a in UNIVERSO_F0 if a.ticker.upper() in pedidos]
        faltan = pedidos - {a.ticker.upper() for a in universo}
        if faltan:
            print(f"No están en el universo: {sorted(faltan)}")
            sys.exit(1)

    print(f"Refresco diario NOVAINVEST — {len(universo)} activos, {desde} a {hasta}")
    print(f"Destino: {'Supabase' if en_supabase else 'cache local (' + str(CACHE_LOCAL) + ')'}")

    resumen = []
    for activo in universo:
        try:
            precios, fuente_usada = _obtener_precios_con_fallback(activo, desde, hasta)
            precios = _filtrar_saltos_espurios(precios, activo.ticker)
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
