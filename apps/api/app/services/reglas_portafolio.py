"""Reglas duras de portafolio (§3.4): "Corto plazo (<1 año): money market
COP, CDTs, SGOV/BIL. Nada de renta variable, sin excepción por perfil."

SGOV/BIL son ETFs de deuda del Tesoro ultra corta — se tratan como
equivalente de efectivo aunque su `clase` de mercado sea 'etf'. Money
market/CDT no tienen ticker de mercado (§5 del plan: tasas a mano, sin API
gratuita) — el usuario los registra con clase='renta_fija' o 'efectivo'.
"""

EXCEPCIONES_CORTO_PLAZO = {"SGOV", "BIL"}
CLASES_PERMITIDAS_CORTO_PLAZO = {"renta_fija", "efectivo", "fx"}


def validar_horizonte_corto(ticker: str, clase: str) -> None:
    """Lanza ValueError si el ticker/clase no es válido para horizonte 'corto'."""
    if ticker in EXCEPCIONES_CORTO_PLAZO:
        return
    if clase not in CLASES_PERMITIDAS_CORTO_PLAZO:
        raise ValueError(
            f"'{ticker}' (clase={clase}) no es válido para horizonte corto (<1 año): "
            "solo money market COP, CDTs, SGOV o BIL. Nada de renta variable, sin excepción por perfil."
        )
