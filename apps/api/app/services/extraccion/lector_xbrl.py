"""Lector de los informes financieros XBRL radicados ante la Superfinanciera
(§5.1, canal D — 08-sep-2026).

**Por qué existe.** Todo el trabajo de `extractor_generico.py` es reconstruir,
a partir de un PDF, información que el emisor ya reportó estructurada. La SFC
publica en SIMEV el mismo estado financiero en XBRL desde 2015-T1, y ahí cada
cifra viene con su concepto NIIF, su unidad y su contexto. Contrastado contra
`ECOPETROL/2022-ANUAL`, que el canal de PDF ya extraía bien, las tres cifras
que se podían comparar coinciden **al peso**:

    activos        306.369.506.610 COP  ->  306.369,50661  (PDF: 306.369,507)
    ingresos       159.473.954.056 COP  ->  159.473,954056 (PDF: 159.473,954)
    utilidad neta   33.406.291.190 COP  ->   33.406,29119  (PDF:  33.406,291)

Y entrega cuatro cosas que el PDF no daba:

- **Acciones en circulación por clase** (41.116.694.690 ordinarias de
  Ecopetrol). Ese campo estaba en 0 de 193 filas y bloqueaba toda métrica por
  acción.
- **La distinción controladora / grupo como conceptos separados**
  (`ProfitLossAttributableToOwnersOfParent` vs `ProfitLoss`), que en el PDF
  había que resolver con dos pasadas de sinónimos.
- **Dividendos decretados**, otro campo que estaba vacío.
- **El período comparativo en el mismo archivo**, así que un archivo rinde dos.

Devuelve el mismo shape que `extractor_generico.extraer` para que el job que
escribe en `fundamentales_reportados` no tenga que distinguir el canal.

**Cómo se resuelve el período.** Por la FECHA DE CIERRE de cada contexto, que
es del documento, y no por el identificador, que es de quien lo generó. La
distinción costó una vuelta: el primer archivo que se probó (Ecopetrol, hecho
con `xbrlengine`) nombra sus contextos
`Context_Instant_Final_P1202212P` / `..._P2202112P`, y esa convención parecía
la del formato. No lo era. Al correr el corpus completo, **103 de 109 archivos
fallaron**: Grupo Sura, Celsia y el resto usan `p1`, `p2`, `p3` a secas. Es
exactamente el mismo error que ya se había cometido en el canal de PDF al atar
las reglas del triage al orden de concatenación de pdfplumber — una regla
deducida de un solo espécimen.

Lo que sí es común a todos: cada contexto declara un `instant` o un
`endDate`, y esa fecha de cierre ordena los períodos. La más reciente es la
del informe; la siguiente, el comparativo.

Queda una salvedad sobre las duraciones: Ecopetrol declara la suya como
`2022-12-01..2022-12-31` (un mes) para una cifra que es anual, mientras Celsia
declara bien `2022-01-01..2022-12-31` y además trae `2022-10-01..2022-12-31`,
que es el cuarto trimestre suelto. Por eso, entre contextos que cierran en la
misma fecha se prefiere **el de mayor duración**: con Celsia eso elige el año
sobre el trimestre, y con Ecopetrol elige el único que hay.
"""

import math
from datetime import date
from xml.etree import ElementTree as ET

XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"

PESOS_POR_MIL_MILLONES = 1_000_000_000

# Conceptos NIIF por campo, EN ORDEN DE PREFERENCIA. El primero que aparezca
# gana, así que el orden codifica una decisión contable, no un capricho:
# para utilidad y patrimonio manda lo ATRIBUIBLE A LA CONTROLADORA, porque es
# el numerador de cualquier métrica por acción; el total del grupo (que incluye
# el interés no controlante) queda de respaldo.
CONCEPTOS = {
    "activos_totales": ["Assets"],
    "pasivos_totales": ["Liabilities"],
    "patrimonio": ["EquityAttributableToOwnersOfParent", "Equity"],
    "ingresos": [
        "Revenue",
        "RevenueFromContractsWithCustomers",
        "RevenueFromSaleOfGoods",
        "RevenueFromRenderingOfServices",
    ],
    "utilidad_operacional": ["ProfitLossFromOperatingActivities"],
    "utilidad_neta": ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"],
    "flujo_caja_operativo": ["CashFlowsFromUsedInOperatingActivities"],
    "deuda_financiera": ["Borrowings", "BorrowingsNoncurrent"],
}

# Campos de FLUJO (cubren un período) vs. de SALDO (foto a una fecha) -- ver
# `_fechas_de_cierre` para por qué el comparativo trimestral necesita una
# fecha distinta para cada grupo.
CAMPOS_FLUJO = {"ingresos", "utilidad_operacional", "utilidad_neta", "flujo_caja_operativo"}

CONCEPTO_DEPRECIACION = ["DepreciationAndAmortisationExpense"]
CONCEPTO_ACCIONES = ["NumberOfSharesOutstanding", "NumberOfSharesIssued"]
CONCEPTO_DIVIDENDOS = ["DividendsPaid", "DividendsRecognisedAsDistributionsToOwners"]
CONCEPTO_UTILIDAD_POR_ACCION = ["BasicEarningsLossPerShare"]

EJE_CLASE_ACCION = "ClassesOfShareCapitalAxis"
MIEMBRO_ORDINARIA = "OrdinarySharesMember"
EJE_PATRIMONIO = "ComponentsOfEquityAxis"
MIEMBRO_PATRIMONIO_TOTAL = "EquityMember"

# Campos que son cifras en pesos y hay que llevar a miles de millones, la
# unidad en que ya está escrita `fundamentales_reportados`. Los que no están
# aquí (acciones) son conteos y se dejan como vienen.
CAMPOS_EN_PESOS = set(CONCEPTOS) | {"ebitda", "dividendos_decretados"}


def _sin_prefijo(texto: str) -> str:
    return (texto or "").split(":")[-1].strip()


def _leer_contextos(raiz) -> dict:
    contextos = {}
    for c in raiz.findall(f"{XBRLI}context"):
        periodo = c.find(f"{XBRLI}period")
        dims = {}
        for contenedor in (c.find(f"{XBRLI}entity/{XBRLI}segment"), c.find(f"{XBRLI}scenario")):
            if contenedor is not None:
                for m in contenedor.findall(f"{XBRLDI}explicitMember"):
                    dims[_sin_prefijo(m.get("dimension"))] = _sin_prefijo(m.text)
        instante = periodo.findtext(f"{XBRLI}instant")
        inicio = periodo.findtext(f"{XBRLI}startDate")
        fin = periodo.findtext(f"{XBRLI}endDate")
        contextos[c.get("id")] = {
            "instante": instante,
            "inicio": inicio,
            # La fecha de CIERRE es lo único que declaran igual todos los
            # generadores, y es lo que ordena los períodos.
            "fecha": instante or fin,
            "dias": _dias(inicio, fin),
            "dims": dims,
        }
    return contextos


def _dias(inicio, fin):
    """Duración en días, o None para un instante. Sirve para desempatar entre
    contextos que cierran el mismo día: el año contra el trimestre suelto."""
    if not (inicio and fin):
        return None
    try:
        return (date.fromisoformat(fin) - date.fromisoformat(inicio)).days
    except ValueError:
        return None


def _fechas_de_cierre(contextos) -> list:
    """Fechas de cierre del documento, de la más reciente a la más antigua,
    mirando solo contextos SIN dimensiones -- los de los estados primarios.
    La posición en esta lista es el índice de período: 1 = el del informe,
    2 = el comparativo. Cada elemento es `{"saldo": fecha, "flujo": fecha}`,
    no una fecha suelta -- ver por qué abajo.

    Se toma UNA fecha de SALDO por año, la más tardía. Verificado real y
    necesario: Ecopetrol declara además contextos de saldo INICIAL (instantes
    en 2022-12-01 y 2021-12-01, el arranque del estado de cambios en el
    patrimonio). Sin agrupar por año, esos se colaban entre el cierre del
    informe y el del comparativo, y el período 2 apuntaba al 2022-12-01 en vez
    del 2021-12-31 -- el comparativo entero se perdía.

    Para un informe TRIMESTRAL esa fecha de saldo no sirve para los campos de
    FLUJO del comparativo: el balance se compara contra el cierre del año
    anterior completo (ej. 2025-12-31), pero el estado de resultados se
    compara contra el mismo trimestre del año anterior (2025-03-31) -- dos
    fechas reales, DISTINTAS, dentro del mismo año calendario. Verificado real
    en GEB 2026-T1: el archivo trae contextos en 2025-12-31 (solo instante,
    sin duración) Y en 2025-03-31 (duración de 89 días) -- tomar solo la más
    tardía del año, como hacía la versión anterior, resolvía el comparativo a
    2025-12-31 y la utilidad neta del trimestre comparativo salía None (no hay
    ninguna duración que termine ahí). Por eso se guarda aparte la fecha de
    FLUJO: la más tardía del año que además tenga al menos un contexto de
    duración. Si no hay ninguna (año sin datos de flujo, o el caso normal
    donde saldo y flujo coinciden, como en un ANUAL), se usa la de saldo.
    """
    por_anio_saldo: dict[str, str] = {}
    por_anio_flujo: dict[str, str] = {}
    for c in contextos.values():
        if not c["fecha"] or c["dims"]:
            continue
        anio = c["fecha"][:4]
        if c["fecha"] > por_anio_saldo.get(anio, ""):
            por_anio_saldo[anio] = c["fecha"]
        if c.get("dias") is not None and c["fecha"] > por_anio_flujo.get(anio, ""):
            por_anio_flujo[anio] = c["fecha"]
    return [
        {"saldo": por_anio_saldo[anio], "flujo": por_anio_flujo.get(anio, por_anio_saldo[anio])}
        for anio in sorted(por_anio_saldo, reverse=True)
    ]


def _leer_hechos(raiz) -> list:
    hechos = []
    for e in raiz:
        if e.tag.startswith(XBRLI) or e.tag.startswith(LINK):
            continue
        if e.get("contextRef") is None:
            continue
        hechos.append({
            "concepto": e.tag.split("}")[-1],
            "ctx": e.get("contextRef"),
            "valor": (e.text or "").strip(),
        })
    return hechos


def _a_numero(texto):
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


# Duración (en días) del contexto que usó la última búsqueda. Es lo que
# permite registrar si un flujo es acumulado o del trimestre suelto en vez de
# inferirlo después — ver db/migrate_f4d_acumulado.sql.
_ULTIMA_DURACION = {"dias": None}


def _buscar(hechos, contextos, conceptos, fecha, dims_exigidas=None):
    """Hecho que case, respetando el orden de `conceptos`. Solo mira contextos
    que cierran en `fecha`; sin dimensiones, salvo que se exijan unas concretas
    -- un hecho dimensionado es un desglose (por segmento, por clase de acción,
    por componente del patrimonio), no el total.

    Entre varios candidatos gana el de MAYOR duración: en un informe anual eso
    elige el año completo sobre el trimestre suelto que algunos emisores
    incluyen con la misma fecha de cierre (Celsia trae `2022-01-01..2022-12-31`
    y `2022-10-01..2022-12-31`)."""
    dims_exigidas = dims_exigidas or {}
    cero = None
    for concepto in conceptos:
        candidatos = []
        for h in hechos:
            if h["concepto"] != concepto:
                continue
            ctx = contextos.get(h["ctx"])
            if ctx is None or ctx["fecha"] != fecha:
                continue
            if dims_exigidas:
                if any(ctx["dims"].get(k) != v for k, v in dims_exigidas.items()):
                    continue
            elif ctx["dims"]:
                continue
            valor = _a_numero(h["valor"])
            if valor is not None:
                candidatos.append((ctx["dias"] if ctx["dias"] is not None else -1, valor))
        if candidatos:
            elegido = max(candidatos, key=lambda x: x[0])
            valor = elegido[1]
            _ULTIMA_DURACION["dias"] = elegido[0] if elegido[0] >= 0 else None
            # Un CERO no gana sobre la alternativa. Verificado real y
            # necesario: varios emisores tagean
            # `ProfitLossAttributableToOwnersOfParent = 0` en el contexto
            # primario y ponen la cifra de verdad en `ProfitLoss` -- y como la
            # controladora va primero en la lista de preferencia, la utilidad
            # neta de BVC, MINEROS 2024 y CIBEST 2025 salia en cero. Lo mismo
            # con las acciones de GEB. Un cero exacto en activos, ingresos,
            # utilidad o acciones de un emisor de la BVC es un hueco de
            # etiquetado, no un dato; si TODAS las alternativas dan cero, se
            # devuelve el cero y que el llamador decida.
            if valor != 0:
                return valor, concepto
            if cero is None:
                cero = (valor, concepto)
    return cero if cero is not None else (None, None)


ESCALAS_ACEPTADAS = (1, 1_000, 1_000_000)
# Holgura contra la potencia de mil mas cercana. Es amplia a proposito: la
# utilidad por accion no es exactamente utilidad / acciones -- se calcula sobre
# el PROMEDIO PONDERADO de acciones del periodo, y la utilidad que la acompana
# puede ser la de operaciones continuas y no la total. Medido sobre el corpus,
# la razon se va entre 0,68 y 1,8 veces la escala real en emisores donde el
# resto de la lectura es impecable (balance cuadrando al peso). Exigir 5% dejo
# 156 de 218 periodos sin leer por un contraste que nunca pretendio ser exacto.
#
# Que sea amplia no la vuelve laxa: las tres escalas posibles estan a factor
# 1.000 una de otra, asi que una ventana de 3x no puede confundirlas.
FACTOR_HOLGURA_ESCALA = 3.0


# Banda de activos totales de un emisor de la BVC, en miles de millones de
# pesos. El ancho es deliberadamente de un factor 1.000 EXACTO: como las tres
# escalas posibles estan a factor 1.000 una de otra, a lo sumo una puede dejar
# el activo dentro de la banda, y la prueba nunca es ambigua.
#
# Los extremos son reales, no inventados: el emisor mas chico del universo
# (BVC) ronda el billon de pesos y el mas grande (Bancolombia) los 363
# billones. Se dejo margen a ambos lados. Como referencia de que el techo es
# sano: el PIB de Colombia esta en el orden de 1.500 billones, asi que un solo
# emisor con 70.000 billones de activos -- lo que daba GRUPO_SURA con la
# escala mal deducida -- es imposible por varios ordenes de magnitud.
MIN_ACTIVOS_MMM = 500
MAX_ACTIVOS_MMM = 500_000


def _escalas_plausibles_por_magnitud(activos_brutos):
    """Escalas que dejan el activo total dentro de la banda. Ninguna, una, o
    en el peor caso ninguna -- por el ancho de la banda no pueden ser dos."""
    if not activos_brutos:
        return []
    return [e for e in ESCALAS_ACEPTADAS
            if MIN_ACTIVOS_MMM <= activos_brutos * e / PESOS_POR_MIL_MILLONES <= MAX_ACTIVOS_MMM]


def _escala_del_archivo(utilidad, acciones, por_accion, activos_brutos=None):
    """(factor, evidencia) para llevar las cifras monetarias a pesos.

    Hace falta porque **el archivo miente sobre su propia unidad**: declara
    `unitRef="peso"` (iso4217:COP) y `decimals="0"` en los 10.606 hechos
    monetarios, pero la aritmetica del propio documento lo desmiente. Ecopetrol
    2022 reporta utilidad 33.406.291.190 y 41.116.694.690 acciones: el cociente
    da 0,81 por accion, y el mismo archivo declara
    `BasicEarningsLossPerShare = 813`. Factor 1.000 -- las cifras estan en
    MILES de pesos, no en pesos. Se contrasto ademas contra lo que el canal de
    PDF ya extraia bien del mismo periodo (306.369,507 miles de millones de
    activos), y cuadra al aplicar ese mismo factor.

    No se codifica "la SFC reporta en miles" como constante: eso es la
    suposicion por emisor que ya nos costo caro en el canal de PDF. Se deduce
    de la redundancia que el archivo trae consigo -- utilidad por accion x
    acciones tiene que dar la utilidad -- y solo se acepta si el resultado cae
    cerca de una potencia de mil. Si no hay con que deducirla, se devuelve
    None y el documento va a revision, igual que un balance que no cuadra.
    """
    por_magnitud = _escalas_plausibles_por_magnitud(activos_brutos)

    if not (utilidad and acciones and por_accion):
        # Sin utilidad por accion no hay contraste aritmetico, pero la magnitud
        # sola alcanza cuando deja una sola escala en pie.
        if len(por_magnitud) == 1:
            return por_magnitud[0], (
                f"x{por_magnitud[0]:,} por magnitud: es la unica escala que deja el activo total "
                f"({activos_brutos * por_magnitud[0] / PESOS_POR_MIL_MILLONES:,.0f} miles de millones) "
                f"dentro de lo posible para un emisor de la BVC"
            )
        return None, "sin utilidad por accion o sin acciones, y la magnitud no basta para deducir la escala"
    razon = (por_accion * acciones) / utilidad
    if razon <= 0:
        return None, f"la razon utilidad-por-accion x acciones / utilidad da {razon:,.1f}"
    escala = min(ESCALAS_ACEPTADAS, key=lambda e: abs(math.log(razon / e)))
    cerca = 1 / FACTOR_HOLGURA_ESCALA <= razon / escala <= FACTOR_HOLGURA_ESCALA

    # La MAGNITUD manda sobre el contraste aritmetico cuando se contradicen.
    # Verificado real y necesario: GRUPO_SURA deducia x1.000.000 en la mitad de
    # sus archivos y x1.000 en la otra mitad, para los MISMOS periodos --
    # 70.941.764 contra 75.902 miles de millones de activos. La razon
    # utilidad-por-accion no es fiable ahi (su utilidad por accion no se
    # calcula sobre las acciones que tagea), pero la magnitud no deja lugar a
    # dudas: un emisor con 70.941.764 miles de millones de activos tendria 47
    # veces el PIB del pais.
    if por_magnitud and escala not in por_magnitud:
        if len(por_magnitud) == 1:
            return por_magnitud[0], (
                f"x{por_magnitud[0]:,} por magnitud, descartando la x{escala:,} que sugeria la "
                f"utilidad por accion (razon {razon:,.1f}): esa dejaba el activo total en "
                f"{activos_brutos * escala / PESOS_POR_MIL_MILLONES:,.0f} miles de millones, imposible"
            )
        return None, (
            f"la utilidad por accion sugiere x{escala:,} pero la magnitud del activo lo desmiente, "
            "y la magnitud sola no deja una unica escala en pie"
        )

    if cerca:
        return escala, (
            f"x{escala:,} deducida de utilidad por accion ({por_accion:,.2f}) x acciones "
            f"({acciones:,.0f}) / utilidad ({utilidad:,.0f}) = {razon:,.1f}"
        )
    if len(por_magnitud) == 1:
        return por_magnitud[0], f"x{por_magnitud[0]:,} por magnitud (la razon {razon:,.1f} no concluia)"
    return None, f"la razon utilidad-por-accion x acciones / utilidad da {razon:,.1f}, que no cae cerca de ninguna escala"


def _vacio(motivos, evidencia_escala=None) -> dict:
    """Salida sin cifras, con el MISMO shape que la buena. Que los retornos
    tempranos omitieran la clave `xbrl` rompía a quien la leyera sin
    comprobarla -- una forma cara de descubrir un problema."""
    return {"campos": {}, "unidad": None, "cuadra_balance": None, "motivos": motivos,
            "paginas_usadas": {},
            "xbrl": {"escala": None, "evidencia_escala": evidencia_escala,
                     "punto_entrada": None, "conceptos": {}}}


def leer(ruta_xbrl, anio: int, periodo: str, indice_periodo: int = 1, escala_conocida=None) -> dict:
    """Mismo shape que `extractor_generico.extraer`.

    `indice_periodo`: 1 es el período del informe; 2 es el comparativo, que
    viene en el mismo archivo y permite aprovecharlo para dos períodos.
    """
    raiz = ET.parse(str(ruta_xbrl)).getroot()
    contextos = _leer_contextos(raiz)
    hechos = _leer_hechos(raiz)
    motivos = []

    esquema = raiz.find(f"{LINK}schemaRef")
    punto_entrada = (esquema.get(f"{XLINK}href") if esquema is not None else "") or ""
    # El punto de entrada dice si el informe es consolidado ("-con-") o
    # separado ("-ind-"). Es la regla dura de Alex, verificable en el archivo
    # mismo en vez de deducida del nombre o del título de una página.
    if "-con-" not in punto_entrada:
        motivos.append(f"el punto de entrada no es consolidado: {punto_entrada.rsplit('/', 1)[-1]}")

    fechas = _fechas_de_cierre(contextos)
    if len(fechas) < indice_periodo:
        motivos.append(f"el archivo solo trae {len(fechas)} fecha(s) de cierre; se pidió la {indice_periodo}")
        return _vacio(motivos)
    fecha = fechas[indice_periodo - 1]["saldo"]
    fecha_flujo = fechas[indice_periodo - 1]["flujo"]
    anio_archivo = int(fecha[:4])
    if anio_archivo != anio:
        motivos.append(f"el cierre {fecha} no corresponde a {anio} -- no se extrae")
        return _vacio(motivos)

    # La escala primero: sin ella no se puede convertir nada (ver
    # `_escala_del_archivo`). `por_accion` y `utilidad_bruta` son de FLUJO
    # (ver `_fechas_de_cierre`) -- en un comparativo trimestral, buscarlos en
    # `fecha` (la de saldo) los perdía si esa fecha no tenía duración.
    acciones, concepto_acc = _buscar(
        hechos, contextos, CONCEPTO_ACCIONES,
        fecha, dims_exigidas={EJE_CLASE_ACCION: MIEMBRO_ORDINARIA},
    )
    por_accion, _ = _buscar(hechos, contextos, CONCEPTO_UTILIDAD_POR_ACCION, fecha_flujo)
    utilidad_bruta, _ = _buscar(hechos, contextos, CONCEPTOS["utilidad_neta"], fecha_flujo)
    activos_brutos, _ = _buscar(hechos, contextos, CONCEPTOS["activos_totales"], fecha)
    escala, evidencia_escala = _escala_del_archivo(utilidad_bruta, acciones, por_accion, activos_brutos)
    if escala is None and escala_conocida:
        # La escala la fija el EMISOR (su generador de XBRL y su convención de
        # presentación), no cada archivo. Cuando un año concreto no trae con qué
        # deducirla -- sin utilidad por acción o sin acciones etiquetadas -- se
        # acepta la que ya se dedujo de otro año del mismo emisor, y se dice de
        # dónde vino. Es la misma lógica que heredar la escala al comparativo,
        # un nivel más arriba.
        escala = escala_conocida
        evidencia_escala = f"x{escala:,} heredada de otro período del mismo emisor"
    if escala is None and indice_periodo != 1:
        # La escala es propiedad del DOCUMENTO, no del periodo: el comparativo
        # rara vez trae acciones ni utilidad por accion propias, asi que se
        # deduce del periodo del informe y se reutiliza. Verificado real:
        # ECOPETROL 2022-ANUAL tagea acciones solo para 2022, y sin esto el
        # comparativo 2021 -- que viene completo en el mismo archivo -- se
        # perdia entero.
        acc1, _ = _buscar(hechos, contextos, CONCEPTO_ACCIONES,
                          fechas[0]["saldo"], dims_exigidas={EJE_CLASE_ACCION: MIEMBRO_ORDINARIA})
        pa1, _ = _buscar(hechos, contextos, CONCEPTO_UTILIDAD_POR_ACCION, fechas[0]["flujo"])
        ut1, _ = _buscar(hechos, contextos, CONCEPTOS["utilidad_neta"], fechas[0]["flujo"])
        act1, _ = _buscar(hechos, contextos, CONCEPTOS["activos_totales"], fechas[0]["saldo"])
        escala, evidencia_escala = _escala_del_archivo(ut1, acc1, pa1, act1)
        if escala is not None:
            evidencia_escala += " (deducida del período del informe y aplicada al comparativo)"
    if escala is None:
        motivos.append(evidencia_escala)
        return _vacio(motivos, evidencia_escala)
    divisor = PESOS_POR_MIL_MILLONES / escala

    # Cuando el emisor no tagea ningún conteo directo de acciones -- BVC no
    # trae `NumberOfSharesOutstanding` ni `NumberOfSharesIssued` en ningún
    # contexto, ni siquiera en cero -- se reconstruye con la misma identidad
    # que ya usa `_escala_del_archivo` para validar la escala: utilidad /
    # utilidad-por-acción = acciones. Verificado real: para BVC 2025-ANUAL da
    # ~65,8 millones, del orden de magnitud público conocido del emisor -- no
    # es una invención, es la cifra que el propio informe ya implica con sus
    # otras dos cifras, solo que no la tagea aparte.
    if not acciones and utilidad_bruta and por_accion:
        acciones = round(utilidad_bruta * escala / por_accion)
        concepto_acc = f"{CONCEPTOS['utilidad_neta'][-1]} / {CONCEPTO_UTILIDAD_POR_ACCION[0]} (derivado, sin conteo directo tageado)"

    campos = {}
    origen_concepto = {}
    dias_flujo = None
    for campo, conceptos in CONCEPTOS.items():
        _ULTIMA_DURACION["dias"] = None
        fecha_del_campo = fecha_flujo if campo in CAMPOS_FLUJO else fecha
        valor, concepto = _buscar(hechos, contextos, conceptos, fecha_del_campo)
        origen_concepto[campo] = concepto
        # `ingresos` es el flujo de referencia: su contexto es el que dice si
        # el estado de resultados de este informe va acumulado o por trimestre.
        if campo == "ingresos" and valor is not None:
            dias_flujo = _ULTIMA_DURACION["dias"]
        if campo == "utilidad_neta" and dias_flujo is None and valor is not None:
            dias_flujo = _ULTIMA_DURACION["dias"]
        campos[campo] = {
            "valor": round(valor / divisor, 6) if valor is not None else None,
            "pagina": None,
            "tabla": f"xbrl: {concepto}" if concepto else None,
        }

    # acciones: se pidieron arriba con la clase ORDINARIA explícita. El total
    # sin dimensión no existe en estos archivos (Ecopetrol trae los tres
    # miembros del eje, con las preferenciales en cero), y mezclar clases daría
    # un conteo que no corresponde al precio de ninguna de las dos.
    campos["acciones_en_circulacion"] = {
        "valor": acciones, "pagina": None,
        "tabla": f"xbrl: {concepto_acc} (acciones ordinarias)" if concepto_acc else None,
    }

    dividendos, concepto_div = _buscar(
        hechos, contextos, CONCEPTO_DIVIDENDOS,
        fecha, dims_exigidas={EJE_PATRIMONIO: MIEMBRO_PATRIMONIO_TOTAL},
    )
    campos["dividendos_decretados"] = {
        "valor": round(dividendos / divisor, 6) if dividendos else None,
        "pagina": None,
        "tabla": f"xbrl: {concepto_div}" if concepto_div else None,
    }

    # EBITDA sigue siendo derivado -- no es una línea NIIF, es métrica no-NIIF.
    depreciacion, _ = _buscar(hechos, contextos, CONCEPTO_DEPRECIACION, fecha_flujo)
    operacional = campos["utilidad_operacional"]["valor"]
    if operacional is not None and depreciacion is not None:
        campos["ebitda"] = {
            "valor": round(operacional + depreciacion / divisor, 6),
            "pagina": None,
            "tabla": "derivado: ProfitLossFromOperatingActivities + DepreciationAndAmortisationExpense",
        }
    else:
        campos["ebitda"] = {"valor": None, "pagina": None, "tabla": None}

    # Chequeo contable, igual que en el canal de PDF. Ojo: `patrimonio` puede
    # ser el atribuible a la controladora, que NO cuadra con activos - pasivos
    # cuando hay interés no controlante, así que el chequeo usa el patrimonio
    # TOTAL del grupo, que es el que cierra la ecuación.
    patrimonio_grupo, _ = _buscar(hechos, contextos, ["Equity"], fecha)
    activos = campos["activos_totales"]["valor"]
    pasivos = campos["pasivos_totales"]["valor"]
    cuadra = None
    if activos and pasivos is not None and patrimonio_grupo is not None:
        total = pasivos + patrimonio_grupo / divisor
        cuadra = abs(total - activos) / activos <= 0.01

    # Contraste interno gratis: utilidad neta / acciones tiene que dar la
    # utilidad por acción que el propio emisor reportó. Si no coincide, algo
    # se está leyendo del contexto equivocado.
    if por_accion and acciones and campos["utilidad_neta"]["valor"] is not None:
        implicita = campos["utilidad_neta"]["valor"] * PESOS_POR_MIL_MILLONES / acciones
        if abs(implicita - por_accion) / abs(por_accion) > 0.02:
            motivos.append(
                f"la utilidad por acción implícita ({implicita:.2f}) no coincide con la "
                f"reportada ({por_accion:.2f})"
            )

    if not any(c["valor"] is not None for c in campos.values()):
        motivos.append("ningún concepto NIIF de los buscados aparece en el archivo")

    return {
        "campos": campos,
        "unidad": "miles_de_millones",
        "cuadra_balance": cuadra,
        "motivos": motivos,
        "paginas_usadas": {},
        "xbrl": {
            "punto_entrada": punto_entrada.rsplit("/", 1)[-1],
            "escala": escala,
            "evidencia_escala": evidencia_escala,
            "dias_periodo": dias_flujo,
            # Acumulado = el flujo arranca en enero. Un trimestre suelto dura
            # ~90 días; el acumulado de T2 ~180, el de T3 ~270, el anual ~365.
            # El corte en 100 separa limpio, no hay nada entre medias.
            #
            # Un informe ANUAL es acumulado por definición y no se le pregunta
            # al archivo: el generador de Ecopetrol declara su duración anual
            # como `2022-12-01..2022-12-31` (30 días) para una cifra que es de
            # todo el año. La duración declarada se guarda igual, para poder
            # auditar, pero no decide.
            "acumulado": True if periodo == "ANUAL" else (None if dias_flujo is None else dias_flujo > 100),
            "anio_contexto": anio_archivo,
            "utilidad_por_accion_reportada": por_accion,
            "conceptos": origen_concepto,
        },
    }


def periodos_disponibles(ruta_xbrl) -> list:
    """(indice, anio) de los períodos que trae el archivo — el del informe y su
    comparativo. Sirve para aprovechar los dos de una sola descarga."""
    contextos = _leer_contextos(ET.parse(str(ruta_xbrl)).getroot())
    return [(i, int(f["saldo"][:4])) for i, f in enumerate(_fechas_de_cierre(contextos), start=1)]
