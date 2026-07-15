"""Fichas de ETF y solapamiento (§3.4, módulo 3 del curso IDI). Lectura
pública — no expone datos personales, no requiere autenticación."""

from fastapi import APIRouter, HTTPException

from app.services.datos_etf import FICHAS_ETF, calcular_solapamiento

router = APIRouter(prefix="/etf", tags=["etf"])


@router.get("/{ticker}")
async def ficha(ticker: str):
    ticker = ticker.upper()
    if ticker not in FICHAS_ETF:
        raise HTTPException(404, f"No hay ficha para {ticker}")
    return {"ticker": ticker, **FICHAS_ETF[ticker]}


@router.get("/solapamiento/{ticker_a}/{ticker_b}")
async def solapamiento(ticker_a: str, ticker_b: str):
    try:
        return calcular_solapamiento(ticker_a.upper(), ticker_b.upper())
    except ValueError as e:
        raise HTTPException(404, str(e))
