"""Análisis fundamental de los 20 emisores de la BVC (F4). Snapshot vigente
calculado por `jobs/analizador_fundamental.py` y guardado en
`fundamentales_analisis` — igual que `senales`, es un dato compartido entre
usuarios, no información personal, pero requiere auth como el resto de la app.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario

router = APIRouter(prefix="/fundamentales", tags=["fundamentales"])


@router.get("")
async def listar_fundamentales(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("fundamentales_analisis").select("*").order("ranking_estrella", desc=False, nullsfirst=False).execute()
    return resp.data


@router.get("/macro/supuestos")
async def supuestos_macro(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    return cliente.table("supuestos_macro").select("*").order("parametro").execute().data


@router.get("/{slug}")
async def detalle_fundamental(slug: str, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("fundamentales_analisis").select("*").eq("slug", slug).execute()
    if not resp.data:
        raise HTTPException(404, f"No hay análisis para {slug}")
    return resp.data[0]
