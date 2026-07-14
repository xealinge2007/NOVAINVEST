"""Universo de activos del criterio de aceptación F0:
3 años de 10 tickers US + 5 BVC (o ADRs) + BTC + TRM.

BVC: verificado F0 que yfinance cubre los emisores locales con sufijo '.CL'
(ver NOTAS_F0.md). PFBCOLOM.CL quedó delistado tras la fusión/rebranding de
Grupo Bancolombia a Grupo Cibest (2025) — se reemplazó por CIBEST.CL.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefinicionActivo:
    ticker: str
    nombre: str
    clase: str  # accion | etf | indice_proxy | cripto | fx
    mercado: str
    moneda: str
    fuente_principal: str
    fuente_respaldo: str | None


TICKERS_US = [
    DefinicionActivo("AAPL", "Apple", "accion", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("MSFT", "Microsoft", "accion", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("GOOGL", "Alphabet", "accion", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("AMZN", "Amazon", "accion", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("NVDA", "Nvidia", "accion", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("VOO", "Vanguard S&P 500 ETF", "etf", "NYSE", "USD", "yfinance", "stooq"),
    DefinicionActivo("VT", "Vanguard Total World Stock ETF", "etf", "NYSE", "USD", "yfinance", "stooq"),
    DefinicionActivo("QQQ", "Invesco QQQ", "etf", "NASDAQ", "USD", "yfinance", "stooq"),
    DefinicionActivo("SGOV", "iShares 0-3 Month Treasury Bond ETF", "etf", "NYSE", "USD", "yfinance", "stooq"),
    DefinicionActivo("BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF", "etf", "NYSE", "USD", "yfinance", "stooq"),
]

TICKERS_BVC = [
    DefinicionActivo("ECOPETROL.CL", "Ecopetrol", "accion", "BVC", "COP", "yfinance", None),
    DefinicionActivo("CIBEST.CL", "Grupo Cibest (ex Bancolombia)", "accion", "BVC", "COP", "yfinance", None),
    DefinicionActivo("ISA.CL", "Interconexión Eléctrica (ISA)", "accion", "BVC", "COP", "yfinance", None),
    DefinicionActivo("GRUPOARGOS.CL", "Grupo Argos", "accion", "BVC", "COP", "yfinance", None),
    DefinicionActivo("PFAVAL.CL", "Grupo Aval (pref)", "accion", "BVC", "COP", "yfinance", None),
    DefinicionActivo("ICOLCAP.CL", "iShares MSCI COLCAP (proxy del índice COLCAP)", "indice_proxy", "BVC", "COP", "yfinance", None),
]

CRIPTO = [
    DefinicionActivo("BTC-USD", "Bitcoin", "cripto", "CRIPTO", "USD", "yfinance", "coingecko"),
]

FX = [
    DefinicionActivo("USDCOP", "TRM oficial (Banrep)", "fx", "FX", "COP", "datos_gov_co", None),
]

UNIVERSO_F0 = TICKERS_US + TICKERS_BVC + CRIPTO + FX
