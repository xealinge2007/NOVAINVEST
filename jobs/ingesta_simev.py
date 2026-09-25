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
import csv
import hashlib
import os
import re
import sys
from pathlib import Path

import pdfplumber

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


NOMBRE_MANIFIESTO = "MANIFIESTO.csv"

FUENTES_VALIDAS = {"simev", "emisor_ir", "superfinanciera", "otro"}


def cargar_manifiesto(carpeta_raiz: Path, ruta_explicita: Path | None = None) -> dict[tuple[str, str], dict]:
    """{(emisor, nombre_archivo): {fuente_origen, url_descarga}} leido de
    `MANIFIESTO.csv` en la raiz del corpus. Devuelve {} si no existe.

    Por que existe (5.1.4): la regla dice que un numero sin procedencia
    registrada no se publica, pero hasta hoy `fuente_origen` se escribia
    hardcodeado como "simev" para los 412 archivos y `url_descarga` quedaba
    vacio en TODOS -- o sea, la procedencia era una suposicion del script, no
    un registro. Y la suposicion es falsa por diseno: el propio documento de
    arquitectura acepta que varias cifras salen de la pagina de relacion con
    inversionistas del emisor, no del SIMEV, y que ante una discrepancia gana
    la version radicada ante el regulador. Sin saber de donde vino cada
    archivo, esa regla de desempate no se puede aplicar.

    El manifiesto lo llena quien descarga. Formato:
        emisor,archivo,fuente_origen,url_descarga,fecha_descarga
    `fuente_origen` tiene que ser uno de FUENTES_VALIDAS. Una fila con fuente
    invalida se ignora y se reporta -- mejor sin procedencia declarada que con
    una inventada."""
    ruta = ruta_explicita or (carpeta_raiz / NOMBRE_MANIFIESTO)
    if not ruta.is_file():
        return {}
    manifiesto: dict[tuple[str, str], dict] = {}
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            emisor = (fila.get("emisor") or "").strip()
            archivo = (fila.get("archivo") or "").strip()
            fuente = (fila.get("fuente_origen") or "").strip().lower()
            if not emisor or not archivo:
                continue
            if fuente not in FUENTES_VALIDAS:
                print(f"  [manifiesto] fuente_origen invalida en {emisor}/{archivo} -- fila ignorada")
                continue
            manifiesto[(emisor, archivo)] = {
                "fuente_origen": fuente,
                "url_descarga": (fila.get("url_descarga") or "").strip() or None,
            }
    return manifiesto


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


EXTENSIONES_VALIDAS = (".pdf", ".xlsx")


def parsear_nombre_archivo(nombre_archivo: str) -> dict | None:
    """Devuelve {anio, periodo, tipo_documento, tipo_documento_crudo} o None
    si el nombre no sigue el patrón mínimo `AAAA-PERIODO_Tipo.pdf` (o
    `.xlsx` -- agregado 24-sep-2026 para el caso real de ETB 2019-T3, que
    solo existe como EEFF consolidado en Excel, nunca en PDF; el resto del
    corpus sigue siendo casi enteramente PDF, esto NO cambia esa mayoría)."""
    nombre_bajo = nombre_archivo.lower()
    ext = next((e for e in EXTENSIONES_VALIDAS if nombre_bajo.endswith(e)), None)
    if ext is None:
        return None
    sin_ext = nombre_archivo[: -len(ext)]
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


def detectar_pdf_protegido(ruta: Path) -> str | None:
    """Firma de un PDF cifrado con Microsoft Information Protection / Azure
    Rights Management (F4a, paso 1 del orden de trabajo). pdfplumber lo abre
    sin lanzar excepción -- no es un PDF corrupto -- pero entrega una sola
    página-aviso ("no tiene autorización para ver su contenido") en vez del
    documento real. Verificado el 03-sep-2026 contra una muestra real
    (`ECOPETROL/2026-T1_..._PROTEGIDO-IRM.pdf`, la única de 409 encontrada):
    el metadato `MSIP_Label_*` es la señal más barata y estable -- sobrevive
    aunque `extract_text()` llegue con acentos rotos por el encoding del
    stub. Devuelve el motivo si detecta la firma, None si el PDF es legible.
    No aplica a XLSX (nunca se ha visto la protección en ese formato en el
    corpus) -- se salta directo, no tiene sentido abrirlo con pdfplumber."""
    if ruta.suffix.lower() != ".pdf":
        return None
    with pdfplumber.open(ruta) as pdf:
        if any(str(k).startswith("MSIP_Label") for k in (pdf.metadata or {})):
            return "PDF protegido (Microsoft Information Protection / Azure Rights Management) -- pedir a Alex que lo re-descargue sin cifrado"
        texto_p1 = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
        if "Information Protection" in texto_p1 or "Rights Management" in texto_p1:
            return "PDF protegido (Microsoft Information Protection / Azure Rights Management) -- pedir a Alex que lo re-descargue sin cifrado"
    return None


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



def _validar(carpetas_emisor: list[Path], raiz: Path, manifiesto: dict) -> int:
    """Compuerta que corre quien descarga, ANTES de entregar los archivos. No
    toca Supabase. Devuelve el codigo de salida (0 si todo cumple).

    Existe porque el contrato de nombre (AAAA-PERIODO_Tipo.pdf) hasta hoy se
    verificaba recien dentro de la ingesta, cuando ya era tarde: un renombrado
    masivo de ~180 archivos dejo 184 filas apuntando a rutas inexistentes y
    costo un job de reconciliacion por hash entero (commit e3e8e24). Revisar el
    contrato antes de entregar es mucho mas barato que reconciliarlo despues."""
    malos: list[str] = []
    sin_procedencia: list[str] = []
    total = 0
    for carpeta in carpetas_emisor:
        archivos = sorted(p for ext in EXTENSIONES_VALIDAS for p in carpeta.glob(f"*{ext}"))
        for archivo in archivos:
            total += 1
            if parsear_nombre_archivo(archivo.name) is None:
                malos.append(str(archivo.relative_to(raiz)))
            if (carpeta.name, archivo.name) not in manifiesto:
                sin_procedencia.append(carpeta.name + "/" + archivo.name)

    print(f"Validacion del corpus: {total} archivos (PDF/XLSX) en {len(carpetas_emisor)} carpetas de emisor")
    print(f"  contrato de nombre AAAA-PERIODO_Tipo.<ext>: {total - len(malos)}/{total} cumplen")
    if malos:
        print(f"  INCUMPLEN el contrato ({len(malos)}) -- renombrar antes de entregar:")
        for m in malos:
            print("    - " + m)
    print(f"  procedencia declarada en el manifiesto: {total - len(sin_procedencia)}/{total}")
    if sin_procedencia:
        print(f"    faltan {len(sin_procedencia)} (se asumira fuente_origen='simev', url_descarga vacia)")
        for m in sin_procedencia[:10]:
            print("    - " + m)
        if len(sin_procedencia) > 10:
            print(f"    ... y {len(sin_procedencia) - 10} mas")
    if malos:
        print("RESULTADO: FALLA -- hay nombres fuera del contrato.")
        return 1
    print("RESULTADO: OK -- todos los nombres cumplen el contrato.")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carpeta", type=Path, default=CARPETA_DEFAULT)
    parser.add_argument("--dry-run", action="store_true", help="solo reporta, no escribe en Supabase")
    parser.add_argument("--manifiesto", type=Path, default=None, help="CSV de procedencia (por defecto MANIFIESTO.csv en la raiz del corpus)")
    parser.add_argument(
        "--validar", action="store_true",
        help="compuerta previa a la ingesta: revisa el contrato de nombre y la cobertura del "
             "manifiesto, no toca Supabase y sale con codigo 1 si algo incumple. Es lo que corre "
             "quien descarga antes de entregar los archivos.",
    )
    args = parser.parse_args()

    if not args.carpeta.is_dir():
        print(f"No existe la carpeta {args.carpeta}")
        sys.exit(1)

    carpetas_emisor = sorted(p for p in args.carpeta.iterdir() if p.is_dir())
    manifiesto = cargar_manifiesto(args.carpeta, args.manifiesto)

    if args.validar:
        sys.exit(_validar(carpetas_emisor, args.carpeta, manifiesto))

    if manifiesto:
        print(f"Manifiesto de procedencia: {len(manifiesto)} entradas")
    else:
        print("Sin manifiesto de procedencia -- se asume fuente_origen='simev' y url_descarga vacia")
    print(f"Ingesta SIMEV_BVC — {len(carpetas_emisor)} carpetas de emisor en {args.carpeta}")

    cliente = None
    if not args.dry_run:
        from app.database import cliente_servicio

        cliente = cliente_servicio()

    cache_emisores: dict[str, int] = {}
    nuevos, ya_existian, cambiados, renombrados, protegidos, sin_patron, errores = 0, 0, 0, 0, 0, [], []
    lista_cambiados: list[tuple[str, str, str]] = []  # (slug, nombre_archivo, estado_previo)
    lista_renombrados: list[tuple[str, str, str]] = []  # (slug, nombre_viejo, nombre_nuevo)

    for carpeta_emisor in carpetas_emisor:
        slug = carpeta_emisor.name
        pdfs = sorted(p for ext in EXTENSIONES_VALIDAS for p in carpeta_emisor.glob(f"*{ext}"))
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
                .select("id,estado,hash_sha256")
                .eq("emisor_id", emisor_id)
                .eq("nombre_archivo", pdf.name)
                .execute()
            )
            hash_archivo = _hash_archivo(pdf)

            if not existente.data:
                # ¿Es el mismo archivo, solo renombrado? Buscar por hash dentro del
                # mismo emisor antes de asumir que es nuevo. Verificado real: un
                # renombrado masivo de ~410 archivos (agregando el sufijo
                # "-Estados-Financieros-..." que el clasificador necesita para
                # reconocerlos) dejó 184 filas huérfanas apuntando a rutas que ya
                # no existían -- sin este chequeo, esta misma corrida las habría
                # tratado como 184 archivos "nuevos", duplicando cada fila en vez
                # de actualizar la que ya tenía su historial de validación.
                posible_renombrado = (
                    cliente.table("reportes_archivo")
                    .select("id,estado,nombre_archivo,tipo_documento")
                    .eq("emisor_id", emisor_id)
                    .eq("hash_sha256", hash_archivo)
                    .execute()
                )
                if posible_renombrado.data:
                    fila_vieja = posible_renombrado.data[0]
                    try:
                        actualizacion = {
                            "nombre_archivo": pdf.name,
                            "ruta_local": str(pdf),
                            "tipo_documento": meta["tipo_documento"],
                            "tipo_documento_crudo": meta["tipo_documento_crudo"],
                        }
                        # El renombrado casi siempre existe justo para corregir la
                        # clasificación (ej. informe_periodico -> estados_financieros,
                        # al agregar el sufijo "-Estados-Financieros-..."). Si cambia,
                        # hay que reprocesar bajo la clasificación correcta -- renombrar
                        # sola la fila no alcanza.
                        reclasificado = fila_vieja["tipo_documento"] != meta["tipo_documento"]
                        if reclasificado or fila_vieja["estado"] == "error":
                            actualizacion["estado"] = "encolado"
                            actualizacion["error_detalle"] = None
                        cliente.table("reportes_archivo").update(actualizacion).eq("id", fila_vieja["id"]).execute()
                        if actualizacion.get("estado") == "encolado":
                            cliente.table("ingesta_cola").upsert(
                                {
                                    "reporte_archivo_id": fila_vieja["id"],
                                    "prioridad": prioridad_emisor(slug),
                                    "estado": "pendiente",
                                    "intentos": 0,
                                    "ultimo_error": None,
                                    "procesado_en": None,
                                },
                                on_conflict="reporte_archivo_id",
                            ).execute()
                        renombrados += 1
                        lista_renombrados.append((slug, fila_vieja["nombre_archivo"], pdf.name))
                    except Exception as e:
                        errores.append((str(pdf.relative_to(args.carpeta)), str(e)))
                    continue

            if existente.data:
                fila_existente = existente.data[0]
                if fila_existente["hash_sha256"] == hash_archivo:
                    ya_existian += 1
                    continue
                # Mismo emisor + mismo nombre de archivo, pero contenido distinto -- Alex
                # reemplazó el PDF sin avisar (ya pasó una vez, ver ESTADO_PROYECTO.md).
                # Sin este chequeo el archivo se saltaría en silencio como "ya existía" y
                # una validación vieja se quedaría contaminando la serie para siempre.
                try:
                    motivo_protegido = detectar_pdf_protegido(pdf)
                    cliente.table("reportes_archivo").update(
                        {
                            "hash_sha256": hash_archivo,
                            "ruta_local": str(pdf),
                            "estado": "irrecuperable" if motivo_protegido else "encolado",
                            "error_detalle": motivo_protegido,
                            "procesado_en": None,
                        }
                    ).eq("id", fila_existente["id"]).execute()
                    if not motivo_protegido:
                        cliente.table("ingesta_cola").upsert(
                            {
                                "reporte_archivo_id": fila_existente["id"],
                                "prioridad": prioridad_emisor(slug),
                                "estado": "pendiente",
                                "intentos": 0,
                                "ultimo_error": None,
                                "procesado_en": None,
                            },
                            on_conflict="reporte_archivo_id",
                        ).execute()
                    cambiados += 1
                    lista_cambiados.append((slug, pdf.name, fila_existente["estado"]))
                except Exception as e:
                    errores.append((str(pdf.relative_to(args.carpeta)), str(e)))
                continue

            try:
                motivo_protegido = detectar_pdf_protegido(pdf)
                fila = {
                    "emisor_id": emisor_id,
                    "nombre_archivo": pdf.name,
                    "ruta_local": str(pdf),
                    "hash_sha256": hash_archivo,
                    # 5.1.4: la procedencia sale del manifiesto si esta declarada.
                    # Sin manifiesto se cae al supuesto historico ("simev"), de donde
                    # viene la mayoria del corpus, y `--validar` reporta cuantos
                    # archivos siguen sin procedencia declarada.
                    **manifiesto.get((slug, pdf.name), {"fuente_origen": "simev"}),  # §5.1.4: este script solo lee C:\Proyectos\BVC\SIMEV_BVC
                    "anio": meta["anio"],
                    "periodo": meta["periodo"],
                    "tipo_documento": meta["tipo_documento"],
                    "tipo_documento_crudo": meta["tipo_documento_crudo"],
                    "estado": "irrecuperable" if motivo_protegido else "encolado",
                }
                if motivo_protegido:
                    fila["error_detalle"] = motivo_protegido
                resp = cliente.table("reportes_archivo").insert(fila).execute()
                reporte_id = resp.data[0]["id"]
                if motivo_protegido:
                    protegidos += 1
                else:
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
    if renombrados:
        print(f"\nDetectados como renombrados por hash (fila reconciliada, no duplicada): {renombrados}")
        for slug, nombre_viejo, nombre_nuevo in lista_renombrados:
            print(f"  - {slug}: {nombre_viejo} -> {nombre_nuevo}")
    if cambiados:
        print(f"\nContenido reemplazado bajo el mismo nombre (re-encolados para reprocesar): {cambiados}")
        for slug, nombre, estado_previo in lista_cambiados:
            aviso = "  <- OJO: tenía datos ya validados" if estado_previo == "procesado" else ""
            print(f"  - {slug}/{nombre} (estaba en '{estado_previo}'){aviso}")
    if protegidos:
        print(f"Protegidos (IRM/Rights Management, marcados 'irrecuperable', no encolados): {protegidos}")
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
