# -*- coding: utf-8 -*-
"""V3 del plan v4: prueba punto-en-el-tiempo del motor de valor contra tres rivales simples.

Pregunta única: lo que el sistema llamó barato, ¿rindió más que lo que llamó caro?

- Datos: estados anuales de `fundamentales_reportados` (2019-2025: el XBRL de la Superfinanciera empieza en
  2020 con 2019 como comparativo; lo anterior es PDF parcial) y precios diarios de `precios` (desde 2016-09).
- Punto en el tiempo: el anual del año Y se considera conocido el 1 de abril de Y+1 (plazo legal de
  publicación más un margen). Se forma la cartera ese día con el precio de cierre de ese día y se mide el
  retorno total (cierre ajustado por dividendos) a 1 y 3 años.
- Motor: la misma lógica pura de `app/services/valoracion.py` (EPV y DCF; el menor de los dos; bancos por
  P/VL justificado) con el beta sectorial de V2 y los supuestos macro de HOY (no hay serie histórica del
  TES cargada: sesgo declarado; en un ranking de corte transversal pesa poco porque mueve a todos a la vez).
  Holdings y vehículos inmobiliarios quedan fuera: su valor depende de precios de las participaciones que no
  se reconstruyen en el tiempo.
- Rivales: libro / precio (P/VL inverso), EBIT / EV (inverso de EV/EBIT; no financieros) y rendimiento por
  dividendo.
- Métricas por cohorte: correlación de rangos (Spearman) entre señal y retorno, y diferencia de retorno
  entre el tercio más barato y el más caro. Pocos datos: el resultado se lee como "descarta / no descarta".
- Sesgo de supervivencia: solo están los emisores que siguen listados hoy.

Solo lee la base. Escribe `db/BACKTEST_V3.md` y `BACKTEST_V3_OBSERVACIONES.csv`.
Uso: python jobs/backtest_valor.py
"""
import csv
import io
import sys
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, median

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))
sys.path.insert(0, str(RAIZ / "jobs"))

from app.services import valoracion as v  # noqa: E402
from app.services.lentes import beta_sectorial  # noqa: E402
from analizador_fundamental import SUPUESTOS_POR_DEFECTO, costo_capital, costo_patrimonio_capm  # noqa: E402

# Desviación declarada frente al motor en vivo: 3 años de EBIT en vez de 4 (`ANIOS_MINIMOS_EBIT`). Con la serie
# desde 2019, exigir 4 dejaría al motor con 2 cohortes. Se reporta también cuántas observaciones tendrían 4.
ANIOS_MINIMOS_BACKTEST = 3
MES_DIA_FORMACION = (4, 1)
SENALES = ("motor", "libro_precio", "ebit_ev", "dividendo")
NOMBRE = {"motor": "Motor de valor (EPV/DCF/P-VL justificado)", "libro_precio": "Rival 1: libro / precio",
          "ebit_ev": "Rival 2: EBIT / EV", "dividendo": "Rival 3: rendimiento por dividendo"}
CAMPOS = ("anio,utilidad_operacional,ingresos,patrimonio,deuda_financiera,efectivo,interes_minoritario,"
          "utilidad_neta,dividendos_decretados,acciones_en_circulacion,resultado_asociadas,utilidad_minoritarios")


def todas(consulta, paso=1000):
    filas, i = [], 0
    while True:
        lote = consulta.range(i, i + paso - 1).execute().data
        filas += lote
        if len(lote) < paso:
            return filas
        i += paso


def precio_en(serie, dia, campo):
    """Primer cierre en o después de `dia` (máx. 10 días después), o None."""
    for f, fila in serie:
        if f >= dia:
            return fila.get(campo) if f <= dia + timedelta(days=10) else None
    return None


def spearman(xs, ys):
    n = len(xs)
    if n < 4:
        return None

    def rangos(z):
        orden = sorted(range(n), key=lambda i: z[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and z[orden[j + 1]] == z[orden[i]]:
                j += 1
            for k in range(i, j + 1):
                r[orden[k]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rangos(xs), rangos(ys)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def tercios(xs, ys):
    """Retorno medio del tercio con la señal más alta (más barato) menos el del tercio más bajo."""
    n = len(xs)
    if n < 6:
        return None
    orden = sorted(range(n), key=lambda i: xs[i])
    k = n // 3
    return mean(ys[i] for i in orden[-k:]) - mean(ys[i] for i in orden[:k])


def valor_motor(slug, arq, sector, serie, Y, cap, acciones, sup):
    """Valor del patrimonio por acción con datos hasta Y. None si no determinable."""
    desde = v.PERIMETRO_DESDE.get(slug, 0)
    anios = sorted(a for a in serie if desde <= a <= Y)
    f = serie.get(Y) or {}
    if not anios or Y not in serie or not acciones:
        return None
    if arq == "banco":
        util = {a: serie[a]["utilidad_neta"] for a in anios if serie[a].get("utilidad_neta") is not None}
        pat = {a: serie[a]["patrimonio"] for a in anios if serie[a].get("patrimonio")}
        roes, _ = v.roes_banco(util, pat)
        if len(roes) < ANIOS_MINIMOS_BACKTEST or not f.get("patrimonio"):
            return None
        beta, _ = beta_sectorial(sector, None, None)
        ke = costo_patrimonio_capm(beta, sup)
        esc = v.escenarios_banco([r for _, r in roes], ke, f["patrimonio"] - (f.get("interes_minoritario") or 0), acciones)
        return esc["central"]["por_accion"]
    if arq not in ("real", "infraestructura_mercado"):
        return None
    con_asoc = slug in v.EMISORES_CON_ASOCIADAS
    ebit = {}
    for a in anios:
        e = serie[a].get("utilidad_operacional")
        if e is None:
            continue
        ebit[a] = v.ebit_equivalente(e, serie[a].get("resultado_asociadas") or 0) if con_asoc else e
    if len(ebit) < ANIOS_MINIMOS_BACKTEST:
        return None
    deuda = f.get("deuda_financiera") or 0
    beta, _ = beta_sectorial(sector, deuda, cap, sup["tasa_renta"])
    _, _, wacc = costo_capital(beta, cap, deuda, sup)
    deuda_neta = deuda - (f.get("efectivo") or 0)
    minoritarios = f.get("interes_minoritario") or 0
    central, _, _, plano, ult3 = v.normalizar_ebit(ebit, slug)
    _, eq_epv = v.valor_epv(central, wacc, deuda_neta, minoritarios)
    if eq_epv is None:
        return None
    epv = eq_epv * 1e9 / acciones
    ingresos = {a: serie[a].get("ingresos") for a in anios if serie[a].get("ingresos")}
    margenes = v.margenes_ebit(ingresos, {a: serie[a]["utilidad_operacional"] for a in anios
                                          if serie[a].get("utilidad_operacional") is not None})
    capital = (f.get("patrimonio") or 0) + minoritarios + deuda_neta
    roic = central * (1 - v.TASA_NOMINAL) / capital if capital > 0 else None
    dcf = None
    if len(margenes) >= ANIOS_MINIMOS_BACKTEST and f.get("ingresos") and roic:
        m = sum(margenes.values()) / len(margenes)
        r = v.dcf_dos_etapas(f["ingresos"], m, wacc, roic, deuda_neta, minoritarios, acciones)
        dcf = r["por_accion"]
    valor = min(epv, dcf) if dcf is not None else epv
    return max(valor, 0.0)


def main():
    from app.database import cliente_servicio
    cl = cliente_servicio()
    sup = dict(SUPUESTOS_POR_DEFECTO)
    try:
        sup.update({x["parametro"]: float(x["valor"]) for x in cl.table("supuestos_macro").select("parametro,valor").execute().data})
    except Exception:
        pass
    emisores = cl.table("emisores").select("id,slug,arquetipo,sector").execute().data
    activos = {a["id"]: a["ticker"] for a in cl.table("activos").select("id,ticker").execute().data}
    instrumentos = {}
    for i in cl.table("instrumentos").select("emisor_id,activo_id").execute().data:
        instrumentos.setdefault(i["emisor_id"], []).append(i["activo_id"])
    anuales = {}
    for f in todas(cl.table("fundamentales_reportados").select("emisor_id," + CAMPOS).eq("periodo", "ANUAL")):
        anuales.setdefault(f["emisor_id"], {})[f["anio"]] = f

    obs = []
    hoy = date.today()
    for em in emisores:
        arq = v.ARQUETIPO_VALORACION.get(em["slug"], em["arquetipo"])
        ids = instrumentos.get(em["id"], [])
        # instrumento: el ordinario si existe (no PF), si no el preferencial
        ids.sort(key=lambda a: activos.get(a, "").startswith("PF"))
        if not ids:
            continue
        serie_p = todas(cl.table("precios").select("fecha,cierre,cierre_ajustado").eq("activo_id", ids[0]).order("fecha"))
        serie_p = [(date.fromisoformat(p["fecha"][:10]), p) for p in serie_p if p.get("cierre")]
        serie = anuales.get(em["id"], {})
        for Y in sorted(serie):
            d0 = date(Y + 1, *MES_DIA_FORMACION)
            if d0 > hoy:
                continue
            f = serie[Y]
            p0, a0 = precio_en(serie_p, d0, "cierre"), precio_en(serie_p, d0, "cierre_ajustado")
            acciones = f.get("acciones_en_circulacion")
            if not p0 or not a0 or not acciones:
                continue
            cap = p0 * acciones / 1e9
            rets = {}
            for h in (1, 3):
                a1 = precio_en(serie_p, d0 + timedelta(days=365 * h), "cierre_ajustado")
                rets[h] = (a1 / a0 - 1) if a1 and d0 + timedelta(days=365 * h) <= hoy else None
            if rets[1] is None:
                continue
            valor = valor_motor(em["slug"], arq, em["sector"], serie, Y, cap, acciones, sup)
            ev = cap + (f.get("deuda_financiera") or 0) - (f.get("efectivo") or 0) + (f.get("interes_minoritario") or 0)
            ebit = f.get("utilidad_operacional")
            obs.append({
                "slug": em["slug"], "arquetipo": arq, "anio_datos": Y, "formacion": d0.isoformat(), "precio": p0,
                "motor": (valor / p0) if valor is not None else None,
                "valor_motor": valor,
                "libro_precio": (f["patrimonio"] - (f.get("interes_minoritario") or 0)) / cap if f.get("patrimonio") else None,
                "ebit_ev": (ebit / ev) if ebit is not None and ev > 0 and arq not in ("banco", "holding") else None,
                "dividendo": (f["dividendos_decretados"] / cap) if f.get("dividendos_decretados") else 0.0,
                "ret_1a": rets[1], "ret_3a": rets[3],
            })

    with open(RAIZ / "BACKTEST_V3_OBSERVACIONES.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(obs[0].keys()))
        w.writeheader()
        w.writerows(obs)

    def evaluar(senal, horizonte, universo):
        filas = [o for o in obs if o[senal] is not None and o[f"ret_{horizonte}a"] is not None and universo(o)]
        cohortes = sorted({o["formacion"] for o in filas})
        por_cohorte = []
        for c in cohortes:
            xs = [o[senal] for o in filas if o["formacion"] == c]
            ys = [o[f"ret_{horizonte}a"] for o in filas if o["formacion"] == c]
            por_cohorte.append({"cohorte": c, "n": len(xs), "spearman": spearman(xs, ys), "tercios": tercios(xs, ys)})
        validas = [p for p in por_cohorte if p["spearman"] is not None]
        return {
            "n": len(filas), "cohortes": por_cohorte,
            "spearman_medio": mean(p["spearman"] for p in validas) if validas else None,
            "cohortes_positivas": sum(1 for p in validas if p["spearman"] > 0), "cohortes_validas": len(validas),
            "tercios_medio": mean(p["tercios"] for p in por_cohorte if p["tercios"] is not None)
            if any(p["tercios"] is not None for p in por_cohorte) else None,
        }

    con_motor = {(o["slug"], o["formacion"]) for o in obs if o["motor"] is not None}
    resultados = {}
    for h in (1, 3):
        for nombre_u, u in (("propio", lambda o: True), ("comun", lambda o: (o["slug"], o["formacion"]) in con_motor)):
            for s in SENALES:
                resultados[(s, h, nombre_u)] = evaluar(s, h, u)

    def f(x, pct=False, dec=2):
        if x is None:
            return "—"
        return f"{x * 100:+.1f} pp" if pct else f"{x:+.{dec}f}"

    lineas = ["# NOVAINVEST — V3: prueba del motor de valor contra la historia", "",
              f"Generado por `jobs/backtest_valor.py` el {hoy.isoformat()}. Reproducible: solo lee la base.", "",
              "## Resultado", ""]
    m1, r_mejor = resultados[("motor", 1, "comun")], None
    rivales_1 = {s: resultados[(s, 1, "comun")] for s in SENALES if s != "motor"}
    r_mejor = max(rivales_1, key=lambda s: rivales_1[s]["spearman_medio"] if rivales_1[s]["spearman_medio"] is not None else -9)
    supera = (m1["spearman_medio"] is not None and rivales_1[r_mejor]["spearman_medio"] is not None
              and m1["spearman_medio"] > rivales_1[r_mejor]["spearman_medio"])
    lineas += [
        f"- Observaciones emisor-año con retorno a 1 año: **{len(obs)}**; con valor del motor: **{len(con_motor)}** "
        f"({len({o['formacion'] for o in obs if o['motor'] is not None})} cohortes anuales).",
        f"- Correlación de rangos media a 1 año, mismo universo: motor **{f(m1['spearman_medio'])}**, mejor rival "
        f"({NOMBRE[r_mejor]}) **{f(rivales_1[r_mejor]['spearman_medio'])}**.",
        f"- Tercio barato menos tercio caro, retorno a 1 año: motor **{f(m1['tercios_medio'], True)}**.",
        "",
        ("**Veredicto: el motor SUPERA al mejor rival simple en esta muestra.** No es prueba (muy pocas cohortes); "
         "solo dice que la muestra no lo descarta." if supera else
         f"**Veredicto: el motor NO supera al rival simple ({NOMBRE[r_mejor]}).** Regla del plan v4: el rival simple "
         "pasa a ser la referencia principal del ordenamiento y el valor intrínseco queda como una lente más del consenso."),
        "", "## Detalle por señal", "",
        "| Señal | Horizonte | Universo | n | Spearman medio | Cohortes > 0 | Tercio barato − caro |",
        "|---|---|---|---|---|---|---|"]
    for h in (1, 3):
        for u in ("comun", "propio"):
            for s in SENALES:
                r = resultados[(s, h, u)]
                lineas.append(f"| {NOMBRE[s]} | {h} año(s) | {'común con el motor' if u == 'comun' else 'propio'} | {r['n']} | "
                              f"{f(r['spearman_medio'])} | {r['cohortes_positivas']}/{r['cohortes_validas']} | {f(r['tercios_medio'], True)} |")
    lineas += ["", "## Por cohorte (1 año, universo común)", "", "| Cohorte | " + " | ".join(NOMBRE[s] for s in SENALES) + " |",
               "|---|" + "---|" * len(SENALES)]
    for i, c in enumerate(resultados[("motor", 1, "comun")]["cohortes"]):
        celdas = []
        for s in SENALES:
            coh = next((x for x in resultados[(s, 1, "comun")]["cohortes"] if x["cohorte"] == c["cohorte"]), None)
            celdas.append(f"ρ {f(coh['spearman'])} (n={coh['n']})" if coh else "—")
        lineas.append(f"| {c['cohorte']} | " + " | ".join(celdas) + " |")
    lineas += ["", "## Límites (léase antes de usar el resultado)", "",
               "- Muestra corta: fundamentales anuales 2019-2025 → a lo sumo 6 cohortes a 1 año y 4 a 3 años; el motor necesita "
               f"{ANIOS_MINIMOS_BACKTEST} años de EBIT, así que arranca con los datos de 2021. El plan v4 suponía 2016-2025: el XBRL "
               "de la Superfinanciera empieza en 2020 y lo anterior es PDF parcial.",
               f"- Desviación declarada: {ANIOS_MINIMOS_BACKTEST} años mínimos de EBIT en vez de {v.ANIOS_MINIMOS_EBIT}.",
               "- Supuestos macro (TES, primas) de hoy aplicados a todas las fechas; beta sectorial, no histórico.",
               "- Sesgo de supervivencia: solo emisores listados hoy.",
               "- Holdings y PEI fuera del motor en la prueba; Davivienda y PEI casi sin historia de precio.",
               "- Retorno con el cierre ajustado de Yahoo (dividendos); eventos como la escisión Sura-Argos pueden no estar bien ajustados.",
               "- Los parámetros de V2 se fijaron (commit 86302c7) ANTES de correr esta prueba y no se tocan después de verla."]
    (RAIZ / "db" / "BACKTEST_V3.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    resumen = {"supera_al_rival": supera, "mejor_rival": r_mejor, "spearman_motor_1a": m1["spearman_medio"],
               "spearman_rival_1a": rivales_1[r_mejor]["spearman_medio"], "observaciones": len(obs),
               "observaciones_motor": len(con_motor), "tercios_motor_1a": m1["tercios_medio"],
               "tercios_rival_1a": rivales_1[r_mejor]["tercios_medio"], "fecha": hoy.isoformat()}
    import json
    (RAIZ / "apps" / "web" / "src" / "data").mkdir(parents=True, exist_ok=True)
    (RAIZ / "apps" / "web" / "src" / "data" / "backtest_v3.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
