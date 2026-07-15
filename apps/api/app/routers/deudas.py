"""Deudas y comparador de estrategias de pago (§3.2B.1)."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.deudas import ComparadorRequest, Deuda
from app.services.comparador_deudas import comparar_estrategias

router = APIRouter(prefix="/deudas", tags=["deudas"])


@router.post("")
async def crear_deuda(body: Deuda, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, **body.model_dump()}
    resp = cliente.table("deudas").insert(fila).execute()
    return resp.data[0]


@router.get("")
async def mis_deudas(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("deudas").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    return resp.data


@router.delete("/{deuda_id}")
async def eliminar_deuda(deuda_id: int, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    cliente.table("deudas").update({"activa": False}).eq("id", deuda_id).eq("user_id", usuario.id).execute()
    return {"status": "ok"}


@router.post("/comparar")
async def comparar(body: ComparadorRequest, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("deudas").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    if not resp.data:
        raise HTTPException(400, "No tienes deudas activas registradas")
    try:
        return comparar_estrategias(resp.data, body.extra_mensual)
    except ValueError as e:
        raise HTTPException(422, str(e))
