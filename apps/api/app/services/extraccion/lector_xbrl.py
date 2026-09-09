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

**La única trampa del formato.** Las fechas de los contextos de duración NO son
de fiar: para una cifra anual de 2022 el contexto declara
`2022-12-01..2022-12-31`, un mes. Lo que sí es fiable es la convención del
identificador del contexto que usa el generador de la SFC:

    Context_Instant_Final_P1202212P   ->  P1 = periodo del informe, corte 2022-12
    Context_Instant_Final_P2202112P   ->  P2 = comparativo, corte 2021-12

Así que el período se resuelve por ese índice (`P1` es el del informe pedido),
nunca por las fechas. Es la misma lección que el canal de PDF: el criterio
tiene que describir el documento, no el capricho de quien lo generó.
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET

XBRLI = "{http://www.xbrl.org/2003/instance}"
XBRLDI = "{http://xbrl.org/2006/xbrldi}"
LINK = "{http://www.xbrl.org/2003/linkbase}"
XLINK = "{http://www.w3.org/1999/xlink}"

PATRON_CONTEXTO = re.compile(r"P(\d)(\d{4})(\d{2})([PA])")

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
        m = PATRON_CONTEXTO.search(c.get("id") or "")
        contextos[c.get("id")] = {
            "instante": periodo.findtext(f"{XBRLI}instant"),
            "indice": int(m.group(1)) if m else None,   # 1 = informe, 2 = comparativo
            "anio": int(m.group(2)) if m else None,
            "mes": int(m.group(3)) if m else None,
            "dims": dims,
            "es_final": "_Final_" in (c.get("id") or "") or periodo.findtext(f"{XBRLI}instant") is not None,
        }
    return contextos


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


def _buscar(hechos, contextos, conceptos, dims_exigidas=None, indice=1):
    """Primer hecho que case, respetando el orden de `conceptos`. Solo mira
    contextos del período pedido (`indice`); sin dimensiones, salvo que se
    exijan unas concretas -- un hecho dimensionado es un desglose (por
    segmento, por clase de acción, por componente del patrimonio), no el total.
    """
    dims_exigidas = dims_exigidas or {}
    for concepto in conceptos:
        for h in hechos:
            if h["concepto"] != concepto:
                continue
            ctx = contextos.get(h["ctx"])
            if ctx is None or ctx["indice"] != indice:
                continue
            if dims_exigidas:
                if any(ctx["dims"].get(k) != v for k, v in dims_exigidas.items()):
                    continue
            elif ctx["dims"]:
                continue
            valor = _a_numero(h["valor"])
            if valor is not None:
                return valor, concepto
    return None, None


ESCALAS_ACEPTADAS = (1, 1_000, 1_000_000)
TOLERANCIA_ESCALA = 0.05


def _escala_del_archivo(utilidad, acciones, por_accion):
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
    if not (utilidad and acciones and por_accion):
        return None, "sin utilidad por accion o sin acciones: no hay con que deducir la escala"
    razon = (por_accion * acciones) / utilidad
    for escala in ESCALAS_ACEPTADAS:
        if abs(razon - escala) / escala <= TOLERANCIA_ESCALA:
            return escala, (
                f"x{escala:,} deducida de utilidad por accion ({por_accion:,.2f}) x acciones "
                f"({acciones:,.0f}) / utilidad ({utilidad:,.0f}) = {razon:,.1f}"
            )
    return None, f"la razon utilidad-por-accion x acciones / utilidad da {razon:,.1f}, que no es una escala reconocible"


def leer(ruta_xbrl, anio: int, periodo: str, indice_periodo: int = 1) -> dict:
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

    del_periodo = [c for c in contextos.values() if c["indice"] == indice_periodo and c["anio"]]
    if not del_periodo:
        motivos.append(f"el archivo no trae contextos del período {indice_periodo}")
        return {"campos": {}, "unidad": None, "cuadra_balance": None,
                "motivos": motivos, "paginas_usadas": {}}
    anio_archivo = del_periodo[0]["anio"]
    if anio_archivo != anio:
        motivos.append(f"el archivo corresponde a {anio_archivo}, no a {anio} -- no se extrae")
        return {"campos": {}, "unidad": None, "cuadra_balance": None,
                "motivos": motivos, "paginas_usadas": {}}

    # La escala primero: sin ella no se puede convertir nada (ver
    # `_escala_del_archivo`).
    acciones, concepto_acc = _buscar(
        hechos, contextos, CONCEPTO_ACCIONES,
        dims_exigidas={EJE_CLASE_ACCION: MIEMBRO_ORDINARIA}, indice=indice_periodo,
    )
    por_accion, _ = _buscar(hechos, contextos, CONCEPTO_UTILIDAD_POR_ACCION, indice=indice_periodo)
    utilidad_bruta, _ = _buscar(hechos, contextos, CONCEPTOS["utilidad_neta"], indice=indice_periodo)
    escala, evidencia_escala = _escala_del_archivo(utilidad_bruta, acciones, por_accion)
    if escala is None and indice_periodo != 1:
        # La escala es propiedad del DOCUMENTO, no del periodo: el comparativo
        # rara vez trae acciones ni utilidad por accion propias, asi que se
        # deduce del periodo del informe y se reutiliza. Verificado real:
        # ECOPETROL 2022-ANUAL tagea acciones solo para 2022, y sin esto el
        # comparativo 2021 -- que viene completo en el mismo archivo -- se
        # perdia entero.
        acc1, _ = _buscar(hechos, contextos, CONCEPTO_ACCIONES,
                          dims_exigidas={EJE_CLASE_ACCION: MIEMBRO_ORDINARIA}, indice=1)
        pa1, _ = _buscar(hechos, contextos, CONCEPTO_UTILIDAD_POR_ACCION, indice=1)
        ut1, _ = _buscar(hechos, contextos, CONCEPTOS["utilidad_neta"], indice=1)
        escala, evidencia_escala = _escala_del_archivo(ut1, acc1, pa1)
        if escala is not None:
            evidencia_escala += " (deducida del período del informe y aplicada al comparativo)"
    if escala is None:
        motivos.append(evidencia_escala)
        return {"campos": {}, "unidad": None, "cuadra_balance": None, "motivos": motivos,
                "paginas_usadas": {}, "xbrl": {"escala": None, "evidencia_escala": evidencia_escala}}
    divisor = PESOS_POR_MIL_MILLONES / escala

    campos = {}
    origen_concepto = {}
    for campo, conceptos in CONCEPTOS.items():
        valor, concepto = _buscar(hechos, contextos, conceptos, indice=indice_periodo)
        origen_concepto[campo] = concepto
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
        dims_exigidas={EJE_PATRIMONIO: MIEMBRO_PATRIMONIO_TOTAL}, indice=indice_periodo,
    )
    campos["dividendos_decretados"] = {
        "valor": round(dividendos / divisor, 6) if dividendos else None,
        "pagina": None,
        "tabla": f"xbrl: {concepto_div}" if concepto_div else None,
    }

    # EBITDA sigue siendo derivado -- no es una línea NIIF, es métrica no-NIIF.
    depreciacion, _ = _buscar(hechos, contextos, CONCEPTO_DEPRECIACION, indice=indice_periodo)
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
    patrimonio_grupo, _ = _buscar(hechos, contextos, ["Equity"], indice=indice_periodo)
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
            "anio_contexto": anio_archivo,
            "utilidad_por_accion_reportada": por_accion,
            "conceptos": origen_concepto,
        },
    }


def periodos_disponibles(ruta_xbrl) -> list:
    """(indice, anio) de los períodos que trae el archivo — el del informe y su
    comparativo. Sirve para aprovechar los dos de una sola descarga."""
    contextos = _leer_contextos(ET.parse(str(ruta_xbrl)).getroot())
    vistos = {}
    for c in contextos.values():
        if c["indice"] and c["anio"]:
            vistos.setdefault(c["indice"], c["anio"])
    return sorted(vistos.items())
