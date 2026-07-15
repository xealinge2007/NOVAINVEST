"""Importación de extractos de broker: IBKR Flex XML o CSV genérico (§8B.1)."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.services.importar_broker import parse_csv_generico, parse_ibkr_flex_xml, reconciliar_contra_posiciones

router = APIRouter(prefix="/portafolio/importar-broker", tags=["portafolio"])


@router.post("")
async def importar(archivo: UploadFile, usuario: UsuarioActual = Depends(get_current_usuario)):
    contenido = (await archivo.read()).decode("utf-8-sig")
    nombre = (archivo.filename or "").lower()

    try:
        if nombre.endswith(".xml") or contenido.lstrip().startswith("<"):
            importadas = parse_ibkr_flex_xml(contenido)
        else:
            importadas = parse_csv_generico(contenido)
    except ValueError as e:
        raise HTTPException(422, str(e))

    if not importadas:
        raise HTTPException(422, "No se encontraron posiciones válidas en el archivo")

    cliente = cliente_supabase_de(usuario)
    existentes_resp = cliente.table("posiciones").select("*").eq("user_id", usuario.id).eq("activa", True).execute()
    reporte = reconciliar_contra_posiciones(importadas, existentes_resp.data)

    aplicadas = []
    rechazadas = []
    for pos in importadas:
        clase = "accion"  # el extracto no trae la clase -- se asume accion/etf listado; el usuario la ajusta luego
        try:
            fila = {
                "user_id": usuario.id,
                "ticker": pos["ticker"],
                "clase": clase,
                "cantidad": pos["cantidad"],
                "precio_promedio_compra": pos["precio_promedio_compra"],
                "moneda_compra": pos["moneda_compra"] if pos["moneda_compra"] in ("COP", "USD") else "USD",
                "cuenta": pos["cuenta"],
                "horizonte": "largo",
                "origen": "importado",
            }
            cliente.table("posiciones").upsert(fila, on_conflict="user_id,ticker,cuenta").execute()
            aplicadas.append(pos["ticker"])
        except Exception as e:
            rechazadas.append({"ticker": pos["ticker"], "error": str(e)})

    return {
        "aplicadas": aplicadas,
        "rechazadas": rechazadas,
        "diferencias_vs_digitado": reporte["diferencias"],
        "total_procesadas": len(importadas),
    }
