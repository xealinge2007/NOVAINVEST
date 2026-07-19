"""Filtro de noticias de alto impacto (§3.5, novedad v2): cuarentena si hay
earnings del activo o evento macro mayor (Fed/FOMC, CPI, empleo) en las
próximas 48h. Lógica pura — recibe las fechas de earnings y los eventos
macro ya consultados (por el router/job), no hace I/O, para poder probarse
con `python -c` sin red ni Supabase.
"""

from datetime import date, datetime, timedelta

HORAS_CUARENTENA = 48


def _dentro_de_ventana(fecha_evento: date, fecha_referencia: datetime, horas: int) -> bool:
    """Compara a granularidad de día (las fuentes gratuitas de calendario no
    garantizan la hora exacta): el evento cuenta si su fecha cae entre hoy y
    `horas` adelante, redondeando hacia arriba (48h → hasta 2 días adelante).
    También cuenta el día de hoy, por si el evento ya se publicó pero el
    mercado todavía no terminó de reaccionar.
    """
    hoy = fecha_referencia.date()
    dias_ventana = -(-horas // 24)  # ceil(horas / 24) sin importar float
    return hoy <= fecha_evento <= hoy + timedelta(days=dias_ventana)


def evaluar_cuarentena(
    fecha_referencia: datetime,
    earnings_proximos: list[date],
    eventos_macro: list[dict],
    horas: int = HORAS_CUARENTENA,
) -> dict:
    """`eventos_macro` es una lista de dicts con al menos `fecha` (date) y
    `tipo`/`descripcion`. Devuelve en_cuarentena=True con el primer motivo
    encontrado (earnings tiene prioridad en el mensaje si coinciden ambos).
    """
    for fecha_earning in earnings_proximos:
        if _dentro_de_ventana(fecha_earning, fecha_referencia, horas):
            return {
                "en_cuarentena": True,
                "motivo": f"earnings el {fecha_earning.isoformat()} (dentro de {horas}h)",
            }

    for evento in eventos_macro:
        fecha_evento = evento["fecha"]
        if isinstance(fecha_evento, str):
            fecha_evento = date.fromisoformat(fecha_evento)
        if _dentro_de_ventana(fecha_evento, fecha_referencia, horas):
            return {
                "en_cuarentena": True,
                "motivo": f"evento macro {evento.get('tipo', 'otro')} el {fecha_evento.isoformat()}: {evento.get('descripcion', '')}",
            }

    return {"en_cuarentena": False, "motivo": None}
