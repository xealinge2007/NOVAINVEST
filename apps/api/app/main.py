"""Punto de entrada de la API FastAPI — NOVAINVEST."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import salud

app = FastAPI(
    title="NOVAINVEST API",
    description="Asesor financiero personal multi-usuario — herramienta analítica, no ejecuta operaciones.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salud.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
