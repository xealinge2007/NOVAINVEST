"""Universo de activos (v3, §0B/§3.4/§11 F2b): tres cajones con reglas
distintas — 'bvc' (analizador completo), 'vehiculo_us' (ETF/subyacentes de
trading y opciones EEUU, sin análisis fundamental) y 'cripto'. La FX/TRM
queda sin cajón: es un dato de referencia para fricción cambiaria, no un
activo del universo de inversión.

BVC: verificado F0 que yfinance cubre los emisores locales con sufijo '.CL'
(ver NOTAS_F0.md). PFBCOLOM.CL quedó delistado tras la fusión/rebranding de
Grupo Bancolombia a Grupo Cibest (2025) — se reemplazó por CIBEST.CL.

Verificación F2b (01-sep-2026, contra yfinance): de los 15 emisores con PDF
en C:\\Proyectos\\BVC\\SIMEV_BVC, tienen preferencial con ticker propio y
líquido en Yahoo: Cibest/Bancolombia, Grupo Sura, Grupo Argos, Cementos
Argos y Corficolombiana (ordinaria + preferencial ambas negociadas); Grupo
Aval y Davivienda Group solo tienen líquida su preferencial (la ordinaria no
resuelve en Yahoo, se registra solo la preferencial). El resto (Ecopetrol,
ISA, Celsia, GEB, PEI, Constructora Conconcreto, Banco de Bogotá, Promigas)
son de clase única. No se asumió nada del plan: cada ticker de esta lista se
probó uno por uno.

Corrección al cerrar F3 (03-sep-2026): la primera pasada de F2b se saltó
`PFCORFICOL.CL` (Corficolombiana sí tiene preferencial propia, distinta en
precio de `CORFICOLCF.CL`) — se encontró auditando el volumen `.CL` contra
el "Más Negociadas" en vivo de bvc.com.co, que la mostraba entre las 5
especies más negociadas del día y reveló el hueco. Ver
`db/AUDITORIA_VOLUMEN_BVC.md`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefinicionActivo:
    ticker: str
    nombre: str
    clase: str  # accion | etf | indice_proxy | cripto | fx | renta_fija
    mercado: str
    moneda: str
    fuente_principal: str
    fuente_respaldo: str | None
    cajon: str | None  # bvc | vehiculo_us | cripto | renta_fija_cop | None (referencia, no invertible)


@dataclass(frozen=True)
class DefinicionEmisorBVC:
    slug: str  # coincide con el nombre de carpeta en C:\Proyectos\BVC\SIMEV_BVC
    nombre: str
    sector: str


@dataclass(frozen=True)
class DefinicionInstrumentoBVC:
    ticker: str  # debe existir en TICKERS_BVC
    emisor_slug: str  # debe existir en EMISORES_BVC
    clase: str  # ordinaria | preferencial | titulo_participativo | adr


TICKERS_US = [
    DefinicionActivo("AAPL", "Apple", "accion", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("MSFT", "Microsoft", "accion", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("GOOGL", "Alphabet", "accion", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("AMZN", "Amazon", "accion", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("NVDA", "Nvidia", "accion", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("VOO", "Vanguard S&P 500 ETF", "etf", "NYSE", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("VT", "Vanguard Total World Stock ETF", "etf", "NYSE", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("QQQ", "Invesco QQQ", "etf", "NASDAQ", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("SGOV", "iShares 0-3 Month Treasury Bond ETF", "etf", "NYSE", "USD", "yfinance", "stooq", "vehiculo_us"),
    DefinicionActivo("BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF", "etf", "NYSE", "USD", "yfinance", "stooq", "vehiculo_us"),
]

# Acciones BVC (§3.7/§3.8, analizador completo). Cada ticker con clase='accion'
# u 'indice_proxy' aquí es lo único que la app permite dar de alta como
# posición tipo 'accion' (F2b: el alta de acciones de otras bolsas se
# deshabilita — ver reglas_portafolio.validar_clase_accion_bvc).
TICKERS_BVC = [
    DefinicionActivo("ECOPETROL.CL", "Ecopetrol", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("CIBEST.CL", "Grupo Cibest (ex Bancolombia) — ordinaria", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFCIBEST.CL", "Grupo Cibest (ex Bancolombia) — preferencial", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("ISA.CL", "Interconexión Eléctrica (ISA)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("GRUPOSURA.CL", "Grupo Sura — ordinaria", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFGRUPSURA.CL", "Grupo Sura — preferencial", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("GRUPOARGOS.CL", "Grupo Argos — ordinaria", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFGRUPOARG.CL", "Grupo Argos — preferencial", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFAVAL.CL", "Grupo Aval — preferencial (sin ordinaria líquida en Yahoo)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("CEMARGOS.CL", "Cementos Argos — ordinaria", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFCEMARGOS.CL", "Cementos Argos — preferencial", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("CELSIA.CL", "Celsia", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("CORFICOLCF.CL", "Corficolombiana — ordinaria", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFCORFICOL.CL", "Corficolombiana — preferencial", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("GEB.CL", "Grupo Energía Bogotá (GEB)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PEI.CL", "PEI (vehículo inmobiliario, se maneja como acción)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PFDAVIGRP.CL", "Davivienda Group — preferencial (sin ordinaria líquida en Yahoo)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("CONCONCRET.CL", "Constructora Conconcreto", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("BOGOTA.CL", "Banco de Bogotá", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("PROMIGAS.CL", "Promigas", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    # Agregados el 09-sep-2026. Los cinco tenían estados financieros completos
    # en `fundamentales_reportados` —ROE, márgenes, patrimonio— pero ningún
    # instrumento dado de alta, así que el analizador no podía calcularles ni
    # capitalización ni múltiplos. Era un hueco del catálogo, no de los datos.
    # Los cinco tickers se verificaron contra yfinance antes de agregarlos:
    # devuelven serie diaria y cierre del día (MINEROS 19.840, TERPEL 18.680,
    # ETB 137, NUTRESA 316.000, BVC 16.340 al 09-sep-2026).
    DefinicionActivo("MINEROS.CL", "Mineros", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("TERPEL.CL", "Organización Terpel", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("ETB.CL", "Empresa de Telecomunicaciones de Bogotá (ETB)", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("NUTRESA.CL", "Grupo Nutresa", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("BVC.CL", "Bolsa de Valores de Colombia", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    # Agregados el 11-sep-2026 a pedido de Alex. A diferencia de los cinco de
    # arriba, estos CUATRO no tienen todavía estados financieros en
    # `fundamentales_reportados` — no hay corpus de XBRL/PDF descargado para
    # ellos en C:\Proyectos\BVC. Esto solo les da precio (vía yfinance) y
    # entrada en el catálogo; el analizador les calculará precio pero ningún
    # múltiplo hasta que se descarguen y procesen sus radicados ante la
    # Superfinanciera, igual que se hizo para los 20 originales. Tickers
    # verificados contra yfinance el 11-sep-2026 (EXITO 4.845, ENKA 19,30,
    # ELCONDOR 500, FABRICATO 5,00 COP).
    DefinicionActivo("EXITO.CL", "Almacenes Éxito", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("ENKA.CL", "Enka de Colombia", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("ELCONDOR.CL", "Construcciones El Cóndor", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("FABRICATO.CL", "Fabricato", "accion", "BVC", "COP", "yfinance", None, "bvc"),
    DefinicionActivo("ICOLCAP.CL", "iShares MSCI COLCAP (proxy del índice COLCAP)", "indice_proxy", "BVC", "COP", "yfinance", None, "bvc"),
]

CRIPTO = [
    DefinicionActivo("BTC-USD", "Bitcoin", "cripto", "CRIPTO", "USD", "yfinance", "coingecko", "cripto"),
]

FX = [
    DefinicionActivo("USDCOP", "TRM oficial (Banrep)", "fx", "FX", "COP", "datos_gov_co", None, None),
]

UNIVERSO_F0 = TICKERS_US + TICKERS_BVC + CRIPTO + FX

# Emisores BVC (§3.4, §5.1): slug = carpeta en C:\Proyectos\BVC\SIMEV_BVC.
# Una fila por empresa, dueña de la serie de fundamentales (F4a la llena).
EMISORES_BVC = [
    DefinicionEmisorBVC("ECOPETROL", "Ecopetrol", "petroleo_gas"),
    DefinicionEmisorBVC("GRUPO_CIBEST_BANCOLOMBIA", "Grupo Cibest (ex Bancolombia)", "banca"),
    DefinicionEmisorBVC("ISA", "Interconexión Eléctrica (ISA)", "energia_infraestructura"),
    DefinicionEmisorBVC("GRUPO_SURA", "Grupo Sura", "holding"),
    DefinicionEmisorBVC("GRUPO_ARGOS", "Grupo Argos", "holding_cemento"),
    DefinicionEmisorBVC("GRUPO_AVAL", "Grupo Aval", "banca"),
    DefinicionEmisorBVC("CEMENTOS_ARGOS", "Cementos Argos", "cemento_construccion"),
    DefinicionEmisorBVC("CELSIA", "Celsia", "energia_utilities"),
    DefinicionEmisorBVC("CORFICOLOMBIANA", "Corficolombiana", "holding_financiero"),
    DefinicionEmisorBVC("GEB", "Grupo Energía Bogotá", "energia_utilities"),
    DefinicionEmisorBVC("PEI", "PEI", "inmobiliario"),
    DefinicionEmisorBVC("DAVIVIENDA_GROUP", "Davivienda Group", "banca"),
    DefinicionEmisorBVC("CONSTRUCTORA_CONCONCRETO", "Constructora Conconcreto", "cemento_construccion"),
    DefinicionEmisorBVC("BANCO_DE_BOGOTA", "Banco de Bogotá", "banca"),
    DefinicionEmisorBVC("PROMIGAS", "Promigas", "energia_utilities"),
    # Agregados el 09-sep-2026. Ya existían en Supabase —`ingesta_simev` los
    # creó solos al encontrar sus carpetas de PDF— pero con
    # sector='sin_clasificar' y sin instrumento, así que no tenían precio y el
    # analizador les calculaba ROE y márgenes pero ningún múltiplo. Se les da
    # aquí su sector real y su ticker, y `seed_emisores_instrumentos.py` los
    # reconcilia por slug sin duplicar nada.
    DefinicionEmisorBVC("MINEROS", "Mineros", "mineria"),
    DefinicionEmisorBVC("TERPEL", "Organización Terpel", "petroleo_gas"),
    DefinicionEmisorBVC("ETB", "Empresa de Telecomunicaciones de Bogotá", "telecomunicaciones"),
    DefinicionEmisorBVC("GRUPO_NUTRESA", "Grupo Nutresa", "consumo"),
    DefinicionEmisorBVC("BVC", "Bolsa de Valores de Colombia", "infraestructura_mercado"),
    # Agregados el 11-sep-2026 a pedido de Alex — ver nota en TICKERS_BVC:
    # solo catálogo y precio, sin estados financieros todavía.
    DefinicionEmisorBVC("EXITO", "Almacenes Éxito", "consumo_retail"),
    DefinicionEmisorBVC("ENKA", "Enka de Colombia", "quimicos_petroquimica"),
    DefinicionEmisorBVC("EL_CONDOR", "Construcciones El Cóndor", "cemento_construccion"),
    DefinicionEmisorBVC("FABRICATO", "Fabricato", "textil"),
]

# Instrumentos BVC (§3.4): cada especie negociada, con su emisor y clase.
# ICOLCAP.CL NO entra aquí — es un proxy de índice, no una acción de un
# emisor. PEI entra como 'titulo_participativo' (se valora por NAV, §6) pero
# cuenta como 'accion' en `posiciones`/`activos` porque cotiza y se negocia
# igual que cualquier especie (decisión de Alex, §3.4).
INSTRUMENTOS_BVC = [
    DefinicionInstrumentoBVC("ECOPETROL.CL", "ECOPETROL", "ordinaria"),
    DefinicionInstrumentoBVC("CIBEST.CL", "GRUPO_CIBEST_BANCOLOMBIA", "ordinaria"),
    DefinicionInstrumentoBVC("PFCIBEST.CL", "GRUPO_CIBEST_BANCOLOMBIA", "preferencial"),
    DefinicionInstrumentoBVC("ISA.CL", "ISA", "ordinaria"),
    DefinicionInstrumentoBVC("GRUPOSURA.CL", "GRUPO_SURA", "ordinaria"),
    DefinicionInstrumentoBVC("PFGRUPSURA.CL", "GRUPO_SURA", "preferencial"),
    DefinicionInstrumentoBVC("GRUPOARGOS.CL", "GRUPO_ARGOS", "ordinaria"),
    DefinicionInstrumentoBVC("PFGRUPOARG.CL", "GRUPO_ARGOS", "preferencial"),
    DefinicionInstrumentoBVC("PFAVAL.CL", "GRUPO_AVAL", "preferencial"),
    DefinicionInstrumentoBVC("CEMARGOS.CL", "CEMENTOS_ARGOS", "ordinaria"),
    DefinicionInstrumentoBVC("PFCEMARGOS.CL", "CEMENTOS_ARGOS", "preferencial"),
    DefinicionInstrumentoBVC("CELSIA.CL", "CELSIA", "ordinaria"),
    DefinicionInstrumentoBVC("CORFICOLCF.CL", "CORFICOLOMBIANA", "ordinaria"),
    DefinicionInstrumentoBVC("PFCORFICOL.CL", "CORFICOLOMBIANA", "preferencial"),
    DefinicionInstrumentoBVC("GEB.CL", "GEB", "ordinaria"),
    DefinicionInstrumentoBVC("PEI.CL", "PEI", "titulo_participativo"),
    DefinicionInstrumentoBVC("PFDAVIGRP.CL", "DAVIVIENDA_GROUP", "preferencial"),
    DefinicionInstrumentoBVC("CONCONCRET.CL", "CONSTRUCTORA_CONCONCRETO", "ordinaria"),
    DefinicionInstrumentoBVC("BOGOTA.CL", "BANCO_DE_BOGOTA", "ordinaria"),
    DefinicionInstrumentoBVC("PROMIGAS.CL", "PROMIGAS", "ordinaria"),
    DefinicionInstrumentoBVC("MINEROS.CL", "MINEROS", "ordinaria"),
    DefinicionInstrumentoBVC("TERPEL.CL", "TERPEL", "ordinaria"),
    DefinicionInstrumentoBVC("ETB.CL", "ETB", "ordinaria"),
    DefinicionInstrumentoBVC("NUTRESA.CL", "GRUPO_NUTRESA", "ordinaria"),
    DefinicionInstrumentoBVC("BVC.CL", "BVC", "ordinaria"),
    DefinicionInstrumentoBVC("EXITO.CL", "EXITO", "ordinaria"),
    DefinicionInstrumentoBVC("ENKA.CL", "ENKA", "ordinaria"),
    DefinicionInstrumentoBVC("ELCONDOR.CL", "EL_CONDOR", "ordinaria"),
    DefinicionInstrumentoBVC("FABRICATO.CL", "FABRICATO", "ordinaria"),
]

# Tickers válidos para dar de alta una posición clase='accion' (F2b: el alta
# de acciones fuera de la BVC se deshabilita). Se deriva de INSTRUMENTOS_BVC,
# no se mantiene a mano aparte.
TICKERS_BVC_VALIDOS: frozenset[str] = frozenset(i.ticker for i in INSTRUMENTOS_BVC)

# ticker -> emisor_slug, para agrupar "misma empresa" en la alerta de
# concentración del portafolio (§3.4: ordinaria + preferencial cuentan como
# una sola posición).
MAPA_TICKER_A_EMISOR_SLUG: dict[str, str] = {i.ticker: i.emisor_slug for i in INSTRUMENTOS_BVC}

# ticker -> clase de activo, para inferir la clase de un ticker importado de
# un extracto de broker (§8B.1) sin adivinar a ciegas.
MAPA_TICKER_CLASE: dict[str, str] = {a.ticker: a.clase for a in UNIVERSO_F0}


def inferir_clase_ticker(ticker: str) -> str:
    """Clase de un ticker según el universo conocido; si no se conoce, se
    asume 'accion' (comportamiento previo) y queda sujeto a
    validar_clase_accion_bvc — un ticker desconocido importado de un broker
    casi siempre es una acción individual fuera de la BVC."""
    return MAPA_TICKER_CLASE.get(ticker, "accion")


def timeframes_validos(activo: DefinicionActivo) -> list[str]:
    """§3.5 (F3, regla dura): la BVC opera solo diario/semanal — no hay dato
    intradía gratuito confiable y la liquidez local no soporta 4h. NY y
    cripto (cajón vehiculo_us/cripto) sí operan en 4h y 1D."""
    if activo.cajon == "bvc":
        return ["1d"]
    return ["4h", "1d"]
