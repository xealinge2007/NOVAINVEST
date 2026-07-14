"""Salud del sistema (§8.8 del plan): última actualización por fuente,
consultable sin auth porque no expone datos personales de nadie.
"""

from fastapi import APIRouter, HTTPException

from app.database import cliente_servicio

router = APIRouter(prefix="/salud", tags=["salud"])


@router.get("/fuentes")
async def salud_fuentes():
    try:
        cliente = cliente_servicio()
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    resp = (
        cliente.table("salud_fuentes")
        .select("*")
        .order("fecha_verificacion", desc=True)
        .limit(20)
        .execute()
    )
    return resp.data
