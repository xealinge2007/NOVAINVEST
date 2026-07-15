"""Fichas de ETF (§3 módulo 3 del curso IDI, §3.4 del plan): TER y top-10
holdings. No hay API gratuita confiable de holdings completos — dataset
curado a mano desde los fact sheets públicos de cada gestora (Vanguard,
Invesco, iShares, SPDR), snapshot al 14-jul-2026. Los pesos reales cambian
día a día; esto es una referencia razonable, no un dato en tiempo real
(mismo criterio de honestidad que con la cobertura BVC en F0).
"""

FICHAS_ETF = {
    "VOO": {
        "nombre": "Vanguard S&P 500 ETF",
        "ter_pct": 0.03,
        "fecha_referencia": "2026-07-14",
        "top_holdings": {
            "AAPL": 7.1, "MSFT": 6.8, "NVDA": 6.5, "AMZN": 3.8, "META": 2.6,
            "GOOGL": 2.1, "AVGO": 2.0, "TSLA": 1.9, "BRK.B": 1.7, "JPM": 1.3,
        },
    },
    "VT": {
        "nombre": "Vanguard Total World Stock ETF",
        "ter_pct": 0.07,
        "fecha_referencia": "2026-07-14",
        "top_holdings": {
            "AAPL": 4.2, "MSFT": 4.0, "NVDA": 3.8, "AMZN": 2.2, "META": 1.5,
            "GOOGL": 1.3, "AVGO": 1.1, "TSLA": 1.1, "TSM": 0.9, "JPM": 0.8,
        },
    },
    "QQQ": {
        "nombre": "Invesco QQQ Trust (Nasdaq-100)",
        "ter_pct": 0.20,
        "fecha_referencia": "2026-07-14",
        "top_holdings": {
            "AAPL": 8.9, "MSFT": 8.3, "NVDA": 7.9, "AMZN": 5.1, "AVGO": 4.4,
            "META": 3.6, "GOOGL": 2.8, "TSLA": 2.5, "COST": 2.2, "NFLX": 2.0,
        },
    },
    "SGOV": {
        "nombre": "iShares 0-3 Month Treasury Bond ETF",
        "ter_pct": 0.09,
        "fecha_referencia": "2026-07-14",
        "top_holdings": {},  # letras del Tesoro EEUU, no acciones -- no hay solapamiento con equity ETFs
    },
    "BIL": {
        "nombre": "SPDR Bloomberg 1-3 Month T-Bill ETF",
        "ter_pct": 0.1354,
        "fecha_referencia": "2026-07-14",
        "top_holdings": {},
    },
}


def calcular_solapamiento(ticker_a: str, ticker_b: str) -> dict:
    if ticker_a not in FICHAS_ETF or ticker_b not in FICHAS_ETF:
        raise ValueError(f"Ficha no disponible para {ticker_a} o {ticker_b}")

    holdings_a = FICHAS_ETF[ticker_a]["top_holdings"]
    holdings_b = FICHAS_ETF[ticker_b]["top_holdings"]
    comunes = sorted(set(holdings_a) & set(holdings_b))

    solapamiento_pct = sum(min(holdings_a[t], holdings_b[t]) for t in comunes)

    return {
        "ticker_a": ticker_a,
        "ticker_b": ticker_b,
        "holdings_comunes": comunes,
        "cantidad_comunes": len(comunes),
        "solapamiento_pct_estimado": round(solapamiento_pct, 2),
        "nota": "Estimado sobre el top-10 de cada fondo (no el fondo completo); ver fecha_referencia de cada ficha.",
    }
