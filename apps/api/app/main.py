"""Punto de entrada de la API FastAPI — NOVAINVEST."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import (
    cuenta,
    deudas,
    etf,
    finanzas,
    gastos,
    importar_broker,
    objetivos,
    perfil,
    portafolio,
    rebalanceo,
    salud,
)

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="NOVAINVEST API",
    description="Asesor financiero personal multi-usuario — herramienta analítica, no ejecuta operaciones.",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salud.router)
app.include_router(perfil.router)
app.include_router(finanzas.router)
app.include_router(deudas.router)
app.include_router(gastos.router)
app.include_router(cuenta.router)
app.include_router(objetivos.router)
app.include_router(portafolio.router)
app.include_router(rebalanceo.router)
app.include_router(etf.router)
app.include_router(importar_broker.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
