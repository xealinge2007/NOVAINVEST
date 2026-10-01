# -*- coding: utf-8 -*-
"""Pilar 3 del Motor de Valor (Greenblatt): ¿tiene el emisor un catalizador vivo?

Logica pura, sin base de datos (la lee `jobs/catalizadores.py`). Es una PUERTA de
tamaño de posicion, no un desempate (plan §2.2): en Colombia el descuento se cierra
por decision del controlante, asi que un evento solo cuenta si sigue vivo y si el
controlante no tiene historial en contra del minoritario (plan §5B).

Criterio documentado, no medido (mismo espiritu que el piso de liquidez de F3); los
dos umbrales son constantes para poder ajustarlos cuando W6 los valide:

- vivo  = estado 'anunciado' o 'en_curso', anunciado hace <= VENTANA_VIGENCIA_DIAS
          y sin `fecha_evento` ya vencida (un evento que debio ocurrir y no figura
          completado no cuenta como vivo).
- fuerte = vivo y `favorece_minoritario` no es False.
- debil  = vivo pero el controlante figura como `favorece_minoritario = False`.
"""

from datetime import date, timedelta

VENTANA_VIGENCIA_DIAS = 548  # ~18 meses: el plan pide el catalizador de los proximos 12
ESTADOS_VIVOS = ("anunciado", "en_curso")


def _fecha(valor):
    if valor is None or isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def evaluar_catalizadores(eventos: list[dict], hoy: date | None = None) -> dict:
    """Devuelve {'tiene_catalizador_vivo': bool, 'nivel': 'fuerte'|'debil'|'ninguno',
    'motivo': str, 'eventos_vivos': [id o indice]} a partir de filas de `catalizadores`."""
    hoy = hoy or date.today()
    limite = hoy - timedelta(days=VENTANA_VIGENCIA_DIAS)
    vivos = []
    for i, e in enumerate(eventos):
        if e.get("estado") not in ESTADOS_VIVOS:
            continue
        anuncio = _fecha(e.get("fecha_anuncio"))
        if anuncio is None or anuncio < limite:
            continue
        previsto = _fecha(e.get("fecha_evento"))
        if previsto is not None and previsto < hoy:
            continue
        vivos.append((e.get("id", i), e))

    if not vivos:
        return {"tiene_catalizador_vivo": False, "nivel": "ninguno",
                "motivo": "sin eventos anunciados/en curso dentro de la ventana de vigencia",
                "eventos_vivos": []}

    ids = [v[0] for v in vivos]
    if any(e.get("favorece_minoritario") is not False for _, e in vivos):
        return {"tiene_catalizador_vivo": True, "nivel": "fuerte",
                "motivo": f"{len(vivos)} evento(s) vivo(s)", "eventos_vivos": ids}
    return {"tiene_catalizador_vivo": True, "nivel": "debil",
            "motivo": "evento(s) vivo(s) pero el controlante figura como no favorable al minoritario",
            "eventos_vivos": ids}


TIPOS_EVENTO = ("escision", "opa", "recompra", "venta_activo", "cambio_control",
                "deslistamiento", "fusion", "recapitalizacion", "otro")
ESTADOS = ("anunciado", "en_curso", "completado", "fallido")


def validar_evento(fila: dict) -> list[str]:
    """Errores de una fila del CSV de catalizadores (lista vacia = valida).

    Exige fuente: un catalizador sin fuente no se carga, como el resto de cifras
    del proyecto (declarar el hueco, no inventar el dato)."""
    errores = []
    if not (fila.get("emisor_slug") or "").strip():
        errores.append("falta emisor_slug")
    if fila.get("tipo_evento") not in TIPOS_EVENTO:
        errores.append(f"tipo_evento invalido: {fila.get('tipo_evento')!r}")
    if (fila.get("estado") or "anunciado") not in ESTADOS:
        errores.append(f"estado invalido: {fila.get('estado')!r}")
    for campo in ("fecha_anuncio", "fecha_evento"):
        valor = (fila.get(campo) or "").strip()
        if valor:
            try:
                date.fromisoformat(valor)
            except ValueError:
                errores.append(f"{campo} no es AAAA-MM-DD: {valor!r}")
        elif campo == "fecha_anuncio":
            errores.append("falta fecha_anuncio")
    if not (fila.get("descripcion") or "").strip():
        errores.append("falta descripcion")
    if not (fila.get("fuente") or "").strip():
        errores.append("falta fuente (sin fuente no se carga)")
    return errores
