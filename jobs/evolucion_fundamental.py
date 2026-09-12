"""Evolución fundamental vs. precio (F4n) -- inspirado en la IDEA
metodológica de cruzar métricas fundamentales contra el precio en el tiempo
(no en código ni fórmulas de ningún tercero): correlación y "efectividad"
direccional, por emisor.

Fases 1, 2 y 3 del plan F4n. Requiere Fase 0 ya aplicada: `precios` con 10
años de historia (`refresco_diario.py --anios 10`) y `cierre_ajustado`.

**Fase 3 (F4o/F4p):** además de la correlación, este job calcula bandas de
valoración por percentil histórico (P/E, P/VL, EV/EBITDA, Deuda/EBITDA) --
dónde está el múltiplo de HOY frente a los últimos ~20 trimestres del propio
emisor. A diferencia de las Fases 1-2, esto SÍ corre para bancos y holdings
financieros: P/E y P/VL son válidos para ellos (usan utilidad_neta y
patrimonio, no ingresos/EBITDA, que sí se excluyen para ese sector desde la
extracción).

**Por qué con rezago, y no solo "contemporáneo":**
Correlacionar la cifra del trimestre con el precio EN LA FECHA DE CIERRE de
ese trimestre mide qué pasó junto al precio, pero el mercado no conocía esa
cifra ese día -- se radica 45-60 días después. Sin el rezago, la
correlación queda inflada por sesgo de anticipación (look-ahead) y no sirve
para nada accionable. Este job calcula LAS DOS series por separado:
contemporánea (describe) y con rezago de 45 días (lo único potencialmente
accionable), y nunca las mezcla.

**Por qué TTM en cada punto y no el trimestre suelto:**
Comparar el trimestre suelto contra el precio mete estacionalidad (un
trimestre bueno en un negocio estacional no es lo mismo que mejora real).
`serie_ttm_historica()` da un trailing-twelve-months en cada punto, la
misma base que ya usa el analizador para TTM "de hoy".

**Qué NO promete este job:** con ~18-28 trimestres de historia por emisor,
esto sirve para describir y para descartar correlaciones que no existen, no
para predecir con confianza estadística real -- se reporta la tasa base
(cuántos trimestres subió el precio de por sí) al lado de cada "efectividad"
para que no se lea como más de lo que es.

Uso: python jobs/evolucion_fundamental.py
"""

import io
import math
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))
sys.path.insert(0, str(RAIZ / "jobs"))

from analizador_fundamental import (  # noqa: E402
    ACCIONES_CURADAS_MANUALMENTE,
    SECTORES_FINANCIEROS,
    TRIMESTRES,
    _cierre,
    _orden,
    acciones_del_emisor,
    descartar_escala_atipica,
    desacumular,
    detectar_acumulado,
    serie_ttm_historica,
)

# Fecha de cierre aproximada de cada período -- estándar calendario, no la
# fecha real de radicación (esa no se guarda; ver LAG_RADICACION_DIAS).
FIN_DE_PERIODO = {"T1": (3, 31), "T2": (6, 30), "T3": (9, 30), "ANUAL": (12, 31)}

# Plazo típico de radicación de resultados trimestrales ante la
# Superfinanciera en Colombia -- aproximado, no exacto por emisor. Es la
# única defensa contra el sesgo de anticipación que este job tiene: sin
# esto, la serie "contemporánea" sería la única posible y se leería como
# predictiva sin serlo.
LAG_RADICACION_DIAS = 45
VENTANA_BUSQUEDA_PRECIO_DIAS = 12
UMBRAL_SALTO_SOSPECHOSO = 0.30  # mismo criterio que refresco_diario.py


def _consultar_todo(consulta, tamano_pagina: int = 1000) -> list[dict]:
    """Pagina una consulta de Supabase con `.range()`. Verificado real:
    PostgREST tiene un tope de 1.000 filas por respuesta que IGNORA
    `.limit()` -- pedir `.limit(5000)` seguía devolviendo 1.000 (confirmado
    contra la tabla `precios`, 102.566 filas totales). Sin paginar, la
    consulta de 10 años de precios (~2.500 filas por activo) se truncaba en
    silencio a las primeras 1.000 -- justo los años más viejos, dejando
    2025-2026 sin precio."""
    filas, inicio = [], 0
    while True:
        pagina = consulta.range(inicio, inicio + tamano_pagina - 1).execute().data
        filas.extend(pagina)
        if len(pagina) < tamano_pagina:
            return filas
        inicio += tamano_pagina


def _fecha_periodo(anio: int, periodo: str) -> date:
    mes, dia = FIN_DE_PERIODO[periodo]
    return date(anio, mes, dia)


def _precio_en_o_despues(precios_ordenados: list[dict], desde: date, ventana_dias: int) -> float | None:
    """Primer cierre ajustado disponible en [desde, desde+ventana]. None si
    no hay ninguno -- ej. la fecha cae después del último dato descargado."""
    hasta = desde + timedelta(days=ventana_dias)
    for p in precios_ordenados:
        if desde <= p["fecha"] <= hasta:
            c = _cierre(p)
            if c:
                return c
    return None


def _pearson_r2(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 5:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    r = cov / math.sqrt(vx * vy)
    return round(r * r, 4)


def _efectividad(variaciones_metrica: list[float], variaciones_precio: list[float]) -> dict:
    """Aciertos = mismo signo (métrica y precio se mueven en la misma
    dirección). Se reporta junto a la tasa base (% de períodos donde el
    precio subió) porque un 68% de aciertos no dice nada si el precio subió
    el 70% de las veces de por sí -- acertar por defecto no es una señal."""
    n = len(variaciones_metrica)
    if n < 5:
        return {"n": n, "aciertos": None, "efectividad_pct": None, "tasa_base_alza_pct": None, "p_valor_vs_azar": None}
    aciertos = sum(1 for m, p in zip(variaciones_metrica, variaciones_precio) if (m > 0) == (p > 0))
    tasa_base = sum(1 for p in variaciones_precio if p > 0) / n
    efectividad = aciertos / n
    # Aproximación normal al binomial contra 50% -- suficiente para avisar
    # "esto es o no distinguible del azar", no para un paper.
    se = math.sqrt(0.25 / n)
    z = (efectividad - 0.5) / se if se else 0
    p_valor = round(2 * (1 - _cdf_normal_estandar(abs(z))), 4)
    return {
        "n": n, "aciertos": aciertos,
        "efectividad_pct": round(efectividad * 100, 1),
        "tasa_base_alza_pct": round(tasa_base * 100, 1),
        "p_valor_vs_azar": p_valor,
    }


def _cdf_normal_estandar(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _filtrar_saltos_espurios_serie(precios: list[dict]) -> list[dict]:
    """Mismo filtro de `refresco_diario._filtrar_saltos_espurios`, reimplementado
    aquí para no importar un job que hace su propio `main()` al cargarse."""
    ordenados = sorted(precios, key=lambda p: p["fecha"])
    descartar = set()
    for i in range(1, len(ordenados) - 1):
        a, b, c = ordenados[i - 1], ordenados[i], ordenados[i + 1]
        ca, cb, cc = _cierre(a), _cierre(b), _cierre(c)
        if not (ca and cb and cc):
            continue
        if abs(cb / ca - 1) > UMBRAL_SALTO_SOSPECHOSO and abs(cc / ca - 1) <= UMBRAL_SALTO_SOSPECHOSO:
            descartar.add(b["fecha"])
    return [p for p in precios if p["fecha"] not in descartar]


METRICAS = ["ebitda_ttm", "margen_ebitda", "margen_operacional", "margen_neto", "valor_patrimonial_accion"]

VENTANA_PERCENTIL_PERIODOS = 20  # ~5 años de trimestres -- lo que se le prometió a Alex como banda histórica
MULTIPLOS_PERCENTIL = ["per", "precio_valor_libro", "ev_ebitda", "deuda_ebitda"]


def percentil_de(valor_actual: float, historicos: list[float]) -> float:
    """% de valores históricos <= valor_actual. Método estándar (rango
    percentil empírico), sin interpolar -- con ~18-20 puntos, interpolar no
    aporta precisión real."""
    return round(sum(1 for v in historicos if v <= valor_actual) / len(historicos) * 100, 1)


def calcular_percentiles(serie_multiplos: dict[str, list[float]]) -> dict[str, dict]:
    """Para cada múltiplo: dónde está el valor MÁS RECIENTE frente a su
    propia distribución de los últimos `VENTANA_PERCENTIL_PERIODOS`. Un
    percentil alto no es necesariamente malo (podría ser porque mejoró de
    verdad) -- se reporta el rango, no un veredicto."""
    resultado = {}
    for multiplo, valores in serie_multiplos.items():
        vals = [v for v in valores if v is not None][-VENTANA_PERCENTIL_PERIODOS:]
        if len(vals) < 6:
            continue
        actual = vals[-1]
        resultado[multiplo] = {
            "valor_actual": round(actual, 3),
            "percentil": percentil_de(actual, vals),
            "minimo": round(min(vals), 3),
            "maximo": round(max(vals), 3),
            "mediana": round(sorted(vals)[len(vals) // 2], 3),
            "n": len(vals),
        }
    return resultado


def calcular_evolucion(filas: list[dict], precios: list[dict], acciones: float | None, emisor_slug: str) -> tuple[list[dict], dict[str, dict]]:
    """(serie, estadisticas). `precios` ya viene ordenado por fecha con
    `cierre_ajustado` y sin saltos espurios."""
    filas = sorted(filas, key=lambda f: _orden(f["anio"], f["periodo"]))
    filas, _ = descartar_escala_atipica(filas)
    declaradas = [f for f in filas if f.get("acumulado") is not None and f["periodo"] != "ANUAL"]
    if declaradas:
        acumulado = sum(1 for f in declaradas if f["acumulado"]) > 0
    else:
        acumulado, _ = detectar_acumulado(filas)
    desac = desacumular(filas) if acumulado else filas

    ebitda_ttm = serie_ttm_historica(desac, "ebitda", emisor_slug)
    ingresos_ttm = serie_ttm_historica(desac, "ingresos", emisor_slug)
    operacional_ttm = serie_ttm_historica(desac, "utilidad_operacional", emisor_slug)
    utilidad_ttm = serie_ttm_historica(desac, "utilidad_neta", emisor_slug)
    patrimonio_por_clave = {(f["anio"], f["periodo"]): f["patrimonio"] for f in filas if f.get("patrimonio") is not None}
    deuda_por_clave = {(f["anio"], f["periodo"]): f["deuda_financiera"] for f in filas if f.get("deuda_financiera") is not None}

    claves = sorted(
        set(ebitda_ttm) | set(ingresos_ttm) | set(operacional_ttm) | set(utilidad_ttm) | set(patrimonio_por_clave),
        key=lambda k: _orden(*k),
    )

    serie = []
    for anio, periodo in claves:
        fecha_cierre = _fecha_periodo(anio, periodo)
        ing = ingresos_ttm.get((anio, periodo))
        fila = {
            "anio": anio, "periodo": periodo, "fecha_cierre": fecha_cierre.isoformat(),
            "ebitda_ttm": ebitda_ttm.get((anio, periodo)),
            "margen_ebitda": round(ebitda_ttm[(anio, periodo)] / ing * 100, 2) if ing and (anio, periodo) in ebitda_ttm else None,
            "margen_operacional": round(operacional_ttm[(anio, periodo)] / ing * 100, 2) if ing and (anio, periodo) in operacional_ttm else None,
            "margen_neto": round(utilidad_ttm[(anio, periodo)] / ing * 100, 2) if ing and (anio, periodo) in utilidad_ttm else None,
            "valor_patrimonial_accion": round(patrimonio_por_clave[(anio, periodo)] * 1_000_000_000 / acciones, 2)
                if acciones and (anio, periodo) in patrimonio_por_clave else None,
        }
        fila["precio_contemporaneo"] = _precio_en_o_despues(precios, fecha_cierre, VENTANA_BUSQUEDA_PRECIO_DIAS)
        fila["precio_rezagado"] = _precio_en_o_despues(
            precios, fecha_cierre + timedelta(days=LAG_RADICACION_DIAS), VENTANA_BUSQUEDA_PRECIO_DIAS)

        # Múltiplos por período -- para las bandas de percentil (describen
        # dónde ha cotizado el emisor frente a sí mismo, no predicen), usan
        # el precio CONTEMPORÁNEO: no hay sesgo de anticipación que evitar
        # aquí, es una foto de la valoración de mercado en ese momento, no
        # una correlación contra un resultado que el mercado no conocía.
        cap_periodo = fila["precio_contemporaneo"] * acciones / 1_000_000_000 if fila["precio_contemporaneo"] and acciones else None
        ut = utilidad_ttm.get((anio, periodo))
        pat = patrimonio_por_clave.get((anio, periodo))
        deu = deuda_por_clave.get((anio, periodo))
        eb = ebitda_ttm.get((anio, periodo))
        fila["per"] = round(cap_periodo / ut, 2) if cap_periodo and ut and ut > 0 else None
        fila["precio_valor_libro"] = round(cap_periodo / pat, 2) if cap_periodo and pat and pat > 0 else None
        ev_periodo = round(cap_periodo + (deu or 0), 3) if cap_periodo is not None else None
        fila["ev_ebitda"] = round(ev_periodo / eb, 2) if ev_periodo is not None and eb and eb > 0 else None
        fila["deuda_ebitda"] = round(deu / eb, 2) if deu is not None and eb and eb > 0 else None

        serie.append(fila)

    estadisticas = {}
    for metrica in METRICAS:
        puntos = [f for f in serie if f[metrica] is not None]
        for sufijo, campo_precio in (("contemporaneo", "precio_contemporaneo"), ("rezagado", "precio_rezagado")):
            con_precio = [f for f in puntos if f[campo_precio] is not None]
            var_m, var_p = [], []
            for a, b in zip(con_precio, con_precio[1:]):
                if a[metrica] and a[campo_precio]:
                    var_m.append((b[metrica] - a[metrica]) / abs(a[metrica]))
                    var_p.append((b[campo_precio] - a[campo_precio]) / a[campo_precio])
            estadisticas[f"{metrica}__{sufijo}"] = {
                "r2": _pearson_r2(var_m, var_p),
                **_efectividad(var_m, var_p),
            }
    return serie, estadisticas


def main():
    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = {e["id"]: e for e in cliente.table("emisores").select("id,slug,nombre,sector").execute().data}
    instrumentos = cliente.table("instrumentos").select("emisor_id,activo_id,ticker,clase").execute().data
    fundamentales = cliente.table("fundamentales_reportados").select("*").execute().data

    por_emisor: dict = defaultdict(list)
    for f in fundamentales:
        if f["emisor_id"] in emisores:
            por_emisor[f["emisor_id"]].append(f)

    filas_serie, filas_stats, filas_percentiles = [], [], []
    procesados, sin_ticker, sin_acciones = 0, 0, 0
    for emisor_id, filas in por_emisor.items():
        em = emisores[emisor_id]
        # Bancos/holdings financieros SÍ entran (F4o): P/E y P/VL son válidos
        # para ellos (usan utilidad_neta y patrimonio, no ingresos/EBITDA).
        # Lo que no aplica -- margen_ebitda, margen_operacional, EV/EBITDA,
        # Deuda/EBITDA -- ya sale en None solo, porque ingresos/utilidad
        # operacional/ebitda se dejan sin poblar DESDE LA EXTRACCIÓN para
        # estos sectores (CAMPOS_NO_APLICABLES_FINANCIEROS en
        # extraer_xbrl.py), no hace falta un guard aparte aquí.
        propios = [i for i in instrumentos if i["emisor_id"] == emisor_id]
        ordinarias = [i for i in propios if not i["ticker"].startswith("PF")]
        elegido = (ordinarias or propios)
        if not elegido:
            sin_ticker += 1
            continue
        acciones, _ = acciones_del_emisor(sorted(filas, key=lambda f: _orden(f["anio"], f["periodo"])))
        if acciones is None:
            acciones, _ = ACCIONES_CURADAS_MANUALMENTE.get(em["slug"], (None, None))
        if acciones is None:
            sin_acciones += 1

        precios_crudos = _consultar_todo(
            cliente.table("precios").select("fecha,cierre,cierre_ajustado")
            .eq("activo_id", elegido[0]["activo_id"]).order("fecha")
        )
        for p in precios_crudos:
            p["fecha"] = date.fromisoformat(p["fecha"])
        precios = _filtrar_saltos_espurios_serie(precios_crudos)
        if not precios:
            continue

        serie, stats = calcular_evolucion(filas, precios, acciones, em["slug"])
        for fila in serie:
            filas_serie.append({"emisor_id": emisor_id, **fila})
        for metrica_sufijo, valores in stats.items():
            filas_stats.append({"emisor_id": emisor_id, "metrica": metrica_sufijo, **valores})

        series_multiplos = {m: [f[m] for f in serie] for m in MULTIPLOS_PERCENTIL}
        for multiplo, datos_percentil in calcular_percentiles(series_multiplos).items():
            filas_percentiles.append({"emisor_id": emisor_id, "multiplo": multiplo, **datos_percentil})
        procesados += 1

    if filas_serie:
        cliente.table("evolucion_fundamental_serie").delete().neq("emisor_id", 0).execute()
        for i in range(0, len(filas_serie), 500):
            cliente.table("evolucion_fundamental_serie").insert(filas_serie[i:i + 500]).execute()
    if filas_stats:
        cliente.table("evolucion_fundamental_estadisticas").delete().neq("emisor_id", 0).execute()
        for i in range(0, len(filas_stats), 500):
            cliente.table("evolucion_fundamental_estadisticas").insert(filas_stats[i:i + 500]).execute()
    if filas_percentiles:
        cliente.table("valoracion_percentiles").delete().neq("emisor_id", 0).execute()
        for i in range(0, len(filas_percentiles), 500):
            cliente.table("valoracion_percentiles").insert(filas_percentiles[i:i + 500]).execute()

    print(f"Emisores procesados: {procesados} (sin ticker: {sin_ticker}, sin acciones: {sin_acciones})")
    print(f"Filas de serie: {len(filas_serie)}, filas de estadística: {len(filas_stats)}, filas de percentil: {len(filas_percentiles)}")

    print(f"\n{'emisor_id':>10} {'métrica':<28} {'n':>4} {'R²':>6} {'efect%':>7} {'base%':>7} {'p':>7}")
    destacadas = sorted(
        [f for f in filas_stats if f["metrica"].endswith("__rezagado") and f["r2"] is not None],
        key=lambda f: f["r2"], reverse=True,
    )[:15]
    for f in destacadas:
        print(f"{f['emisor_id']:>10} {f['metrica']:<28} {f['n']:>4} {f['r2']:>6} "
              f"{f['efectividad_pct']:>7} {f['tasa_base_alza_pct']:>7} {f['p_valor_vs_azar']:>7}")


if __name__ == "__main__":
    main()
