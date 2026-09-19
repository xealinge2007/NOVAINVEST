# -*- coding: utf-8 -*-
"""Pilar 1 — Seguridad (Whitman), W2 del Motor de Valor BVC (plan aprobado
16-sep-2026, `db/DOCTRINA_VALOR.md`).

**"Safe" es previo a "cheap".** Este job no valora nada — decide si un
emisor es siquiera analizable e invertible, antes de que W3 calcule cuánto
vale. Escribe el veredicto en `score_valor.elegible`/`pilar1_seguridad_ok`
(no las cifras: esas ya viven en `fundamentales_analisis`, este job las lee,
no las recalcula).

**Honestidad sobre lo que SÍ se puede medir hoy.** El molde de 4 métricas
por arquetipo que describe el plan (§6) asume datos que este pipeline no
tiene todavía:
  - Molde REAL: cobertura de intereses, activos cuasi-caja/pasivos, deuda
    CP/caja y deuda USD sin cobertura necesitan gasto financiero y el
    desglose de caja/deuda por plazo y moneda -- `fundamentales_reportados`
    no los captura (no está en el XBRL taxonomizado que se lee hoy).
  - Molde HOLDING: "deuda del nivel holding / valor de mercado del
    portafolio" necesita `participaciones_holding` poblada (W3a, todavía
    vacía) para saber cuánto vale el portafolio a mercado.
  - Molde BANCO: CET1, cartera vencida, costo del riesgo y concentración
    del fondeo son datos regulatorios (informes de la Superfinanciera
    específicos de bancos) que este pipeline no ingiere.
  - Molde VEHÍCULO INMOBILIARIO: loan-to-value real (contra el valor de
    los inmuebles, no el activo contable) y ocupación/plazo de contratos
    tampoco están capturados.

Por eso este job **solo evalúa lo que puede medir sin inventar**: apalancamiento
(deuda/EBITDA, deuda/patrimonio -- ya calculados en `fundamentales_analisis`
por `analizador_fundamental.py`) para los moldes REAL, HOLDING y VEHÍCULO
INMOBILIARIO, y **declara el molde BANCO sin evaluar** (motivo explícito, no
un `False` disfrazado de veredicto). El resto de las métricas del plan
quedan listadas como pendientes en `motivo_metricas_faltantes` de cada fila,
para que quede trazable qué falta y por qué, no que se olvidó.

**Puerta de liquidez** (plan §6, "la iliquidez veta también"): reusa
`app.services.liquidez.volumen_suficiente`, el mismo piso de 500M COP/día
de 20 sesiones que ya usa F3 para señales. Se exige en AL MENOS UN
instrumento del emisor (ordinaria o preferencial). Es Puerta 0: si no pasa,
el emisor sale con `elegible=False` sin evaluar seguridad.

Uso: python jobs/solidez_financiera.py [--emisor SLUG] [--dry-run]
"""

import argparse
import io
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

import pandas as pd  # noqa: E402

from app.services.liquidez import volumen_suficiente  # noqa: E402

# DOCTRINA_VALOR.md §2 -- clasificación ya documentada, se siembra aquí
# porque F0/W1 dejó `emisores.arquetipo` vacío a propósito ("sembrarla es
# tarea de W2/W3a, no del DDL").
ARQUETIPO_POR_SLUG = {
    "GRUPO_ARGOS": "holding", "GRUPO_SURA": "holding", "GRUPO_AVAL": "holding",
    "CORFICOLOMBIANA": "holding", "GEB": "holding",
    "GRUPO_CIBEST_BANCOLOMBIA": "banco", "BANCO_DE_BOGOTA": "banco", "DAVIVIENDA_GROUP": "banco",
    "ECOPETROL": "real", "CEMENTOS_ARGOS": "real", "MINEROS": "real", "PROMIGAS": "real",
    "ISA": "real", "TERPEL": "real", "CONSTRUCTORA_CONCONCRETO": "real", "GRUPO_NUTRESA": "real",
    "ETB": "real", "CELSIA": "real", "FABRICATO": "real", "EXITO": "real", "ENKA": "real",
    "EL_CONDOR": "real",
    "PEI": "vehiculo_inmobiliario",
    "BVC": "infraestructura_mercado",
}

# Umbrales de apalancamiento -- criterio documentado, no medido (mismo
# espíritu que el piso de liquidez de `liquidez.py`): deuda/EBITDA > 4x o
# deuda/patrimonio > 2x es la zona donde Whitman diría que el balance ya no
# es "excepcionalmente fuerte", el filtro previo a cualquier "cheap".
# Holgura: un EBITDA_TTM negativo o ausente no reprueba por deuda/EBITDA --
# ese ratio no tiene sentido con denominador negativo/None, se declara no
# evaluable en vez de tratarlo como infinito.
MAX_DEUDA_EBITDA = 4.0
MAX_DEUDA_PATRIMONIO = 2.0

MOTIVO_BANCO_NO_EVALUADO = (
    "molde banco: requiere CET1/solvencia regulatoria, cartera vencida, costo del "
    "riesgo y concentración del fondeo -- ninguno capturado por este pipeline "
    "todavía (son informes regulatorios específicos de bancos, no XBRL/PDF "
    "estándar). No se aproxima con apalancamiento genérico porque para un banco "
    "la deuda ES el fondeo (depósitos), no apalancamiento en el sentido de "
    "Whitman -- usar deuda/patrimonio aquí sería inventar una señal."
)

METRICAS_FALTANTES_POR_MOLDE = {
    "real": "cobertura de intereses, activos cuasi-caja/pasivos totales, deuda CP/caja, "
            "deuda USD sin cobertura, tangibles vs. goodwill -- sin gasto financiero ni "
            "desglose de caja/deuda por plazo y moneda en fundamentales_reportados",
    "holding": "deuda del nivel holding / valor de mercado del portafolio (necesita "
               "participaciones_holding poblada, W3a), dividendos recibidos vs. gastos "
               "holding, liquidez de las participaciones -- se usa deuda/patrimonio "
               "consolidado como proxy provisional, más débil que la métrica del plan",
    "vehiculo_inmobiliario": "loan-to-value contra el valor de los inmuebles (no el "
               "activo contable), cobertura del servicio de deuda, ocupación y plazo "
               "medio de contratos -- se usa deuda/patrimonio y deuda/activos como "
               "proxy provisional, no es LTV real",
    "infraestructura_mercado": "molde atípico (BVC, la Bolsa misma), sin plan de "
               "métricas dedicado -- se usa el mismo proxy de apalancamiento que 'real'",
}


def _seguridad_por_apalancamiento(deuda_ebitda, deuda_patrimonio, ebitda_ttm):
    """(ok, motivo). None en ok = no evaluable (falta el dato para juzgar)."""
    razones_reprueba = []
    if deuda_patrimonio is not None:
        if deuda_patrimonio > MAX_DEUDA_PATRIMONIO:
            razones_reprueba.append(f"deuda/patrimonio {deuda_patrimonio:.2f}x > {MAX_DEUDA_PATRIMONIO}x")
    else:
        return None, "sin deuda/patrimonio calculado"

    if ebitda_ttm is not None and ebitda_ttm > 0 and deuda_ebitda is not None:
        if deuda_ebitda > MAX_DEUDA_EBITDA:
            razones_reprueba.append(f"deuda/EBITDA {deuda_ebitda:.2f}x > {MAX_DEUDA_EBITDA}x")
    else:
        # EBITDA ausente o negativo: no se puede juzgar por este ratio, pero
        # el de patrimonio ya alcanza para decidir -- no se bloquea el
        # veredicto completo por un solo ratio no evaluable.
        pass

    if razones_reprueba:
        return False, "; ".join(razones_reprueba)
    return True, f"deuda/patrimonio {deuda_patrimonio:.2f}x, deuda/EBITDA {deuda_ebitda if deuda_ebitda is not None else 'n/d'}"


def _liquidez_ok(cliente, emisor_id):
    """(ok, detalle) sobre TODOS los instrumentos del emisor -- pasa si al
    menos uno supera el piso de `liquidez.py`."""
    instrumentos = cliente.table("instrumentos").select("id,ticker,activo_id").eq("emisor_id", emisor_id).execute().data
    if not instrumentos:
        return False, "sin instrumento registrado"
    detalles = []
    for inst in instrumentos:
        precios = (
            cliente.table("precios").select("cierre,volumen")
            .eq("activo_id", inst["activo_id"]).order("fecha", desc=True).limit(20).execute().data
        )
        df = pd.DataFrame(precios)
        ok = volumen_suficiente(df)
        detalles.append(f"{inst['ticker']}: {'OK' if ok else 'insuficiente'}")
        if ok:
            return True, "; ".join(detalles)
    return False, "; ".join(detalles)


def _ultimo_periodo_con_cifras(cliente, emisor_id):
    """(anio, periodo) más reciente con activos_totales no nulo -- es la
    fecha "as of" que se le asigna al veredicto de solidez en `score_valor`,
    que exige (emisor_id, anio, periodo). `fundamentales_analisis` es un
    snapshot TTM sin período propio; se toma prestado el del dato crudo."""
    filas = (
        cliente.table("fundamentales_reportados")
        .select("anio,periodo").eq("emisor_id", emisor_id)
        .not_.is_("activos_totales", "null")
        .execute().data
    )
    if not filas:
        return None, None
    orden_periodo = {"T1": 1, "T2": 2, "T3": 3, "T4": 4, "ANUAL": 5}
    mejor = max(filas, key=lambda f: (f["anio"], orden_periodo.get(f["periodo"], 0)))
    return mejor["anio"], mejor["periodo"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()

    emisores = cliente.table("emisores").select("id,slug,arquetipo").execute().data
    if args.emisor:
        emisores = [e for e in emisores if e["slug"] == args.emisor]

    analisis = {a["slug"]: a for a in cliente.table("fundamentales_analisis").select("*").execute().data}

    resumen = {"sin_arquetipo": 0, "sin_liquidez": 0, "banco_no_evaluado": 0, "ok": 0, "no_ok": 0, "no_evaluable": 0}

    for em in emisores:
        slug = em["slug"]
        arquetipo = em.get("arquetipo") or ARQUETIPO_POR_SLUG.get(slug)
        if arquetipo is None:
            print(f"  [{slug}] AVISO: sin arquetipo conocido (no está en DOCTRINA_VALOR.md §2) -- se salta")
            resumen["sin_arquetipo"] += 1
            continue

        if em.get("arquetipo") is None and not args.dry_run:
            cliente.table("emisores").update({"arquetipo": arquetipo}).eq("id", em["id"]).execute()

        liquidez_ok, liquidez_detalle = _liquidez_ok(cliente, em["id"])

        if not liquidez_ok:
            print(f"  {slug:26s} molde={arquetipo:22s} ELEGIBLE=False (Puerta 0, liquidez: {liquidez_detalle})")
            resumen["sin_liquidez"] += 1
            veredicto = {"elegible": False, "motivo_no_elegible": f"liquidez insuficiente: {liquidez_detalle}",
                         "pilar1_seguridad_ok": None, "pilar1_motivo": "no evaluado: no pasó Puerta 0"}
        elif arquetipo == "banco":
            print(f"  {slug:26s} molde=banco                 pilar1=no_evaluable ({MOTIVO_BANCO_NO_EVALUADO[:60]}...)")
            resumen["banco_no_evaluado"] += 1
            veredicto = {"elegible": True, "motivo_no_elegible": None,
                         "pilar1_seguridad_ok": None, "pilar1_motivo": MOTIVO_BANCO_NO_EVALUADO}
        else:
            fa = analisis.get(slug, {})
            ok, motivo = _seguridad_por_apalancamiento(fa.get("deuda_ebitda"), fa.get("deuda_patrimonio"), fa.get("ebitda_ttm"))
            faltantes = METRICAS_FALTANTES_POR_MOLDE.get(arquetipo, "")
            motivo_completo = f"{motivo} -- pendiente del plan completo: {faltantes}" if motivo else faltantes
            if ok is None:
                resumen["no_evaluable"] += 1
            elif ok:
                resumen["ok"] += 1
            else:
                resumen["no_ok"] += 1
            print(f"  {slug:26s} molde={arquetipo:22s} pilar1={'OK' if ok else ('no_ok' if ok is False else 'no_evaluable')} ({motivo})")
            veredicto = {"elegible": True, "motivo_no_elegible": None,
                         "pilar1_seguridad_ok": ok, "pilar1_motivo": motivo_completo}

        if args.dry_run:
            continue

        anio, periodo = _ultimo_periodo_con_cifras(cliente, em["id"])
        if anio is None:
            print(f"    {slug}: sin período con cifras -- no se escribe en score_valor")
            continue
        cliente.table("score_valor").upsert(
            {"emisor_id": em["id"], "anio": anio, "periodo": periodo, **veredicto},
            on_conflict="emisor_id,anio,periodo",
        ).execute()

    print("\n" + "=" * 76)
    for k, v in resumen.items():
        print(f"  {v:4d}  {k}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
