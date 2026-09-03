"""Ingesta de PDF trimestrales desde C:\\Proyectos\\BVC\\SIMEV_BVC (§5.1, F4a):
recorre cada carpeta de emisor, infiere periodo/tipo del nombre del archivo
(patrón `AAAA-PERIODO_Tipo-Documento.pdf` — verificado contra los 408
archivos reales del corpus: el patrón aguanta sin excepciones, aunque el
fragmento "Tipo" a veces trae de regalo el nombre del emisor en medio,
ej. `2023-T1_BANCOLOMBIA_Informe-Periodico-Trimestral.pdf`) y encola cada
uno en `ingesta_cola` para que un job de procesamiento (fuera del alcance de
este script) lo extraiga y valide.

El nombre es pista, no verdad: el periodo/tipo inferidos aquí se confirman
contra el encabezado del documento en la etapa de extracción, no aquí.

Idempotente y re-ejecutable (§5.1.1: "el universo crece entre corridas"):
- Un archivo ya registrado (mismo emisor + nombre de archivo) se omite por
  completo — no se reinserta en `reportes_archivo` ni se vuelve a encolar,
  así que su estado de procesamiento/validación nunca se pisa.
- Un emisor nuevo (carpeta que `emisores` no conocía) se crea sobre la
  marcha — el pipeline no depende de una lista fija en código.

Uso: python jobs/ingesta_simev.py [--carpeta RUTA] [--dry-run]
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.datos import EMISORES_BVC  # noqa: E402

CARPETA_DEFAULT = Path(r"C:\Proyectos\BVC\SIMEV_BVC")

MAPA_EMISORES_CONOCIDOS = {e.slug: e for e in EMISORES_BVC}

# Orden de carga sugerido por peso en el COLCAP (§5.1.1) — menor número = mayor prioridad.
PRIORIDAD_TANDA_1 = {
    "ECOPETROL", "GRUPO_CIBEST_BANCOLOMBIA", "ISA", "GRUPO_SURA", "GRUPO_ARGOS",
    "CEMENTOS_ARGOS", "CELSIA", "CORFICOLOMBIANA", "GEB", "GRUPO_AVAL", "DAVIVIENDA_GROUP",
}
PRIORIDAD_TANDA_2 = {
    "PROMIGAS", "TERPEL", "MINEROS", "GRUPO_NUTRESA", "BANCO_DE_BOGOTA",
    "BANCO_DE_OCCIDENTE", "CANACOL", "ETB", "CONSTRUCTORA_CONCONCRETO", "PEI",
}

PATRON_NOMBRE = re.compile(r"^(\d{4})-(.+)$")
PERIODOS_VALIDOS = {"T1", "T2", "T3", "T4", "ANUAL"}

# Clasificación de tipo_documento (§5.1: precedencia — estados financieros e
# informe periódico mandan; comunicado de prensa solo da contexto). Orden
# importa: se evalúa de arriba hacia abajo, gana el primer match.
REGLAS_TIPO_DOCUMENTO = [
    (re.compile(r"^Aviso", re.IGNORECASE), "aviso"),
    (re.compile(r"Estados[-_]?Financieros|EEFF", re.IGNORECASE), "estados_financieros"),
    (
        re.compile(
            r"Informe[-_]?Periodico|Reporte[-_]?Financiero[-_]?Trimestral|"
            r"Informe[-_]?Fin[-_]?(de[-_]?)?Ejercicio|Informe[-_]?(de[-_]?)?Gestion|"
            r"(Informe|Reporte)[-_]?Integrado[-_]?Gestion",
            re.IGNORECASE,
        ),
        "informe_periodico",
    ),
    (
        re.compile(r"Comunicado|Presentacion[-_]?Resultados|Informe[-_]?Resultados|Conference[-_]?Call", re.IGNORECASE),
        "comunicado_prensa",
    ),
]


def clasificar_tipo_documento(tipo_crudo: str) -> str:
    for patron, tipo in REGLAS_TIPO_DOCUMENTO:
        if patron.search(tipo_crudo):
            return tipo
    return "otro"


def prioridad_emisor(slug: str) -> int:
    if slug in PRIORIDAD_TANDA_1:
        return 10
    if slug in PRIORIDAD_TANDA_2:
        return 50
    return 100


def parsear_nombre_archivo(nombre_archivo: str) -> dict | None:
    """Devuelve {anio, periodo, tipo_documento, tipo_documento_crudo} o None
    si el nombre no sigue el patrón mínimo `AAAA-PERIODO_Tipo.pdf`."""
    if not nombre_archivo.lower().endswith(".pdf"):
        return None
    sin_ext = nombre_archivo[:-4]
    partes = sin_ext.split("_", 1)
    if len(partes) != 2:
        return None
    izquierda, tipo_crudo = partes
    m = PATRON_NOMBRE.match(izquierda)
    if not m:
        return None
    anio_str, periodo = m.groups()
    anio = int(anio_str)
    if periodo not in PERIODOS_VALIDOS or not (2000 <= anio <= 2100):
        return None
    return {
        "anio": anio,
        "periodo": periodo,
        "tipo_documento": clasificar_tipo_documento(tipo_crudo),
        "tipo_documento_crudo": tipo_crudo,
    }


def _hash_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _nombre_por_defecto(slug: str) -> str:
    return slug.replace("_", " ").title()


def _asegurar_emisor(cliente, slug: str, cache: dict) -> int:
    if slug in cache:
        return cache[slug]
    existente = cliente.table("emisores").select("id").eq("slug", slug).execute()
    if existente.data:
        cache[slug] = existente.data[0]["id"]
        return cache[slug]

    conocido = MAPA_EMISORES_CONOCIDOS.get(slug)
    fila = {
        "slug": slug,
        "nombre": conocido.nombre if conocido else _nombre_por_defecto(slug),
        "sector": conocido.sector if conocido else "sin_clasificar",
    }
    resp = cliente.table("emisores").insert(fila).execute()
    emisor_id = resp.data[0]["id"]
    cache[slug] = emisor_id
    if not conocido:
        print(f"  [emisor nuevo] '{slug}' no estaba en EMISORES_BVC — creado con sector='sin_clasificar', revisar a mano")
    return emisor_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carpeta", type=Path, default=CARPETA_DEFAULT)
    parser.add_argument("--dry-run", action="store_true", help="solo reporta, no escribe en Supabase")
    args = parser.parse_args()

    if not args.carpeta.is_dir():
        print(f"No existe la carpeta {args.carpeta}")
        sys.exit(1)

    carpetas_emisor = sorted(p for p in args.carpeta.iterdir() if p.is_dir())
    print(f"Ingesta SIMEV_BVC — {len(carpetas_emisor)} carpetas de emisor en {args.carpeta}")

    cliente = None
    if not args.dry_run:
        from app.database import cliente_servicio

        cliente = cliente_servicio()

    cache_emisores: dict[str, int] = {}
    nuevos, ya_existian, sin_patron, errores = 0, 0, [], []

    for carpeta_emisor in carpetas_emisor:
        slug = carpeta_emisor.name
        pdfs = sorted(carpeta_emisor.glob("*.pdf"))
        if not pdfs:
            continue

        emisor_id = None
        if not args.dry_run:
            emisor_id = _asegurar_emisor(cliente, slug, cache_emisores)

        for pdf in pdfs:
            meta = parsear_nombre_archivo(pdf.name)
            if meta is None:
                sin_patron.append(str(pdf.relative_to(args.carpeta)))
                continue

            if args.dry_run:
                nuevos += 1
                continue

            existente = (
                cliente.table("reportes_archivo")
                .select("id,estado")
                .eq("emisor_id", emisor_id)
                .eq("nombre_archivo", pdf.name)
                .execute()
            )
            if existente.data:
                ya_existian += 1
                continue

            try:
                hash_archivo = _hash_archivo(pdf)
                fila = {
                    "emisor_id": emisor_id,
                    "nombre_archivo": pdf.name,
                    "ruta_local": str(pdf),
                    "hash_sha256": hash_archivo,
                    "anio": meta["anio"],
                    "periodo": meta["periodo"],
                    "tipo_documento": meta["tipo_documento"],
                    "tipo_documento_crudo": meta["tipo_documento_crudo"],
                    "estado": "encolado",
                }
                resp = cliente.table("reportes_archivo").insert(fila).execute()
                reporte_id = resp.data[0]["id"]
                cliente.table("ingesta_cola").insert(
                    {
                        "reporte_archivo_id": reporte_id,
                        "prioridad": prioridad_emisor(slug),
                    }
                ).execute()
                nuevos += 1
            except Exception as e:  # un archivo fallido no debe tumbar la corrida completa
                errores.append((str(pdf.relative_to(args.carpeta)), str(e)))

    print(f"\nNuevos encolados: {nuevos}")
    print(f"Ya existían (omitidos, no se tocó su estado): {ya_existian}")
    if sin_patron:
        print(f"\nSin patrón reconocible ({len(sin_patron)}) — no se encolan, requieren mirada manual:")
        for s in sin_patron:
            print(f"  - {s}")
    if errores:
        print(f"\nErrores ({len(errores)}):")
        for ruta, err in errores:
            print(f"  - {ruta}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
