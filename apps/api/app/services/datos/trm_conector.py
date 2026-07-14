"""Conector de la TRM oficial (Banrep) vía el dataset público de datos.gov.co.

No requiere key. Verificado F0 (14-jul-2026): endpoint responde con
{valor, unidad, vigenciadesde, vigenciahasta} por día hábil cambiario.
"""

from datetime import date, datetime

import requests

from .base import FuenteDatos, PrecioDiario

_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"


class TrmConector(FuenteDatos):
    nombre = "datos_gov_co"

    def obtener_precios(self, ticker: str, desde: date, hasta: date) -> list[PrecioDiario]:
        # El dataset solo tiene una serie (la TRM); 'ticker' se ignora pero se
        # mantiene en la firma para cumplir la interfaz FuenteDatos.
        params = {
            "$where": f"vigenciadesde >= '{desde.isoformat()}' AND vigenciadesde <= '{hasta.isoformat()}'",
            "$order": "vigenciadesde ASC",
            "$limit": 5000,
        }
        resp = requests.get(_URL, params=params, timeout=20)
        resp.raise_for_status()
        datos = resp.json()
        precios = []
        for fila in datos:
            fecha = datetime.fromisoformat(fila["vigenciadesde"]).date()
            precios.append(PrecioDiario(fecha=fecha, cierre=float(fila["valor"])))
        return precios

    def disponible(self) -> bool:
        try:
            resp = requests.get(_URL, params={"$limit": 1}, timeout=15)
            return resp.status_code == 200 and len(resp.json()) == 1
        except Exception:
            return False
