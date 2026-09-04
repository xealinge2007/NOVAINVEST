"""Corre las plantillas de extracción disponibles, y donde no haya
plantilla, el extractor genérico (triage + etiqueta, sin plantilla por
emisor -- §5.1.3, F4a paso 6), sobre lo que `ingesta_simev.py` dejó en
`reportes_archivo`. Todavía es SOLO el parser — no hay doble extracción con
el subagente `analista-fundamental` todavía, así que todo lo que logra
extraer entra a `fundamentales_reportados` con `metodo_validacion =
'provisional'` (§5.1.2: "el dato queda provisional hasta que el admin o un
segundo usuario lo confirme").

Un reporte donde ni la plantilla ni el extractor genérico encuentran
ninguna tabla ancla (formato distinto o informe narrativo sin cifras), o
donde el balance no cuadra (activos ≠ pasivos + patrimonio ±1%), se marca
`requiere_revision` en `reportes_archivo` con el motivo — nunca se descarta
en silencio ni se rellena con nada.

Uso: python jobs/extraer_fundamentales.py [--emisor SLUG] [--limite N]
"""

import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path


class TimeoutExtraccion(Exception):
    pass


RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.extraccion import extractor_generico, plantilla_ecopetrol, plantilla_ecopetrol_eeff_anual  # noqa: E402

TIMEOUT_SEGUNDOS = 120  # un solo PDF no debe poder bloquear el lote entero.

# Verificado real, dos rondas: un primer intento con ThreadPoolExecutor.result(timeout=...)
# evitaba el bloqueo del proceso principal, pero el hilo colgado NO se puede matar en
# Python (no hay señal portable para eso) -- quedaba corriendo de fondo para siempre,
# compitiendo por CPU/GIL con cada archivo siguiente. El síntoma real en la corrida:
# los timeouts se fueron alargando solos, 122s -> 132s -> 209s -> 246s -> 281s, cada
# hilo zombi nuevo hacía más lento a todos los que venían después. Un PROCESO sí se
# puede matar de verdad (terminate()), liberando la CPU al expirar el límite -- por
# eso corre en un proceso aparte, no en un hilo.


def _ejecutar_en_proceso(func, args, cola):
    try:
        cola.put(("ok", func(*args)))
    except Exception as e:
        cola.put(("error", f"{type(e).__name__}: {e}"))


def _con_limite_de_tiempo(func, *args):
    """Corre func(*args) en un proceso aparte con timeout real. Si se pasa, mata el
    proceso (terminate + join) para no dejar nada compitiendo por CPU de fondo, y
    lanza TimeoutExtraccion."""
    cola = mp.Queue()
    proceso = mp.Process(target=_ejecutar_en_proceso, args=(func, args, cola))
    proceso.start()
    proceso.join(timeout=TIMEOUT_SEGUNDOS)
    if proceso.is_alive():
        proceso.terminate()
        proceso.join()
        raise TimeoutExtraccion(f"timeout tras {TIMEOUT_SEGUNDOS}s")
    tipo, valor = cola.get()
    if tipo == "error":
        raise RuntimeError(valor)
    return valor

# Un emisor puede tener más de una plantilla, cada una atada a un
# `tipo_documento` (§5.1: precedencia -- estados financieros e informe
# periódico mandan, nunca comunicado de prensa) y opcionalmente acotada por
# fecha. "vigente_desde" es un filtro barato para no ni intentarlo en años
# claramente anteriores, NO una garantía de formato estable dentro del
# rango: Ecopetrol coexiste con dos formatos de informe periódico incluso
# dentro del mismo año (2025-T1/2026-T1 traen "Tabla 1: Resumen
# Financiero"; 2025-T2/T3/ANUAL NO la traen, son el formato narrativo por
# secciones, que a su vez NO trae cifras -- remite a SIMEV/la web). Un
# reporte que cae en el rango de fechas pero no trae la tabla ancla queda
# `requiere_revision`, nunca se fuerza.
PLANTILLAS_DISPONIBLES = {
    "ECOPETROL": [
        {
            "modulo": plantilla_ecopetrol,
            "tipos_documento": ["informe_periodico"],
            "vigente_desde": "2025-01-01",
            "version": "resumen_tabla1_2025_2026",
        },
        {
            "modulo": plantilla_ecopetrol_eeff_anual,
            "tipos_documento": ["estados_financieros"],
            "vigente_desde": "2000-01-01",
            "version": "eeff_consolidados_auditados",
        },
    ],
}

CAMPOS_NUMERICOS = [
    "ingresos", "utilidad_operacional", "utilidad_neta", "ebitda",
    "activos_totales", "pasivos_totales", "patrimonio", "flujo_caja_operativo",
    "deuda_financiera", "acciones_en_circulacion", "dividendos_decretados",
]


def _plantilla_para(slug_emisor: str, tipo_documento: str, anio: int):
    candidatas = PLANTILLAS_DISPONIBLES.get(slug_emisor, [])
    for c in candidatas:
        if tipo_documento in c["tipos_documento"] and anio >= int(c["vigente_desde"][:4]):
            return c
    return None


def _activos_fuera_de_rango(cliente, emisor_id: int, activos_nuevo: float) -> bool:
    """True si `activos_nuevo` difiere más de 3x (o menos de 1/3) del promedio
    de lo ya guardado para este emisor. Verificado real: CIBEST 2025-ANUAL
    "cuadraba" perfecto (activos=pasivos+patrimonio) con 42.187 miles de
    millones -- una tabla internamente consistente pero equivocada (probable
    subsidiaria o segmento, no el consolidado, cuyo activos real ronda
    375.000-390.000 en los trimestres ya verificados). El chequeo contable
    NO atrapa esto porque una tabla equivocada puede cuadrar perfecto sola;
    hace falta comparar contra el propio historial del emisor. Sin historial
    todavía, no hay con qué comparar -- no se objeta."""
    existentes = cliente.table("fundamentales_reportados").select("activos_totales").eq("emisor_id", emisor_id).execute().data
    valores = [e["activos_totales"] for e in existentes if e["activos_totales"] is not None]
    if not valores or activos_nuevo <= 0:
        return False
    promedio = sum(valores) / len(valores)
    if promedio <= 0:
        return False
    razon = activos_nuevo / promedio
    return not (1 / 3 <= razon <= 3)


def _es_separado(tipo_documento_crudo: str) -> bool:
    """§5.1 + instrucción explícita de Alex (03-sep-2026): el análisis usa
    SOLO resultados consolidados -- un 'EEFF-Separados'/'Estados-Financieros-
    Individuales' nunca entra, aunque tenga plantilla técnicamente aplicable."""
    t = tipo_documento_crudo.lower()
    return "separad" in t or "individual" in t


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None, help="slug de un solo emisor (ej. ECOPETROL)")
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()

    emisores_resp = cliente.table("emisores").select("id,slug,sector").execute()
    emisores = {e["slug"]: e["id"] for e in emisores_resp.data}
    id_a_slug = {v: k for k, v in emisores.items()}
    id_a_sector = {e["id"]: e["sector"] for e in emisores_resp.data}

    # El extractor genérico no necesita plantilla -- cubre TODOS los emisores,
    # no solo los de PLANTILLAS_DISPONIBLES (esa lista sigue existiendo por si
    # una plantilla específica supera al genérico para un emisor puntual).
    slugs_cubiertos = list(emisores.keys()) if args.emisor is None else [args.emisor]
    ids_cubiertos = [emisores[s] for s in slugs_cubiertos if s in emisores]

    query = (
        cliente.table("reportes_archivo")
        .select("*")
        .in_("emisor_id", ids_cubiertos)
        .in_("tipo_documento", ["informe_periodico", "estados_financieros"])
        .in_("estado", ["encolado", "requiere_revision"])
        .order("anio")
        .order("periodo")
    )
    if args.limite:
        query = query.limit(args.limite)
    reportes = query.execute().data

    print(f"{len(reportes)} reportes encolados para procesar ({slugs_cubiertos})")

    resumen = []

    def _registrar(resultado_str, inicio):
        resumen.append((slug, r["anio"], r["periodo"], resultado_str))
        print(f"{resultado_str} ({time.monotonic() - inicio:.0f}s)", flush=True)

    for i, r in enumerate(reportes, 1):
        slug = id_a_slug[r["emisor_id"]]
        inicio = time.monotonic()
        print(f"[{i}/{len(reportes)}] {slug} {r['anio']}-{r['periodo']} ({r['nombre_archivo']})...", end=" ", flush=True)

        if _es_separado(r["tipo_documento_crudo"]):
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": "separado/individual, no consolidado -- excluido por criterio explícito (solo consolidado)"}
            ).eq("id", r["id"]).execute()
            _registrar("EXCLUIDO_SEPARADO", inicio)
            continue

        plantilla = _plantilla_para(slug, r["tipo_documento"], r["anio"])
        if plantilla is not None:
            try:
                extraido = _con_limite_de_tiempo(plantilla["modulo"].extraer, Path(r["ruta_local"]))
            except TimeoutExtraccion:
                cliente.table("reportes_archivo").update(
                    {"estado": "error", "error_detalle": f"timeout ({TIMEOUT_SEGUNDOS}s) -- PDF anormalmente lento o pesado"}
                ).eq("id", r["id"]).execute()
                _registrar("TIMEOUT", inicio)
                continue
            except Exception as e:
                cliente.table("reportes_archivo").update(
                    {"estado": "error", "error_detalle": f"{type(e).__name__}: {e}"}
                ).eq("id", r["id"]).execute()
                _registrar(f"ERROR: {type(e).__name__}", inicio)
                continue

            campos_con_valor = {c: extraido[c]["valor"] for c in CAMPOS_NUMERICOS if c in extraido and extraido[c]["valor"] is not None}
            if not campos_con_valor:
                cliente.table("reportes_archivo").update(
                    {"estado": "requiere_revision", "error_detalle": "la plantilla no encontró ninguna tabla ancla en este PDF"}
                ).eq("id", r["id"]).execute()
                _registrar("SIN_TABLAS_RECONOCIDAS", inicio)
                continue

            pagina_ingresos = extraido.get("ingresos", {}).get("pagina")
            fila = {
                "emisor_id": r["emisor_id"],
                "anio": r["anio"],
                "periodo": r["periodo"],
                "consolidado": True,
                "origen": "reportado",
                **campos_con_valor,
                "metodo_validacion": "provisional",
                "reporte_archivo_id": r["id"],
                "pagina_fuente": pagina_ingresos,
            }
            cliente.table("fundamentales_reportados").upsert(fila, on_conflict="emisor_id,anio,periodo,consolidado").execute()
            cliente.table("reportes_archivo").update({"estado": "procesado"}).eq("id", r["id"]).execute()
            _registrar(f"OK-PLANTILLA ({len(campos_con_valor)}/{len(CAMPOS_NUMERICOS)} campos)", inicio)
            continue

        # Sin plantilla específica -- el extractor genérico (triage + etiqueta,
        # §5.1.3 paso 6) no necesita una por emisor.
        try:
            resultado = _con_limite_de_tiempo(
                extractor_generico.extraer,
                Path(r["ruta_local"]), id_a_sector.get(r["emisor_id"], "sin_clasificar"), r["anio"], r["periodo"],
            )
        except TimeoutExtraccion:
            cliente.table("reportes_archivo").update(
                {"estado": "error", "error_detalle": f"timeout ({TIMEOUT_SEGUNDOS}s) -- PDF anormalmente lento o pesado"}
            ).eq("id", r["id"]).execute()
            _registrar("TIMEOUT", inicio)
            continue
        except Exception as e:
            cliente.table("reportes_archivo").update(
                {"estado": "error", "error_detalle": f"{type(e).__name__}: {e}"}
            ).eq("id", r["id"]).execute()
            _registrar(f"ERROR-GENERICO: {type(e).__name__}", inicio)
            continue

        campos_generico = resultado["campos"]
        campos_con_valor = {c: campos_generico[c]["valor"] for c in CAMPOS_NUMERICOS if c in campos_generico and campos_generico[c]["valor"] is not None}

        if not campos_con_valor:
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": "el extractor genérico no encontró ninguna tabla ancla en este PDF"}
            ).eq("id", r["id"]).execute()
            _registrar("SIN_TABLAS_RECONOCIDAS", inicio)
            continue

        if resultado["cuadra_balance"] is False:
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": "el extractor genérico encontró activos/pasivos/patrimonio pero el balance no cuadra (±1%)"}
            ).eq("id", r["id"]).execute()
            _registrar("BALANCE_NO_CUADRA", inicio)
            continue

        # Un solo campo sin el balance confirmado no basta para publicar -- verificado
        # real: CIBEST 2023-ANUAL (informe de gestión de 300+ páginas, muchas tablas
        # anexas que reusan títulos parecidos) escribió únicamente flujo_caja_operativo
        # de una página que resultó ser la equivocada, sin nada que lo corrobore.
        # activos_totales presente = el balance al menos se ubicó (aunque no cuadre
        # verificablemente); sin eso, exigir 2+ campos como corroboración mínima.
        if "activos_totales" not in campos_con_valor and len(campos_con_valor) < 2:
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": f"solo 1 campo sin balance confirmado ({list(campos_con_valor)[0]}) -- insuficiente para publicar sin corroboración"}
            ).eq("id", r["id"]).execute()
            _registrar("CORROBORACION_INSUFICIENTE", inicio)
            continue

        if "activos_totales" in campos_con_valor and _activos_fuera_de_rango(cliente, r["emisor_id"], campos_con_valor["activos_totales"]):
            cliente.table("reportes_archivo").update(
                {"estado": "requiere_revision", "error_detalle": f"activos_totales={campos_con_valor['activos_totales']} se sale de rango (>3x o <1/3) del historial del emisor -- probable tabla equivocada aunque el balance cuadre"}
            ).eq("id", r["id"]).execute()
            _registrar("FUERA_DE_RANGO", inicio)
            continue

        pagina_ingresos = campos_generico.get("ingresos", {}).get("pagina") or campos_generico.get("activos_totales", {}).get("pagina")
        fila = {
            "emisor_id": r["emisor_id"],
            "anio": r["anio"],
            "periodo": r["periodo"],
            "consolidado": True,
            "origen": "reportado",
            "unidad": resultado["unidad"] or "millones",
            **campos_con_valor,
            "metodo_validacion": "provisional",
            "reporte_archivo_id": r["id"],
            "pagina_fuente": pagina_ingresos,
        }
        cliente.table("fundamentales_reportados").upsert(fila, on_conflict="emisor_id,anio,periodo,consolidado").execute()
        cliente.table("reportes_archivo").update({"estado": "procesado"}).eq("id", r["id"]).execute()
        cuadra = "cuadra" if resultado["cuadra_balance"] else "sin verificar"
        _registrar(f"OK-GENERICO ({len(campos_con_valor)}/{len(CAMPOS_NUMERICOS)} campos, balance {cuadra})", inicio)

    print(f"\n{'emisor':<28}{'periodo':<10}resultado")
    for slug, anio, periodo, estado in resumen:
        print(f"{slug:<28}{anio}-{periodo:<6}{estado}")


if __name__ == "__main__":
    main()
