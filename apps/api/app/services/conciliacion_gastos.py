"""Conciliación anti-duplicados entre gastos manuales y el extracto importado
(§3.2B.5): mismo monto ± 1 día se propone como fusión — el manual cubre
efectivo, el extracto cubre lo demás, nada se digita dos veces.
"""

from datetime import date, timedelta


def conciliar(gastos_manuales: list[dict], filas_extracto: list[dict]) -> dict:
    """gastos_manuales: [{id, fecha: date, monto}], ya filtrados a origen='manual'.
    filas_extracto: [{fecha: date, monto, descripcion}].
    Devuelve {fusiones: [{gasto_id, referencia_extracto}], nuevos: [fila, ...]}.
    """
    disponibles = list(gastos_manuales)
    fusiones = []
    nuevos = []

    for fila in filas_extracto:
        match = next(
            (
                g
                for g in disponibles
                if g["monto"] == fila["monto"] and abs((g["fecha"] - fila["fecha"]).days) <= 1
            ),
            None,
        )
        if match:
            disponibles.remove(match)
            fusiones.append({"gasto_id": match["id"], "referencia_extracto": fila.get("descripcion", "")})
        else:
            nuevos.append(fila)

    return {"fusiones": fusiones, "nuevos": nuevos}
