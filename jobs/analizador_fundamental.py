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
        # `acumulado` viene del XBRL, que lo declara (ver
        # db/migrate_f4d_acumulado.sql). Cuando está, MANDA sobre lo que diga
        # la inferencia por razones T2/T1: un dato registrado le gana a uno
        # deducido. Cuando es False, la fila ya trae el trimestre suelto y
        # restarle el anterior lo destrozaría. Cuando es None -- las filas del
        # canal de PDF -- sigue valiendo la inferencia, que es lo único que hay.
        if f.get("acumulado") is False:
            salida.append(g)
            continue
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


SIN_EXTENSION_TTM = {
    # GRUPO_CIBEST_BANCOLOMBIA: desde 2025-T2 la serie trimestral pasó al
    # perímetro de Grupo Cibest (17-31% más grande que Bancolombia S.A. solo
    # -- ver EMISORES_SERIE_PARALELA_REEMPLAZA en extraer_xbrl.py), pero
    # 2025-ANUAL sigue siendo el perímetro viejo (no hay versión "Cibest" del
    # anual). Extender el TTM restaría un trimestre 2025 del perímetro NUEVO
    # contra un anual del perímetro VIEJO -- un salto de perímetro
    # disfrazado de variación real. Se prefiere el anual solo, desactualizado
    # pero consistente, hasta que exista un ANUAL 2026 ya en el perímetro
    # nuevo de punta a punta.
    "GRUPO_CIBEST_BANCOLOMBIA",
}


def ttm(filas_desacumuladas: list[dict], campo: str, emisor_slug: str | None = None) -> tuple[float | None, str]:
    """(valor TTM, cómo se obtuvo). Prefiere el ANUAL más reciente -- es la cifra
    auditada y no depende de que estén los cuatro trimestres -- pero lo
    EXTIENDE con trimestres sueltos más nuevos si ya los hay: real
    trailing-twelve-months = anual + trimestres del año siguiente ya
    publicados - los mismos trimestres del año del anual (que ya están
    contados dentro de él).

    Antes de F4h esto no se podía hacer con confianza: los trimestres
    comparativos de un año casi siempre venían en None por el bug de fechas
    de `lector_xbrl.py`, así que intentar restar un trimestre ausente habría
    dejado el TTM en None más seguido que acertar. Arreglado eso, extender es
    seguro -- y hace falta: NUTRESA con el anual 2025 solo (1.235,8) escondía
    que 2026-T1 fue pérdida y 2026-T2 tibio; el TTM real (extendido a
    2026-T2) es 601,4, la mitad. Si falta CUALQUIER trimestre del año base
    para restar, no se extiende ese tramo -- mejor quedarse en el anual
    (dato real, aunque más viejo) que inventar un TTM con un hueco. Tampoco
    se extiende si el emisor está en `SIN_EXTENSION_TTM` -- ver por qué ahí.

    Si no hay ANUAL, suma los cuatro últimos trimestres sueltos consecutivos."""
    anuales = [f for f in filas_desacumuladas if f["periodo"] == "ANUAL" and f.get(campo) is not None]
    trims_por_clave = {
        (f["anio"], f["periodo"]): f[campo]
        for f in filas_desacumuladas if f["periodo"] != "ANUAL" and f.get(campo) is not None
    }
    if anuales:
        base = max(anuales, key=lambda f: f["anio"])
        anio, valor, fuente = base["anio"], base[campo], f"anual {base['anio']}"
        if emisor_slug not in SIN_EXTENSION_TTM:
            while True:
                siguiente = anio + 1
                trims_siguiente = sorted(t for (a, t) in trims_por_clave if a == siguiente)
                if not trims_siguiente or not all((anio, t) in trims_por_clave for t in trims_siguiente):
                    break
                for t in trims_siguiente:
                    valor = valor - trims_por_clave[(anio, t)] + trims_por_clave[(siguiente, t)]
                fuente = f"anual {base['anio']} extendido a {siguiente}-{trims_siguiente[-1]}"
                anio = siguiente
        return round(valor, 3), fuente

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


ACCIONES_CURADAS_MANUALMENTE: dict[str, tuple[float, str]] = {
    # (acciones, fuente) — solo para emisores donde acciones_del_emisor()
    # no logra derivar nada confiable desde los estados financieros (ni un
    # solo período, o sin supermayoría entre clústeres). Cifra de ORDINARIA
    # en circulación (excluye tesorería), la clase que cotiza bajo el ticker
    # de cada emisor en esta tabla. Verificado 11-sep-2026, puede quedar
    # desactualizado tras un split, recompra o nueva emisión — revisar si el
    # precio implica una capitalización que no cuadra con el tamaño conocido
    # del emisor.
    "GRUPO_CIBEST_BANCOLOMBIA": (509_704_584, "Bancolombia SEC Form 6-K, 31-mar-2025 (acciones ordinarias)"),
    "GRUPO_SURA": (165_834_026, "Grupo SURA, Informe Circular 012 4T-2025, 31-dic-2025 (ordinarias en circulación, excluye readquiridas)"),
    "GRUPO_ARGOS": (398_953_357, "derivado de estados financieros (período más reciente tras la conversión de acciones con Grupo Sura); corroborado por la composición 58% ordinarias / 42% preferenciales reportada tras la escisión (58% de 685.301.741 totales ≈ 397,5M)"),
    "PROMIGAS": (1_134_848_043, "Promigas, Composición Accionaria (promigas.com/Documents/Inversionistas/Acciones-Promigas-202601.pdf)"),
    "MINEROS": (292_793_666, "Mineros S.A., tras 1er tramo de recompra de acciones, cierre 26-may-2026"),
    "ETB": (3_550_553_412, "Presentación corporativa ETB 2020-2021 — no se encontró una cifra más reciente; ETB no ha reportado splits ni recompras desde entonces"),
    "PEI": (43_142_200, "PEI, base tras el desdoblamiento de 2022 (431.422 -> 43.142.200 títulos); hay una 12a emisión en curso desde ago-2025 (~7M títulos adicionales) que puede no estar reflejada aún"),
    # BVC: sin cifra confiable — la búsqueda solo encontró una cifra de
    # tercero (27,38M) sin corroborar contra fuente oficial. Mejor sin P/E
    # que con un conteo que se sabe no verificado.
}

UMBRAL_SUPERMAYORIA_ACCIONES = 0.75


def acciones_del_emisor(filas: list[dict]) -> tuple[float | None, str]:
    """(acciones, evidencia). Agrupa lo derivado en cada período en clústeres
    que concuerdan entre sí (dispersión interna ≤ DISPERSION_MAXIMA_ACCIONES),
    y solo acepta la mediana del clúster si es una SUPERMAYORÍA (≥75% de los
    períodos) — no solo la mayoría simple.

    El número de acciones de una empresa cambia poco de un trimestre a otro,
    así que la dispersión entre períodos es una prueba gratis de si la
    derivación (utilidad neta / utilidad por acción) está funcionando. La
    primera versión de este descarte comparaba mínimo contra máximo de TODA
    la serie: bastaba un período mal derivado para tirar el conteo entero. La
    segunda versión podaba extremos hasta que la mitad de los períodos
    concordara — pero "la mitad" no es prueba de nada: en GRUPO_SURA (8 de 15
    períodos daban ~166M) y GRUPO_CIBEST (6 de 9 daban ~510M) esa mayoría
    simple ganaba sobre el clúster que en realidad es el correcto (~469M y
    ~961M respectivamente, verificado contra fuentes externas) — probablemente
    porque en varios períodos la utilidad usada es la del grupo consolidado y
    en otros la de la controladora, y ese quiebre no es aleatorio: se repite
    lo bastante seguido como para casi empatar con el clúster bueno.

    Con el umbral en 75%, SURA y CIBEST correctamente devuelven None en vez de
    un número plausible pero equivocado — para esos (y para los que nunca
    logran derivar nada: BVC, ETB, MINEROS, PEI, PROMIGAS, y ahora también
    GRUPO_ARGOS) el número de acciones se cura a mano en
    `ACCIONES_CURADAS_MANUALMENTE`, con su fuente documentada ahí. TERPEL sí
    pasa el umbral (15 de 17 períodos, 88%) y coincide con el conteo real."""
    valores = sorted(f["acciones_en_circulacion"] for f in filas if f.get("acciones_en_circulacion"))
    if not valores:
        return None, ""
    if len(valores) == 1:
        return valores[0], "1 periodo, sin con qué contrastar"

    clusteres = []
    for v in valores:
        if clusteres and v / clusteres[-1][0] <= DISPERSION_MAXIMA_ACCIONES:
            clusteres[-1].append(v)
        else:
            clusteres.append([v])
    mejor = max(clusteres, key=len)
    proporcion = len(mejor) / len(valores)

    if proporcion < UMBRAL_SUPERMAYORIA_ACCIONES:
        otros = ", ".join(f"{len(c)}x~{c[len(c)//2]:,.0f}" for c in sorted(clusteres, key=len, reverse=True))
        return None, f"descartado: sin supermayoría entre {len(valores)} periodos — clústeres: {otros}"

    mediana = mejor[len(mejor) // 2]
    if len(mejor) == len(valores):
        return mediana, f"mediana de {len(valores)} periodos (dispersión {valores[-1] / valores[0]:.2f}x)"
    return mediana, (f"mediana de {len(mejor)} de {len(valores)} periodos que concuerdan "
                      f"({proporcion:.0%}); descartados como outlier "
                      f"{len(valores) - len(mejor)}")


SECTORES_FINANCIEROS = {"banca", "holding_financiero"}

# Supuestos macro para el costo de capital — no salen de los estados
# financieros de cada emisor, son de mercado y se revisan a mano de vez en
# cuando, no cada corrida. Documentados aquí en vez de en una fuente en vivo
# porque no hay un conector confiable a la curva de TES en este proyecto
# todavía; si se agrega uno (F6, datos macro), esto se vuelve dinámico.
TASA_LIBRE_RIESGO = 0.10          # aprox. TES 10 años COP, revisar periódicamente
PRIMA_RIESGO_MERCADO = 0.075      # prima de riesgo accionario Colombia (estilo Damodaran), aprox.
SPREAD_CREDITO_APROX = 0.03       # sobre la libre de riesgo, para el costo de la deuda -- no hay gasto financiero por emisor para derivarlo directo
TASA_IMPUESTO_RENTA = 0.35        # tarifa de renta corporativa en Colombia


def _retornos_diarios(precios_activo: list[dict]) -> dict[str, float]:
    """{fecha: retorno_simple} a partir de una serie ordenada por fecha ascendente."""
    ordenados = sorted(precios_activo, key=lambda p: p["fecha"])
    retornos = {}
    anterior = None
    for p in ordenados:
        if anterior and anterior["cierre"]:
            retornos[p["fecha"]] = (p["cierre"] - anterior["cierre"]) / anterior["cierre"]
        anterior = p
    return retornos


def beta_vs_indice(retornos_activo: dict[str, float], retornos_indice: dict[str, float]) -> float | None:
    """Beta = cov(activo, índice) / var(índice), sobre las fechas en común.
    None si hay menos de 60 observaciones en común (~3 meses de pregones) --
    con menos que eso el número no es confiable."""
    fechas = sorted(set(retornos_activo) & set(retornos_indice))
    if len(fechas) < 60:
        return None
    ra = [retornos_activo[f] for f in fechas]
    ri = [retornos_indice[f] for f in fechas]
    media_a, media_i = sum(ra) / len(ra), sum(ri) / len(ri)
    cov = sum((a - media_a) * (i - media_i) for a, i in zip(ra, ri)) / len(fechas)
    var_i = sum((i - media_i) ** 2 for i in ri) / len(fechas)
    if var_i == 0:
        return None
    return cov / var_i


def costo_capital(beta: float, capitalizacion: float, deuda: float) -> tuple[float, float, float]:
    """(costo_patrimonio, costo_deuda_despues_de_impuesto, wacc) vía CAPM +
    estructura de capital a valor de mercado (deuda a valor en libros, que es
    lo único que hay)."""
    costo_patrimonio = TASA_LIBRE_RIESGO + beta * PRIMA_RIESGO_MERCADO
    costo_deuda_dt = (TASA_LIBRE_RIESGO + SPREAD_CREDITO_APROX) * (1 - TASA_IMPUESTO_RENTA)
    v = (capitalizacion or 0) + (deuda or 0)
    if v == 0:
        return costo_patrimonio, costo_deuda_dt, costo_patrimonio
    peso_patrimonio = (capitalizacion or 0) / v
    peso_deuda = (deuda or 0) / v
    wacc = peso_patrimonio * costo_patrimonio + peso_deuda * costo_deuda_dt
    return costo_patrimonio, costo_deuda_dt, wacc


PVL_IMPLAUSIBLE = 8.0
PER_IMPLAUSIBLE = 60.0


def revisar_multiplos(per, pvl, ticker) -> str:
    """Aviso cuando un múltiplo sale fuera de todo rango razonable. No se
    oculta la cifra ni se publica como si nada: se muestra marcada.

    Verificado real: GRUPO_NUTRESA sale con P/E 115,6 y P/VL 14,3, lo que
    implicaría una capitalización de 143 billones de pesos —más que Ecopetrol—
    para una compañía con 20,6 billones de ingresos. El precio no es un error
    de carga: la serie de Yahoo va de 45.217 en septiembre de 2023 a 316.000
    hoy, coherente con las OPA sobre la compañía. Pero un salto de 7x en el
    precio junto a un conteo de acciones estable deja dos sospechosos —una
    serie de precios sin ajustar por la reorganización, o un conteo que ya no
    corresponde a la acción que cotiza— y ninguno se puede descartar desde
    aquí. Marcarlo es lo honesto; adivinar cuál de los dos es, no."""
    avisos = []
    if pvl is not None and pvl > PVL_IMPLAUSIBLE:
        avisos.append(f"P/VL {pvl:.1f} fuera de rango")
    if per is not None and per > PER_IMPLAUSIBLE:
        avisos.append(f"P/E {per:.0f} fuera de rango")
    if not avisos:
        return ""
    return (" y ".join(avisos) + " — revisar el precio de " + (ticker or "la acción")
            + " o el conteo de acciones antes de usarlo")


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

    # Serie completa por activo (para beta vs. COLCAP) -- consulta aparte de
    # `precios` de arriba porque esa viene truncada a 20.000 filas globales y
    # para el beta hace falta la historia completa de cada activo, no solo el
    # último cierre.
    activo_icolcap = next((a["id"] for a in cliente.table("activos").select("id,ticker").eq("ticker", "ICOLCAP.CL").execute().data), None)
    retornos_icolcap: dict[str, float] = {}
    if activo_icolcap:
        serie = cliente.table("precios").select("fecha,cierre").eq("activo_id", activo_icolcap).order("fecha").limit(3000).execute().data
        retornos_icolcap = _retornos_diarios(serie)
    else:
        print("AVISO: no se encontró ICOLCAP.CL en `activos` -- no se puede calcular beta ni WACC para nadie.")

    por_emisor: dict = defaultdict(list)
    for f in fundamentales:
        if f["emisor_id"] in emisores:
            por_emisor[f["emisor_id"]].append(f)

    filas_salida = []
    for emisor_id, filas in por_emisor.items():
        em = emisores[emisor_id]
        filas = sorted(filas, key=lambda f: _orden(f["anio"], f["periodo"]))
        filas, avisos_escala = descartar_escala_atipica(filas)
        # Si alguna fila trae la periodicidad declarada, se usa esa y no se
        # infiere nada. La inferencia queda para las series que solo tienen
        # filas del canal de PDF.
        declaradas = [f for f in filas if f.get("acumulado") is not None and f["periodo"] != "ANUAL"]
        if declaradas:
            n_acum = sum(1 for f in declaradas if f["acumulado"])
            acumulado = n_acum > 0
            evidencia = (f"declarado por el XBRL en {n_acum} de {len(declaradas)} trimestres "
                         f"({'acumulado' if acumulado else 'trimestre suelto'})")
        else:
            acumulado, evidencia = detectar_acumulado(filas)
        desac = desacumular(filas) if acumulado else filas

        ingresos, fuente_ing = ttm(desac, "ingresos", em["slug"])
        utilidad, fuente_ut = ttm(desac, "utilidad_neta", em["slug"])
        operacional, _ = ttm(desac, "utilidad_operacional", em["slug"])
        ebitda, _ = ttm(desac, "ebitda", em["slug"])
        patrimonio, fecha_pat = ultimo_saldo(filas, "patrimonio")
        activos, _ = ultimo_saldo(filas, "activos_totales")
        deuda, _ = ultimo_saldo(filas, "deuda_financiera")

        acciones, fecha_acc = acciones_del_emisor(filas)
        if acciones is None and em["slug"] in ACCIONES_CURADAS_MANUALMENTE:
            acciones, fuente_manual = ACCIONES_CURADAS_MANUALMENTE[em["slug"]]
            fecha_acc = f"curado a mano: {fuente_manual}"

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

        # Creación de valor: ROIC vs. WACC. No aplica a bancos/holdings
        # financieros -- su "deuda" son depósitos de clientes, no financiación,
        # así que ni el capital invertido ni el costo de la deuda significan
        # lo mismo que en una empresa no financiera.
        beta = costo_patrimonio = costo_deuda_dt = wacc = roic = eva = None
        motivo_sin_roic = ""
        if em["sector"] in SECTORES_FINANCIEROS:
            motivo_sin_roic = "no aplica: sector financiero"
        elif not elegido or not retornos_icolcap:
            motivo_sin_roic = "sin ticker con precio o sin serie de COLCAP"
        else:
            serie_activo = cliente.table("precios").select("fecha,cierre").eq(
                "activo_id", elegido[0]["activo_id"]).order("fecha").limit(3000).execute().data
            retornos_activo = _retornos_diarios(serie_activo)
            beta = beta_vs_indice(retornos_activo, retornos_icolcap)
            if beta is None:
                motivo_sin_roic = "menos de 60 pregones en común con COLCAP para estimar beta"
            elif operacional is None:
                motivo_sin_roic = "sin utilidad operacional TTM"
            elif capitalizacion is None:
                motivo_sin_roic = "sin capitalización (falta precio o acciones)"
            else:
                costo_patrimonio, costo_deuda_dt, wacc = costo_capital(beta, capitalizacion, deuda)
                capital_invertido = (deuda or 0) + (patrimonio or 0)
                nopat = operacional * (1 - TASA_IMPUESTO_RENTA)
                roic = _div(nopat, capital_invertido)
                if capital_invertido and wacc is not None:
                    eva = round(nopat - wacc * capital_invertido, 1)

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
            "alerta_multiplos": revisar_multiplos(
                _r(_div(capitalizacion, utilidad)), _r(_div(capitalizacion, patrimonio)), ticker),
            "beta": _r(beta, 2),
            "costo_patrimonio": _pct(costo_patrimonio),
            "costo_deuda_dt": _pct(costo_deuda_dt),
            "wacc": _pct(wacc),
            "roic": _pct(roic),
            "eva_mmm": eva,
            "spread_valor": _pct(roic - wacc) if roic is not None and wacc is not None else None,
            "motivo_sin_roic": motivo_sin_roic,
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

    # slug -> emisor_id, para que la tabla en Supabase (que la API real lee)
    # tenga la misma llave primaria estable que el resto del esquema.
    slug_a_id = {e["slug"]: eid for eid, e in emisores.items()}
    filas_supabase = []
    for fila in filas_salida:
        fila_db = {k: v for k, v in fila.items() if k != "emisor"}
        fila_db["emisor_id"] = slug_a_id[fila["emisor"]]
        fila_db["slug"] = fila["emisor"]
        filas_supabase.append(fila_db)
    cliente.table("fundamentales_analisis").upsert(filas_supabase, on_conflict="emisor_id").execute()

    _imprimir(filas_salida)
    print(f"\nCSV: {destino.resolve()}")
    print(f"Supabase: {len(filas_supabase)} filas en fundamentales_analisis")


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
    alertadas = [r for r in filas if r["alerta_multiplos"]]
    if alertadas:
        print(f"\n  {len(alertadas)} emisor(es) con múltiplos fuera de rango:")
        for r in alertadas:
            print(f"    {r['emisor']}: {r['alerta_multiplos']}")
    print()
    n = len(filas)
    for campo, etiqueta in (("per", "P/E"), ("roe", "ROE"), ("margen_neto", "margen neto"),
                            ("capitalizacion_mmm", "capitalización"), ("ingresos_ttm", "ingresos TTM")):
        print(f"  con {etiqueta:<16}: {sum(1 for r in filas if r[campo] is not None):2d}/{n}")


if __name__ == "__main__":
    main()
