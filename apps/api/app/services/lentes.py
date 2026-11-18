# -*- coding: utf-8 -*-
"""V2 del plan v4: calibración del costo de capital, tres lentes de valor y veredicto por consenso.

Lógica PURA (sin base de datos). La usan `jobs/analizador_fundamental.py` (beta sectorial) y
`jobs/ranking_valor.py` (lentes, consenso y puntajes de calidad).

Reglas de la casa que se mantienen: rango y no un número solo; "no determinable" cuando falta el dato;
cada supuesto nombrado aquí. Estos parámetros quedan FIJOS antes del backtest de V3 (plan v4 §5:
no se recalibra para que "dé bonito").
"""
from statistics import median

# ---------------------------------------------------------------------------
# 1. Costo de capital: beta sectorial reapalancado (Damodaran, mercados emergentes)
# ---------------------------------------------------------------------------
# El beta por regresión diaria contra el COLCAP mide liquidez, no riesgo: una acción que casi no
# negocia sale con beta ~0 (Fabricato -0,09, ETB 0,02, Nutresa 0,06) y su Ke queda por debajo del de
# un banco grande. Se reemplaza por el beta DESAPALANCADO de la industria (tablas de Damodaran para
# mercados emergentes, valores redondeados de la edición de enero de 2025; revisar cada enero) y se
# reapalanca con la deuda de cada emisor (Hamada). Los financieros usan el beta apalancado de la
# industria directamente: su deuda es materia prima, no estructura de capital.
BETA_DESAPALANCADO_SECTOR = {
    "telecomunicaciones": 0.60,
    "cemento_construccion": 0.75,
    "petroleo_gas": 0.70,
    "energia_utilities": 0.45,
    "energia_infraestructura": 0.45,
    "mineria": 0.90,
    "consumo_retail": 0.70,
    "consumo": 0.55,
    "textil": 0.75,
    "quimicos_petroquimica": 0.80,
    "infraestructura_mercado": 0.80,
    "inmobiliario": 0.55,
    "holding": 0.75,
    "holding_cemento": 0.75,
}
BETA_APALANCADO_FINANCIERO = {"banca": 0.85, "holding_financiero": 0.90}
BETA_DESAPALANCADO_DEFECTO = 0.75
BETA_MINIMO = 0.60          # piso: ninguna acción de la BVC es menos riesgosa que 0,6 veces el mercado
BETA_MAXIMO = 2.00
DEUDA_PATRIMONIO_MAXIMA_BETA = 3.0   # tope al D/E del reapalancamiento: con más, el beta explota por una cifra


def beta_sectorial(sector: str | None, deuda: float | None, capitalizacion: float | None,
                   tasa: float = 0.35) -> tuple[float, str]:
    """(beta, explicación). Financieros: beta apalancado de su industria. Resto: beta desapalancado de la
    industria x (1 + (1 - t) x D/E), con D/E a valor de mercado y tope `DEUDA_PATRIMONIO_MAXIMA_BETA`;
    sin capitalización se usa D/E = 0 (beta de la industria sin deuda). Siempre entre `BETA_MINIMO` y
    `BETA_MAXIMO`."""
    if sector in BETA_APALANCADO_FINANCIERO:
        b = BETA_APALANCADO_FINANCIERO[sector]
        return b, f"beta de la industria {sector} (financiero, sin reapalancar) {b:.2f}"
    bu = BETA_DESAPALANCADO_SECTOR.get(sector, BETA_DESAPALANCADO_DEFECTO)
    de = (deuda or 0) / capitalizacion if capitalizacion and capitalizacion > 0 else 0.0
    de = min(max(de, 0.0), DEUDA_PATRIMONIO_MAXIMA_BETA)
    b = bu * (1 + (1 - tasa) * de)
    acotado = min(max(b, BETA_MINIMO), BETA_MAXIMO)
    nota = f"beta desapalancado {sector or 'sin sector'} {bu:.2f} reapalancado con D/E {de:.2f} = {b:.2f}"
    if acotado != b:
        nota += f" (acotado a {acotado:.2f})"
    return acotado, nota


# ---------------------------------------------------------------------------
# 2. Lentes
# ---------------------------------------------------------------------------
MULTIPLO_MAXIMO_VALIDO = {"per": 60.0, "precio_valor_libro": 10.0, "ev_ebitda": 30.0}
OBSERVACIONES_MINIMAS_HISTORIA = 8     # trimestres con el múltiplo para usar la propia historia
VENTANA_HISTORIA = 40                   # hasta 10 años de trimestres
PARES_MINIMOS = 3                       # emisores en el grupo, contando al propio

# Grupos de pares y los múltiplos que tienen sentido en cada uno.
GRUPOS_PARES = {
    "banca": ({"BANCO_DE_BOGOTA", "GRUPO_AVAL", "GRUPO_CIBEST_BANCOLOMBIA", "DAVIVIENDA_GROUP"},
              ("precio_valor_libro", "per")),
    "energia": ({"GEB", "ISA", "CELSIA", "PROMIGAS"}, ("ev_ebitda", "per")),
    "holdings": ({"GRUPO_ARGOS", "GRUPO_SURA", "CORFICOLOMBIANA"}, ("precio_valor_libro",)),
    "cemento_construccion": ({"CEMENTOS_ARGOS", "CONSTRUCTORA_CONCONCRETO", "EL_CONDOR"}, ("ev_ebitda",)),
}
# Múltiplos por defecto para la lente de propia historia, según el tipo de negocio.
MULTIPLOS_HISTORIA_FINANCIERO = ("precio_valor_libro", "per")
MULTIPLOS_HISTORIA_REAL = ("ev_ebitda", "per", "precio_valor_libro")


def multiplo_valido(nombre: str, valor) -> bool:
    return valor is not None and 0 < valor <= MULTIPLO_MAXIMO_VALIDO.get(nombre, 1e9)


def precio_implicito(precio: float, multiplo_actual: float, multiplo_referencia: float, nombre: str,
                     ev_por_accion: float | None = None, deuda_neta_por_accion: float | None = None):
    """Precio por acción que tendría la acción si cotizara al múltiplo de referencia. Para P/U y P/VL es
    proporcional (precio x ref / actual). Para EV/EBITDA se escala el EV y se resta la deuda neta:
    (EV x ref / actual) - deuda neta, todo por acción; sin EV por acción se cae a proporcional."""
    if not multiplo_valido(nombre, multiplo_actual) or not multiplo_valido(nombre, multiplo_referencia) or not precio:
        return None
    if nombre == "ev_ebitda" and ev_por_accion and deuda_neta_por_accion is not None:
        return max(ev_por_accion * multiplo_referencia / multiplo_actual - deuda_neta_por_accion, 0.0)
    return precio * multiplo_referencia / multiplo_actual


def lente_historia(serie: dict, actuales: dict, precio: float, financiero: bool, **ev):
    """Lente 2: múltiplos contra la propia historia. `serie` = {múltiplo: [valores trimestrales en orden]}.
    Por cada múltiplo con >= `OBSERVACIONES_MINIMAS_HISTORIA` observaciones válidas en los últimos
    `VENTANA_HISTORIA` trimestres: precio implícito a la mediana histórica. Valor de la lente = mediana
    de los precios implícitos. None si ningún múltiplo alcanza."""
    detalle = []
    for nombre in (MULTIPLOS_HISTORIA_FINANCIERO if financiero else MULTIPLOS_HISTORIA_REAL):
        valores = [x for x in (serie.get(nombre) or [])[-VENTANA_HISTORIA:] if multiplo_valido(nombre, x)]
        if len(valores) < OBSERVACIONES_MINIMAS_HISTORIA:
            continue
        ref = median(valores)
        p = precio_implicito(precio, actuales.get(nombre), ref, nombre, **ev)
        if p is None:
            continue
        rango = sorted(valores)
        detalle.append({"multiplo": nombre, "actual": round(actuales[nombre], 2), "mediana": round(ref, 2),
                        "percentil_actual": round(sum(1 for x in valores if x <= actuales[nombre]) / len(valores) * 100),
                        "minimo": round(rango[0], 2), "maximo": round(rango[-1], 2), "n": len(valores),
                        "precio_implicito": round(p, 1)})
    if not detalle:
        return None
    return {"valor": round(median(d["precio_implicito"] for d in detalle), 1), "multiplos": detalle}


def grupo_de(slug: str):
    for nombre, (miembros, multiplos) in GRUPOS_PARES.items():
        if slug in miembros:
            return nombre, miembros, multiplos
    return None, set(), ()


def lente_pares(slug: str, actuales_por_emisor: dict, precio: float, **ev):
    """Lente 3: múltiplos contra pares. Precio implícito a la mediana de los OTROS miembros del grupo
    con múltiplo válido; exige que el grupo tenga al menos `PARES_MINIMOS` emisores con dato (contando
    al propio). Valor de la lente = mediana de los precios implícitos de cada múltiplo."""
    grupo, miembros, multiplos = grupo_de(slug)
    if not grupo:
        return None
    propios = actuales_por_emisor.get(slug) or {}
    detalle = []
    for nombre in multiplos:
        otros = {s: (actuales_por_emisor.get(s) or {}).get(nombre) for s in miembros if s != slug}
        otros = {s: x for s, x in otros.items() if multiplo_valido(nombre, x)}
        if len(otros) + 1 < PARES_MINIMOS:
            continue
        ref = median(otros.values())
        p = precio_implicito(precio, propios.get(nombre), ref, nombre, **ev)
        if p is None:
            continue
        detalle.append({"multiplo": nombre, "actual": round(propios[nombre], 2), "mediana_pares": round(ref, 2),
                        "pares": {s: round(x, 2) for s, x in sorted(otros.items())}, "precio_implicito": round(p, 1)})
    if not detalle:
        return None
    return {"valor": round(median(d["precio_implicito"] for d in detalle), 1), "grupo": grupo, "multiplos": detalle}


# ---------------------------------------------------------------------------
# 3. Veredicto por consenso
# ---------------------------------------------------------------------------
INFRA, EN_PRECIO, SOBRE, MIXTO, NO_DET = ("infravalorada", "en_precio", "sobrevalorada", "senales_mixtas",
                                          "no_determinable")
# Margen exigido según la incertidumbre: más incertidumbre, más descuento antes de llamar algo barato o caro.
MARGEN_EXIGIDO = {"baja": 0.15, "media": 0.25, "alta": 0.35}
DISPERSION_BAJA = 1.35      # mayor / menor valor entre lentes
DISPERSION_MEDIA = 2.0


def veredicto_lente(valor, precio, margen: float) -> str:
    """infravalorada si el precio está al menos `margen` por debajo del valor; sobrevalorada si el precio
    supera el valor en al menos `margen` (simétrico en múltiplos: precio >= valor / (1 - margen))."""
    if valor is None or not precio or valor <= 0:
        return NO_DET
    if precio <= valor * (1 - margen):
        return INFRA
    if precio >= valor / (1 - margen):
        return SOBRE
    return EN_PRECIO


def incertidumbre(valores: list, nivel_evidencia: str | None, atraso_trimestres: int | None) -> tuple[str, list]:
    """(baja | media | alta, motivos). Parte de la dispersión entre lentes y sube un nivel por evidencia
    provisional y otro por resultados atrasados más de 2 trimestres. Con una sola lente es alta."""
    motivos = []
    positivos = [v for v in valores if v and v > 0]
    niveles = ["baja", "media", "alta"]
    if len(positivos) < 2:
        i = 2
        motivos.append("una sola lente con valor")
    else:
        disp = max(positivos) / min(positivos)
        i = 0 if disp <= DISPERSION_BAJA else 1 if disp <= DISPERSION_MEDIA else 2
        motivos.append(f"las lentes van de {min(positivos):,.0f} a {max(positivos):,.0f} ({disp:.2f}x)")
    if nivel_evidencia == "provisional":
        i += 1
        motivos.append("valor intrínseco con evidencia provisional")
    if atraso_trimestres and atraso_trimestres > 2:
        i += 1
        motivos.append(f"resultados con {atraso_trimestres} trimestres de atraso")
    return niveles[min(i, 2)], motivos


def consenso(lentes: dict, precio, nivel_evidencia=None, atraso_trimestres=None) -> dict:
    """Veredicto final. `lentes` = {"intrinseco": valor|None, "historia": valor|None, "pares": valor|None}.

    - Se necesitan al menos 2 lentes con valor; si no: no determinable.
    - Incertidumbre por dispersión y calidad del dato; fija el margen exigido.
    - Cada lente vota infravalorada / en precio / sobrevalorada con ese margen. Rige lo que digan al menos
      2 lentes; si no hay 2 que coincidan: señales mixtas.
    - Precio justo = mediana de las lentes; rango = menor y mayor lente."""
    con_valor = {k: v for k, v in lentes.items() if v is not None and v > 0}
    if not precio or len(con_valor) < 2:
        return {"veredicto": NO_DET, "lentes_con_valor": len(con_valor), "precio": precio,
                "motivo": "menos de 2 lentes con valor" if precio else "sin precio",
                "votos": {k: NO_DET for k in lentes}, "incertidumbre": None}
    nivel, motivos = incertidumbre(list(con_valor.values()), nivel_evidencia, atraso_trimestres)
    margen = MARGEN_EXIGIDO[nivel]
    votos = {k: (veredicto_lente(v, precio, margen) if k in con_valor else NO_DET) for k, v in lentes.items()}
    conteo = {}
    for v in votos.values():
        if v != NO_DET:
            conteo[v] = conteo.get(v, 0) + 1
    ganador = max(conteo, key=conteo.get)
    veredicto = ganador if conteo[ganador] >= 2 and list(conteo.values()).count(conteo[ganador]) == 1 else MIXTO
    justo = median(con_valor.values())
    return {
        "veredicto": veredicto, "votos": votos, "lentes_con_valor": len(con_valor),
        "incertidumbre": nivel, "motivos_incertidumbre": motivos, "margen_exigido_pct": round(margen * 100),
        "precio": precio, "precio_justo": round(justo, 1),
        "rango_justo": [round(min(con_valor.values()), 1), round(max(con_valor.values()), 1)],
        "margen_vs_justo_pct": round((justo - precio) / justo * 100, 1),
    }


# ---------------------------------------------------------------------------
# 4. Puntajes de calidad
# ---------------------------------------------------------------------------
def piotroski(actual: dict, previo: dict) -> dict:
    """Piotroski F con lo que trae la extracción anual (no financieros). Cada criterio es 1/0 o se omite
    si falta el dato; el puntaje se reporta como `puntaje / evaluados`. No se calcula liquidez corriente
    (la extracción no separa activo y pasivo corriente)."""
    def g(d, k):
        return d.get(k) if d else None

    def div(a, b):
        return a / b if a is not None and b else None

    crit = {}
    roa = div(g(actual, "utilidad_neta"), g(actual, "activos_totales"))
    roa0 = div(g(previo, "utilidad_neta"), g(previo, "activos_totales"))
    cfo = div(g(actual, "flujo_caja_operativo"), g(actual, "activos_totales"))
    if roa is not None:
        crit["roa_positivo"] = int(roa > 0)
    if cfo is not None:
        crit["flujo_operativo_positivo"] = int(cfo > 0)
    if roa is not None and roa0 is not None:
        crit["roa_mejora"] = int(roa > roa0)
    if roa is not None and cfo is not None:
        crit["flujo_mayor_que_utilidad"] = int(cfo > roa)
    lev, lev0 = div(g(actual, "deuda_financiera"), g(actual, "activos_totales")), div(g(previo, "deuda_financiera"), g(previo, "activos_totales"))
    if lev is not None and lev0 is not None:
        crit["apalancamiento_baja"] = int(lev <= lev0)
    acc, acc0 = g(actual, "acciones_en_circulacion"), g(previo, "acciones_en_circulacion")
    if acc and acc0:
        crit["sin_emision_de_acciones"] = int(acc <= acc0 * 1.005)
    mb, mb0 = div(g(actual, "utilidad_bruta"), g(actual, "ingresos")), div(g(previo, "utilidad_bruta"), g(previo, "ingresos"))
    if mb is not None and mb0 is not None:
        crit["margen_bruto_mejora"] = int(mb > mb0)
    rot, rot0 = div(g(actual, "ingresos"), g(actual, "activos_totales")), div(g(previo, "ingresos"), g(previo, "activos_totales"))
    if rot is not None and rot0 is not None:
        crit["rotacion_activos_mejora"] = int(rot > rot0)
    if len(crit) < 5:
        return {"puntaje": None, "evaluados": len(crit), "criterios": crit,
                "nota": "menos de 5 de los 8 criterios disponibles: no se reporta"}
    return {"puntaje": sum(crit.values()), "evaluados": len(crit), "criterios": crit,
            "lectura": "fuerte" if sum(crit.values()) / len(crit) >= 0.75 else
                       "débil" if sum(crit.values()) / len(crit) <= 0.375 else "media"}


NO_CALCULABLES = {
    "altman_z": "no calculable: la extracción no trae capital de trabajo ni utilidades retenidas",
    "beneish_m": "no calculable: la extracción no trae cuentas por cobrar ni gastos de administración y ventas",
}
