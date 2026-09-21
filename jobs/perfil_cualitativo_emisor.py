"""Perfil cualitativo del emisor (F4q): descripción del negocio, CEO,
noticias de impacto y situación micro/macro para la ficha de Fundamentales
(botón -> detalle, ver apps/web/src/pages/Fundamentales.jsx).

Combina dos fuentes, declaradas por campo en `fuentes`:

1. yfinance (Ticker.info) -- cuando el emisor tiene cobertura: descripción
   (longBusinessSummary) y CEO (companyOfficers). Gratis, verificable y se
   usa siempre que exista.
2. Investigación asistida por IA -- para lo que yfinance no cubre (frecuente
   en emisores BVC medianos/pequeños) y para noticias de impacto y
   situación micro/macro, que yfinance no trae. Se completa a mano en
   `db/perfil_cualitativo_seed.json`, un emisor a la vez, citando la fuente
   consultada. A propósito este script NO llama a ningún LLM en caliente:
   mismo criterio del resto del proyecto de "nunca estimar a ojo" -- cada
   dato debe poder rastrearse a quién lo escribió y de dónde salió, y el
   seed es donde queda ese rastro antes de subirlo.

Uso:
    python jobs/perfil_cualitativo_emisor.py [--seed RUTA]

Estado 21-sep-2026: seed con 6 de ~24 emisores (los de mayor capitalización).
El resto queda pendiente de una siguiente ronda de investigación -- un
emisor sin fila en `perfil_cualitativo_emisor` no rompe nada, el frontend
muestra "todavía no hay perfil" en vez de datos inventados.
"""

import argparse
import io
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

SEED_POR_DEFECTO = RAIZ / "db" / "perfil_cualitativo_seed.json"
CLAVES_CEO = ("chief executive", "ceo", "gerente general", "presidente ejecutivo")


def _ceo_de_officers(officers: list[dict] | None) -> str | None:
    """companyOfficers no siempre marca 'title' de forma consistente -- se
    busca cualquier variante de CEO/gerente general, no un match exacto."""
    if not officers:
        return None
    for o in officers:
        titulo = (o.get("title") or "").lower()
        if any(clave in titulo for clave in CLAVES_CEO):
            return o.get("name")
    return None


def obtener_de_yfinance(ticker: str) -> dict:
    """{} si yfinance no tiene nada usable -- nunca lanza: un emisor sin
    cobertura no debe tumbar el job completo (igual que el resto de
    conectores de datos del proyecto)."""
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).info
    except Exception as e:
        print(f"  yfinance falló para {ticker}: {e}")
        return {}

    resultado = {}
    resumen = info.get("longBusinessSummary")
    if resumen:
        resultado["descripcion"] = resumen
    ceo = _ceo_de_officers(info.get("companyOfficers"))
    if ceo:
        resultado["ceo"] = ceo
    return resultado


def cargar_seed(ruta: Path) -> dict:
    """{slug: {descripcion?, ceo?, noticias_impacto?, situacion_micro?,
    situacion_macro?, fuentes?, confianza?}} -- investigación cargada a
    mano (asistida por IA), un emisor a la vez. Ausente o vacío = todavía
    no investigado para ese emisor."""
    if not ruta.exists():
        return {}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos.pop("_leeme", None)
    return datos


def construir_fila(emisor_id: int, slug: str, de_yfinance: dict, de_seed: dict) -> dict | None:
    """Fusiona yfinance + seed. El seed manda en descripcion/ceo cuando lo
    trae: está en español, citado y curado para esta app, mientras que
    longBusinessSummary de yfinance viene en inglés (Yahoo no traduce
    emisores BVC) -- mezclar idiomas en la ficha sería peor que preferir
    la fuente ya revisada. yfinance solo rellena lo que el seed no trajo
    (huecos de una futura ronda) y aporta lo que el seed nunca tiene
    (verificación adicional). Sin nada de ninguna de las dos fuentes no
    se escribe fila -- el frontend ya maneja "sin perfil todavía" sin
    necesitar una fila vacía."""
    descripcion = de_seed.get("descripcion") or de_yfinance.get("descripcion")
    ceo = de_seed.get("ceo") or de_yfinance.get("ceo")
    noticias = de_seed.get("noticias_impacto", [])
    situacion_micro = de_seed.get("situacion_micro")
    situacion_macro = de_seed.get("situacion_macro")

    if not any([descripcion, ceo, noticias, situacion_micro, situacion_macro]):
        return None

    fuentes = list(de_seed.get("fuentes", []))
    if de_seed.get("descripcion"):
        fuentes.append({"campo": "descripcion", "tipo": "investigacion_ia", "detalle": "seed curado, ver noticias_impacto para citas"})
    elif de_yfinance.get("descripcion"):
        fuentes.append({"campo": "descripcion", "tipo": "yfinance", "detalle": f"Ticker.info de {slug} (en inglés, Yahoo no cubre BVC en español)"})
    if de_seed.get("ceo"):
        fuentes.append({"campo": "ceo", "tipo": "investigacion_ia", "detalle": "seed curado, ver noticias_impacto para citas"})
    elif de_yfinance.get("ceo"):
        fuentes.append({"campo": "ceo", "tipo": "yfinance", "detalle": f"Ticker.info de {slug}"})

    # A diferencia de arriba, esto mira qué terminó EN LA FILA (no qué trajo
    # cada fuente) -- si el seed cubrió todo, yfinance no cuenta aunque haya
    # respondido con datos que quedaron sin usar.
    usa_yfinance = (not de_seed.get("descripcion") and bool(de_yfinance.get("descripcion"))) or (
        not de_seed.get("ceo") and bool(de_yfinance.get("ceo"))
    )
    usa_investigacion = bool(
        de_seed.get("descripcion") or de_seed.get("ceo") or noticias or situacion_micro or situacion_macro
    )
    if usa_yfinance and usa_investigacion:
        generado_por = "mixto"
    elif usa_investigacion:
        generado_por = "investigacion_ia"
    else:
        generado_por = "yfinance"

    return {
        "emisor_id": emisor_id,
        "descripcion": descripcion,
        "ceo": ceo,
        "noticias_impacto": noticias,
        "situacion_micro": situacion_micro,
        "situacion_macro": situacion_macro,
        "fuentes": fuentes,
        "generado_por": generado_por,
        "confianza": de_seed.get("confianza", "media"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=SEED_POR_DEFECTO)
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    seed = cargar_seed(args.seed)

    emisores = cliente.table("emisores").select("id, slug, nombre").eq("activo", True).execute().data
    tickers = {
        f["slug"]: f["ticker"] for f in cliente.table("fundamentales_analisis").select("slug, ticker").execute().data
    }

    filas = []
    for e in emisores:
        slug = e["slug"]
        ticker = tickers.get(slug)
        de_yfinance = obtener_de_yfinance(ticker) if ticker else {}
        de_seed = seed.get(slug, {})
        fila = construir_fila(e["id"], slug, de_yfinance, de_seed)
        if fila:
            filas.append(fila)
            print(f"{slug}: {fila['generado_por']}")
        else:
            print(f"{slug}: sin datos (ni yfinance ni seed) -- se omite")

    if not filas:
        print("Nada para escribir.")
        return

    cliente.table("perfil_cualitativo_emisor").upsert(filas, on_conflict="emisor_id").execute()
    print(f"\n{len(filas)} perfiles escritos en perfil_cualitativo_emisor.")


if __name__ == "__main__":
    main()
