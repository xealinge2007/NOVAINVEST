"""Analizador fundamental de la BVC (§3.4, F4b) — el entregable de F4a.

Toma lo que `extraer_fundamentales.py` dejó en `fundamentales_reportados`, lo
normaliza y calcula las métricas por emisor: TTM de resultados, márgenes, ROE,
apalancamiento, y las de mercado (capitalización, P/E, P/B) cruzando con
`precios`.

**Lo que este job resuelve y el extractor no puede:**

1. **Estanco vs acumulado.** Los estados intermedios colombianos reportan el
   estado de resultados ACUMULADO en el año, no el trimestre suelto. Está
   medido en los propios datos: T2/T1 da ≈2,0 de forma sistemática
   (BVC 2024: 80 → 164; Celsia 2024: 1.375 → 3.301; Cementos Argos 2023:
   3.382 → 6.713). Sumar cuatro trimestres tal como vienen contaría el primero
   cuatro veces. Aquí el trimestre suelto se obtiene restando el acumulado
   anterior — `T2 = YTD(T2) − YTD(T1)` — y el TTM se arma con esos.
   El balance NO se toca: es una foto a una fecha, no un acumulado.

2. **Acciones en circulación.** El extractor solo las deriva donde el emisor
   publica la utilidad por acción. El número de acciones cambia poco entre
   períodos, así que aquí se propaga el valor conocido más reciente de cada
   emisor a los períodos que no lo traen, marcándolo como propagado. Sin esto
   no hay ninguna métrica por acción.

**Lo que NO hace, a propósito:** no recomienda comprar ni vender. Devuelve las
métricas y la calidad del dato detrás de cada una; la decisión es de Alex.

Uso:
    python jobs/analizador_fundamental.py [--csv RUTA] [--min-campos 3]
"""

import argparse
import csv
import io
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

TRIMESTRES = ["T1", "T2", "T3", "T4"]
# Campos de FLUJO (se acumulan en el año). Los demás son de SALDO (foto a una fecha).
CAMPOS_FLUJO = ("ingresos", "utilidad_operacional", "utilidad_neta", "ebitda", "flujo_caja_operativo")
CAMPOS_SALDO = ("activos_totales", "pasivos_totales", "patrimonio", "deuda_financiera")


def _orden(anio: int, periodo: str) -> tuple:
    """Clave de orden cronológico. ANUAL cierra el año, después de T4."""
    return (anio, 5 if periodo == "ANUAL" else TRIMESTRES.index(periodo) + 1)


UMBRAL_ACUMULADO = 1.6  # T2/T1 por encima de esto = la serie viene acumulada


def detectar_acumulado(filas: list[dict]) -> tuple[bool, str]:
    """(la serie viene acumulada, evidencia). NO se asume: se mide en los datos
    del propio emisor.

    Suponerlo universal habria roto la mitad del universo. Medido sobre lo
    extraido: CELSIA da T2/T1 de 2,40 · 1,91 · 2,06 (acumulado) y ECOPETROL
    0,88 · 1,04 · 1,40 (estanco, cada trimestre por separado). Se usa la
    MEDIANA de las razones y no el promedio porque un solo trimestre atipico
    -- Ecopetrol 2026 da 1,40 aunque el emisor sea estanco -- no puede voltear
    la clasificacion de toda la serie.

    Con menos de dos años comparables no se decide: se deja como esta y se
    reporta, que es preferible a restar un acumulado que no era tal."""
    razones = []
    por_clave = {(f["anio"], f["periodo"]): f for f in filas}
    for (anio, periodo), f in por_clave.items():
        if periodo != "T2" or f.get("ingresos") in (None, 0):
            continue
        t1 = por_clave.get((anio, "T1"))
        if t1 and t1.get("ingresos"):
            razones.append(f["ingresos"] / t1["ingresos"])
    if len(razones) < 2:
        return False, f"indeterminado ({len(razones)} año(s) comparable(s)) -- se deja como se reportó"
    razones.sort()
    mediana = razones[len(razones) // 2] if len(razones) % 2 else (razones[len(razones) // 2 - 1] + razones[len(razones) // 2]) / 2
    detalle = " · ".join(f"{r:.2f}" for r in razones)
    if mediana >= UMBRAL_ACUMULADO:
        return True, f"acumulado (T2/T1 = {detalle})"
    return False, f"estanco (T2/T1 = {detalle})"


def descartar_escala_atipica(filas: list[dict]) -> tuple[list[dict], list[str]]:
    """Quita las filas cuyo activo total se sale de escala frente a la mediana
    del propio emisor. Es la ultima red antes de calcular: un error de unidad
    es siempre un factor de 1.000, y arruina cualquier ratio sin que se note.

    Verificado real: las filas ANUAL de ECOPETROL entraban por la plantilla por
    emisor, que devuelve millones sin convertir mientras el extractor generico
    convierte a miles de millones -- activos 306.369.507 contra 312.361 de su
    propio trimestre siguiente, y un ROE de 18.189%. Eso ya se corrigio en el
    origen (`extraer_fundamentales.PLANTILLAS_DESACTIVADAS`), pero la guarda se
    queda: el analizador no deberia poder publicar una cifra asi aunque el
    extractor se equivoque otra vez."""
    con = [f for f in filas if f.get("activos_totales")]
    if len(con) < 3:
        return filas, []
    valores = sorted(f["activos_totales"] for f in con)
    mediana = valores[len(valores) // 2]
    descartadas, avisos = [], []
    for f in filas:
        a = f.get("activos_totales")
        if a and (a > mediana * 20 or a < mediana / 20):
            avisos.append(f"{f['anio']}-{f['periodo']} activos={a:,.0f} vs mediana {mediana:,.0f}")
            continue
        descartadas.append(f)
    return descartadas, avisos


def desacumular(filas: list[dict]) -> list[dict]:
    """Convierte los campos de flujo de acumulado-en-el-año a trimestre suelto.

    `filas` son las de un solo emisor. T1 ya es el trimestre. Para T2/T3/T4 se
    resta el acumulado del trimestre anterior DEL MISMO AÑO; si ese trimestre
    falta, no se inventa: el trimestre queda sin valor de flujo (el de saldo
    sigue estando). ANUAL se deja como está — es el año completo, que es
    justamente lo que se quiere para el TTM.
    """
    por_clave = {(f["anio"], f["periodo"]): f for f in filas}
    salida = []
    for f in filas:
        g = dict(f)
        g["flujo_desacumulado"] = True
        if f["periodo"] in ("T2", "T3", "T4"):
            previo = por_clave.get((f["anio"], TRIMESTRES[TRIMESTRES.index(f["periodo"]) - 1]))
            for c in CAMPOS_FLUJO:
                if f.get(c) is None:
                    continue
                if previo is None or previo.get(c) is None:
                    g[c] = None
                    g["flujo_desacumulado"] = False
                else:
                    g[c] = round(f[c] - previo[c], 3)
        salida.append(g)
    return salida


def ttm(filas_desacumuladas: list[dict], campo: str) -> tuple[float | None, str]:
    """(valor TTM, cómo se obtuvo). Prefiere el ANUAL más reciente — es la cifra
    auditada y no depende de que estén los cuatro trimestres. Si no hay ANUAL,
    suma los cuatro últimos trimestres sueltos consecutivos."""
    anuales = [f for f in filas_desacumuladas if f["periodo"] == "ANUAL" and f.get(campo) is not None]
    if anuales:
        mejor = max(anuales, key=lambda f: f["anio"])
        return mejor[campo], f"anual {mejor['anio']}"

    trims = sorted(
        [f for f in filas_desacumuladas if f["periodo"] != "ANUAL" and f.get(campo) is not None],
        key=lambda f: _orden(f["anio"], f["periodo"]),
    )
    if len(trims) < 4:
        return None, "sin 4 trimestres"
    ultimos = trims[-4:]
    return round(sum(f[campo] for f in ultimos), 3), (
        f"suma {ultimos[0]['anio']}-{ultimos[0]['periodo']}..{ultimos[-1]['anio']}-{ultimos[-1]['periodo']}"
    )


def ultimo_saldo(filas: list[dict], campo: str) -> tuple[float | None, str]:
    """Último valor de un campo de saldo (balance): la foto más reciente."""
    con = [f for f in filas if f.get(campo) is not None]
    if not con:
        return None, ""
    mejor = max(con, key=lambda f: _orden(f["anio"], f["periodo"]))
    return mejor[campo], f"{mejor['anio']}-{mejor['periodo']}"


DISPERSION_MAXIMA_ACCIONES = 1.5  # max/min entre periodos


def acciones_del_emisor(filas: list[dict]) -> tuple[float | None, str]:
    """(acciones, evidencia). MEDIANA de lo derivado en todos los periodos, y
    solo si los periodos concuerdan entre si.

    El numero de acciones de una empresa cambia poco de un trimestre a otro, asi
    que la dispersion entre periodos es una prueba gratis de si la derivacion
    (utilidad neta / utilidad por accion) esta funcionando. Medido sobre lo
    extraido:

        GRUPO_CIBEST  11 periodos  966 M .. 979 M   -> concuerdan (real ~961 M)
        GRUPO_SURA     3 periodos  359 M .. 389 M   -> concuerdan (real ~469 M)
        BVC            2 periodos   66,0 M .. 66,1 M -> concuerdan (real ~60,5 M)
        MINEROS        6 periodos   98 M .. 300 M   -> NO concuerdan
        TERPEL        10 periodos  4,1 M .. 181 M   -> NO concuerdan

    En TERPEL y MINEROS la utilidad y la utilidad por accion no siempre cubren
    el mismo periodo (una fila trae el acumulado y la otra el trimestre), y el
    cociente sale disparatado. Cuando eso pasa se devuelve None: sin numero de
    acciones no hay P/E, que es preferible a un P/E calculado sobre un conteo
    que se sabe malo."""
    valores = sorted(f["acciones_en_circulacion"] for f in filas if f.get("acciones_en_circulacion"))
    if not valores:
        return None, ""
    if len(valores) == 1:
        return valores[0], "1 periodo, sin con qué contrastar"
    mediana = valores[len(valores) // 2]
    dispersion = valores[-1] / valores[0] if valores[0] else float("inf")
    if dispersion > DISPERSION_MAXIMA_ACCIONES:
        return None, f"descartado: {len(valores)} periodos dispersan {dispersion:.1f}x ({valores[0]:,.0f}..{valores[-1]:,.0f})"
    return mediana, f"mediana de {len(valores)} periodos (dispersión {dispersion:.2f}x)"


def _div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="ANALISIS_FUNDAMENTAL_BVC.csv")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = {e["id"]: e for e in cliente.table("emisores").select("id,slug,nombre,sector").execute().data}
    fundamentales = cliente.table("fundamentales_reportados").select("*").execute().data
    instrumentos = cliente.table("instrumentos").select("emisor_id,activo_id,ticker,clase").execute().data

    # Precio: el cierre más reciente de la acción ORDINARIA del emisor (las
    # "PF" son preferenciales, con precio propio; para capitalización se usa la
    # ordinaria, que es la que el conteo de acciones representa).
    precios = cliente.table("precios").select("activo_id,fecha,cierre").order("fecha", desc=True).limit(20000).execute().data
    ultimo_precio: dict = {}
    for p in precios:
        ultimo_precio.setdefault(p["activo_id"], p)

    por_emisor: dict = defaultdict(list)
    for f in fundamentales:
        if f["emisor_id"] in emisores:
            por_emisor[f["emisor_id"]].append(f)

    filas_salida = []
    for emisor_id, filas in por_emisor.items():
        em = emisores[emisor_id]
        filas = sorted(filas, key=lambda f: _orden(f["anio"], f["periodo"]))
        filas, avisos_escala = descartar_escala_atipica(filas)
        acumulado, evidencia = detectar_acumulado(filas)
        desac = desacumular(filas) if acumulado else filas

        ingresos, fuente_ing = ttm(desac, "ingresos")
        utilidad, fuente_ut = ttm(desac, "utilidad_neta")
        operacional, _ = ttm(desac, "utilidad_operacional")
        ebitda, _ = ttm(desac, "ebitda")
        patrimonio, fecha_pat = ultimo_saldo(filas, "patrimonio")
        activos, _ = ultimo_saldo(filas, "activos_totales")
        deuda, _ = ultimo_saldo(filas, "deuda_financiera")

        acciones, fecha_acc = acciones_del_emisor(filas)

        # Se prefiere la ORDINARIA: es la clase que el conteo de acciones
        # derivado de la utilidad por accion representa. Si el emisor solo
        # cotiza preferencial (Aval, Davivienda), se usa esa y se deja dicho --
        # la capitalizacion asi calculada es aproximada, porque las dos clases
        # cotizan a precios distintos.
        propios = [i for i in instrumentos if i["emisor_id"] == emisor_id]
        ordinarias = [i for i in propios if not i["ticker"].startswith("PF")]
        elegido = (ordinarias or propios)
        precio, ticker, clase_precio = None, "", ""
        if elegido:
            ticker = elegido[0]["ticker"]
            clase_precio = "ordinaria" if ordinarias else "preferencial (aprox.)"
            p = ultimo_precio.get(elegido[0]["activo_id"])
            precio = p["cierre"] if p else None

        # capitalización en miles de millones (las cifras contables ya están ahí)
        capitalizacion = None
        if precio is not None and acciones:
            capitalizacion = round(precio * acciones / 1_000_000_000, 3)

        filas_salida.append({
            "emisor": em["slug"],
            "nombre": em["nombre"],
            "sector": em["sector"],
            "ticker": ticker,
            "precio": precio,
            "acciones": acciones,
            "capitalizacion_mmm": capitalizacion,
            "ingresos_ttm": ingresos,
            "utilidad_neta_ttm": utilidad,
            "utilidad_operacional_ttm": operacional,
            "ebitda_ttm": ebitda,
            "patrimonio": patrimonio,
            "activos": activos,
            "deuda_financiera": deuda,
            "margen_neto": _pct(_div(utilidad, ingresos)),
            "margen_operacional": _pct(_div(operacional, ingresos)),
            "roe": _pct(_div(utilidad, patrimonio)),
            "deuda_patrimonio": _r(_div(deuda, patrimonio)),
            "eps_cop": _r(_div(utilidad * 1_000_000_000 if utilidad is not None else None, acciones), 2),
            "per": _r(_div(capitalizacion, utilidad)),
            "precio_valor_libro": _r(_div(capitalizacion, patrimonio)),
            "clase_precio": clase_precio,
            "serie_resultados": evidencia,
            "filas_descartadas_por_escala": " | ".join(avisos_escala),
            "fuente_resultados": fuente_ut,
            "fuente_ingresos": fuente_ing,
            "balance_de": fecha_pat,
            "acciones_de": fecha_acc,
            "periodos_con_cifras": len(filas),
        })

    filas_salida.sort(key=lambda r: (r["per"] is None, r["per"] if r["per"] is not None else 0))

    destino = Path(args.csv)
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_salida[0].keys()))
        w.writeheader()
        w.writerows(filas_salida)

    _imprimir(filas_salida)
    print(f"\nCSV: {destino.resolve()}")


def _r(v, dec=2):
    return None if v is None else round(v, dec)


def _pct(v):
    return None if v is None else round(v * 100, 1)


def _f(v, ancho=10, dec=1):
    if v is None:
        return "—".rjust(ancho)
    return f"{v:,.{dec}f}".rjust(ancho)


def _imprimir(filas):
    print("=" * 132)
    print("ANALIZADOR FUNDAMENTAL BVC — cifras en miles de millones de pesos; márgenes y ROE en %")
    print("=" * 132)
    print(f"{'EMISOR':<26}{'TICKER':<13}{'CAP.':>11}{'INGR.TTM':>12}{'UT.NETA':>11}{'PATRIM.':>11}{'M.NETO':>8}{'ROE':>8}{'D/P':>7}{'P/E':>8}{'P/VL':>7}")
    print("-" * 132)
    for r in filas:
        print(
            f"{r['emisor'][:25]:<26}{r['ticker']:<13}"
            f"{_f(r['capitalizacion_mmm'], 11, 0)}{_f(r['ingresos_ttm'], 12, 0)}{_f(r['utilidad_neta_ttm'], 11, 0)}"
            f"{_f(r['patrimonio'], 11, 0)}{_f(r['margen_neto'], 8)}{_f(r['roe'], 8)}{_f(r['deuda_patrimonio'], 7)}"
            f"{_f(r['per'], 8)}{_f(r['precio_valor_libro'], 7)}"
        )
    print("-" * 132)
    n = len(filas)
    for campo, etiqueta in (("per", "P/E"), ("roe", "ROE"), ("margen_neto", "margen neto"),
                            ("capitalizacion_mmm", "capitalización"), ("ingresos_ttm", "ingresos TTM")):
        print(f"  con {etiqueta:<16}: {sum(1 for r in filas if r[campo] is not None):2d}/{n}")


if __name__ == "__main__":
    main()
