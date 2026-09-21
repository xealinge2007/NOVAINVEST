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


@router.get("/{slug}/perfil")
async def perfil_cualitativo(slug: str, usuario: UsuarioActual = Depends(get_current_usuario)):
    """Descripción, CEO, noticias de impacto y situación micro/macro (F4q).
    404 cuando el emisor todavía no tiene ficha investigada -- el frontend lo
    trata como "aún no disponible", no como error."""
    cliente = cliente_supabase_de(usuario)
    emisor = cliente.table("emisores").select("id").eq("slug", slug).execute().data
    if not emisor:
        raise HTTPException(404, f"No existe el emisor {slug}")
    resp = cliente.table("perfil_cualitativo_emisor").select("*").eq("emisor_id", emisor[0]["id"]).execute().data
    if not resp:
        raise HTTPException(404, f"Todavía no hay perfil cualitativo para {slug}")
    return resp[0]


@router.get("/{slug}/evolucion")
async def evolucion_fundamental(slug: str, usuario: UsuarioActual = Depends(get_current_usuario)):
    """Serie histórica (TTM en cada punto) vs. precio, contemporáneo y con
    rezago de 45 días, más correlación/efectividad direccional y bandas de
    valoración por percentil histórico -- F4n. Márgenes y EV/EBITDA salen en
    None para bancos/holdings financieros (P/E y P/VL sí aplican para ellos)."""
    cliente = cliente_supabase_de(usuario)
    emisor = cliente.table("emisores").select("id").eq("slug", slug).execute().data
    if not emisor:
        raise HTTPException(404, f"No existe el emisor {slug}")
    emisor_id = emisor[0]["id"]
    serie = cliente.table("evolucion_fundamental_serie").select("*").eq(
        "emisor_id", emisor_id).order("fecha_cierre").execute().data
    estadisticas = cliente.table("evolucion_fundamental_estadisticas").select("*").eq(
        "emisor_id", emisor_id).execute().data
    percentiles = cliente.table("valoracion_percentiles").select("*").eq(
        "emisor_id", emisor_id).execute().data
    if not serie:
        raise HTTPException(404, f"No hay evolución calculada para {slug} -- sin datos suficientes")
    return {"serie": serie, "estadisticas": estadisticas, "percentiles": percentiles}
