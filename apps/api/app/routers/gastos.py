"""Registro manual de gastos + importación de extracto con conciliación
anti-duplicados (§3.2B.5)."""

import csv
import io
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth import UsuarioActual, cliente_supabase_de, get_current_usuario
from app.schemas.gastos import GastoManual
from app.services.conciliacion_gastos import conciliar

router = APIRouter(prefix="/gastos", tags=["gastos"])


@router.post("/manual")
async def registrar_gasto_manual(body: GastoManual, usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    fila = {"user_id": usuario.id, "origen": "manual", **body.model_dump()}
    resp = cliente.table("gastos").insert(fila).execute()
    return resp.data[0]


@router.get("")
async def mis_gastos(usuario: UsuarioActual = Depends(get_current_usuario)):
    cliente = cliente_supabase_de(usuario)
    resp = cliente.table("gastos").select("*").eq("user_id", usuario.id).order("fecha", desc=True).execute()
    return resp.data


@router.post("/importar-extracto")
async def importar_extracto(archivo: UploadFile, usuario: UsuarioActual = Depends(get_current_usuario)):
    """CSV con columnas: fecha (YYYY-MM-DD), monto, descripcion."""
    contenido = (await archivo.read()).decode("utf-8-sig")
    lector = csv.DictReader(io.StringIO(contenido))
    columnas_requeridas = {"fecha", "monto", "descripcion"}
    if lector.fieldnames is None or not columnas_requeridas.issubset(set(lector.fieldnames)):
        raise HTTPException(422, f"El CSV debe tener columnas {columnas_requeridas}")

    filas_extracto = []
    for fila in lector:
        try:
            filas_extracto.append(
                {
                    "fecha": datetime.strptime(fila["fecha"], "%Y-%m-%d").date(),
                    "monto": float(fila["monto"]),
                    "descripcion": fila["descripcion"],
                }
            )
        except (KeyError, ValueError):
            continue

    cliente = cliente_supabase_de(usuario)
    resp = (
        cliente.table("gastos")
        .select("id,fecha,monto")
        .eq("user_id", usuario.id)
        .eq("origen", "manual")
        .execute()
    )
    gastos_manuales = [
        {"id": g["id"], "fecha": datetime.strptime(g["fecha"], "%Y-%m-%d").date(), "monto": g["monto"]}
        for g in resp.data
    ]

    resultado = conciliar(gastos_manuales, filas_extracto)

    for fusion in resultado["fusiones"]:
        cliente.table("gastos").update(
            {"origen": "conciliado", "referencia_extracto": fusion["referencia_extracto"]}
        ).eq("id", fusion["gasto_id"]).eq("user_id", usuario.id).execute()

    nuevas_filas = [
        {
            "user_id": usuario.id,
            "fecha": n["fecha"].isoformat(),
            "monto": n["monto"],
            "categoria": "sin_clasificar",
            "descripcion": n["descripcion"],
            "origen": "importado",
            "referencia_extracto": n["descripcion"],
        }
        for n in resultado["nuevos"]
    ]
    if nuevas_filas:
        cliente.table("gastos").insert(nuevas_filas).execute()

    return {
        "fusionados": len(resultado["fusiones"]),
        "nuevos": len(nuevas_filas),
        "total_filas_procesadas": len(filas_extracto),
    }
