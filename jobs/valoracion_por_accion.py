# -*- coding: utf-8 -*-
"""Valor por acción de cada emisor no-holding (P2 de la auditoría 01-oct-2026).

Reemplaza las constantes escritas a mano de `epv_engine.py`: TODO sale de la base de datos
(`fundamentales_reportados`, `fundamentales_analisis`, `emisores`) y se escribe en
`valor_estimado`, así que se recalcula solo cuando cambia un precio o un trimestre.

Rutas por arquetipo (la matemática vive en `app/services/valoracion.py`):
  - real                  -> EPV (Greenwald) a valor del patrimonio, con rango, sensibilidad y
                             crecimiento implícito en el precio (DCF inverso).
  - banco                 -> P/VL justificado = (ROE - g) / (Ke - g).
  - vehiculo_inmobiliario -> NAV por título (libro a valor razonable, NIC 40).
  - holding               -> `valor_engine.py` (suma de partes).
  - infraestructura_mercado (BVC) -> no determinable: activos de terceros en el balance.

Salida por emisor: valor del patrimonio bajo/central/alto, por acción, contra el precio. El
rango es de ESCENARIOS (no percentiles estadísticos): ver `valoracion.escenarios_*`.

Uso: python jobs/valoracion_por_accion.py [--emisor SLUG] [--dry-run]
"""

import argparse
import io
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))
sys.path.insert(0, str(RAIZ / "jobs"))

from app.services import valoracion as v  # noqa: E402
from analizador_fundamental import ACCIONES_PREFERENCIALES  # noqa: E402
from compat_esquema import upsert_valor_estimado  # noqa: E402

ORDEN = {"T1": 1, "T2": 2, "T3": 3, "T4": 4, "ANUAL": 5}
FIN_PERIODO = {"T1": "03-31", "T2": "06-30", "T3": "09-30", "T4": "12-31", "ANUAL": "12-31"}
RUTA_DB = {"real": "activos_epv", "banco": "banco", "vehiculo_inmobiliario": "inmobiliario"}
FACTOR_NAV_INMOBILIARIO = (0.90, 1.00, 1.00)

# Datos operativos de vehículos inmobiliarios para la sensibilidad del NAV (curados, con fuente). PEI,
# 2T-2026: NOI e ingresos del trimestre (se anualizan x4: el 2T ya refleja la venta del 51 % de Plaza
# Central), vacancia económica de la teleconferencia. Los inmuebles (propiedad de inversión) se estiman con
# la participación que tuvieron en el activo total en el 1T-2026 (10.090,865 / 10.307,115 = 97,9 %).
DATOS_OPERATIVOS = {
    "PEI": {
        "noi_trimestre": 172.844, "ingresos_trimestre": 205.778, "vacancia_economica_pct": 7.25,
        "vacancia_fisica_pct": 6.72, "participacion_inmuebles_en_activos": 10090.865 / 10307.115,
        "fuente": "Informe 2T-2026 del Representante Legal (Fiducoldex) y Valora Analitik 6-ago-2026; "
                  "propiedad de inversión y activo total del 1T-2026 (informe del Representante Legal)",
        # EEFF condensados al 30-jun-2026 (pei.com.co), nota 12: tramos de deuda (capital en miles de millones y tasa
        # efectiva anual ponderada); EBITDA del 2T del informe del Representante Legal (Fiducoldex), p. 10.
        "tramos_deuda": [(170.894306, 13.05), (1743.853844, 12.92), (761.223030, 9.26)], "ebitda_trimestre": 141.414,
        "avisos": [
            "deuda 2.676 de capital (2.709 con intereses), SIN covenants financieros (solo pagarés), tasa promedio ponderada 11,89 % "
            "(bancaria 12,9-13,1 %; bonos IPC+3,8-4,3 % y 7,28 %); deuda / EBITDA 4,73x y cobertura EBITDA / interés 1,78x. "
            "Vencimientos contractuales: 203,9 en 1 año, 1.393,7 entre 1 y 5 años y 1.111,3 a más de 5 años (nota 12). Esa tabla ubica "
            "todo el capital de bonos (761) a más de 5 años, pero las series C10 (28-ago-2028, 209,4) y A10 (7-nov-2029, 226,0) vencen "
            "en menos de 5: leyéndolas así, ~2.033 (75 %) vence en 5 años",
            "costo de la deuda 11,9 % contra rendimiento del NOI sobre libros de 6,96 %: el apalancamiento resta a los libros (solo es neutro "
            "al cap rate de 11,66 % que descuenta el precio)",
            "compromisos de ingresos por arrendamientos ya firmados: 2.979 (643,7 en 1 año; 1.293,9 entre 1 y 5; 1.041,7 a más de 5 años); "
            "sin contingencias registradas; capex del 1S-26: mejoras 39,2 + adquisiciones 1,9 + equipo 1,4 = 42,5 (flujo de caja)",
            "sin impuesto de renta ni impuestos diferidos en los estados del vehículo (solo predial como gasto): no hay impuestos latentes "
            "registrados a nivel de PEI; la tributación del rendimiento recae en el inversionista (a confirmar con el prospecto)",
            "composición de la propiedad de inversión (2T-2026): 38,0 % centros comerciales, 35,4 % corporativo, 17,0 % logístico, "
            "6,7 % especializado, 2,9 % locales; ~1.495 arrendatarios y GLA 1.115.144 m2. NO se publica concentración por activo "
            "ni por arrendatario en los documentos oficiales leídos",
            "calificación i AAA (BRC, 21-may-2026); duración promedio de contratos bajó a 4 años en 2025 desde 5 en 2022 (BRC)",
            "EVENTO PENDIENTE no incluido en el NAV ni en el conteo de títulos: compra del portafolio de Terranum (contrato del "
            "9-jul-2026, precio COP 2.181.025 millones sujeto al ajuste por el valor de los títulos a NAV que se emitan al vendedor; "
            "cinco activos corporativos y logísticos, > 375.000 m2, NOI > 200.000 millones). Parte del pago va a una entidad vinculada "
            "a los accionistas de la administradora (transacción con parte vinculada). La asamblea del 22-sep-2026 aprobó el pago en "
            "especie y renunciar al derecho de preferencia con 70,76 % de los títulos; sigue sujeta a autoridades de competencia y "
            "regulatorias. Cambiará el NAV y el número de títulos",
        ],
    },
}  # el libro ya es valor razonable: sin potencial por encima


def _entidad_regulatoria(slug):
    """Texto `entidad_medida` de db/semillas/bancos_regulatorio.csv del último período del emisor (None si no está)."""
    import csv
    ruta = RAIZ / "db" / "semillas" / "bancos_regulatorio.csv"
    if not ruta.is_file():
        return None
    filas = [f for f in csv.DictReader(ruta.open(encoding="utf-8")) if f["emisor_slug"] == slug]
    return max(filas, key=lambda r: r["periodo"])["entidad_medida"] if filas else None


def _r(x, d=1):
    return None if x is None else round(x, d)


def _ultimo_periodo(cliente, emisor_id):
    filas = (cliente.table("fundamentales_reportados").select("anio,periodo").eq("emisor_id", emisor_id)
             .not_.is_("activos_totales", "null").execute().data)
    if not filas:
        return None, None
    m = max(filas, key=lambda f: (f["anio"], ORDEN.get(f["periodo"], 0)))
    return m["anio"], m["periodo"]


def _anuales(cliente, emisor_id, campos):
    """{año: fila} de los ANUAL del emisor."""
    filas = (cliente.table("fundamentales_reportados").select("anio," + ",".join(campos))
             .eq("emisor_id", emisor_id).eq("periodo", "ANUAL").order("anio").execute().data)
    return {f["anio"]: f for f in filas}


def no_determinable(motivo):
    return {"determinable": False, "motivo_no_determinable": motivo, "confianza": "baja"}


def valorar_real(cliente, em, a, acciones_total):
    if em["slug"] in v.NO_DETERMINABLE_POR_METODO:
        return no_determinable(v.NO_DETERMINABLE_POR_METODO[em["slug"]])
    con_asociadas = em["slug"] in v.EMISORES_CON_ASOCIADAS
    minoritario_mercado = em["slug"] in v.EMISORES_MINORITARIO_A_MERCADO
    try:
        anuales = _anuales(cliente, em["id"], ["utilidad_operacional", "ingresos"] + (["resultado_asociadas"] if con_asociadas else [])
                           + (["utilidad_minoritarios"] if minoritario_mercado else []))
    except Exception:  # columna sin migrar (db/migrate_p4_resultado_asociadas.sql, migrate_p5_utilidad_minoritarios.sql)
        return no_determinable("falta aplicar db/migrate_p4_resultado_asociadas.sql o db/migrate_p5_utilidad_minoritarios.sql "
                               "y recargar el XBRL: el EPV de este emisor necesita esos rubros")
    ebit = {y: f["utilidad_operacional"] for y, f in anuales.items() if f.get("utilidad_operacional") is not None}
    asociadas = {}
    if con_asociadas:
        # Solo años con ambos rubros: mezclar años con y sin asociadas arma una serie incomparable.
        asociadas = {y: anuales[y]["resultado_asociadas"] for y in ebit if anuales[y].get("resultado_asociadas") is not None}
        ebit = {y: v.ebit_equivalente(x, asociadas[y]) for y, x in ebit.items() if y in asociadas}
    ebit = {y: x for y, x in ebit.items() if y >= max(ebit, default=0) - 6}
    desde = v.PERIMETRO_DESDE.get(em["slug"])
    if desde:
        ebit = {y: x for y, x in ebit.items() if y >= desde}
    if len(ebit) < v.ANIOS_MINIMOS_EBIT:
        return no_determinable(f"solo {len(ebit)} año(s) de EBIT anual; se exigen {v.ANIOS_MINIMOS_EBIT}"
                               + (f" (el perímetro vigente del emisor arranca en {desde}: antes incluye negocios que ya no tiene)"
                                  if desde else ""))
    if not a.get("wacc"):
        return no_determinable("sin WACC (falta beta o capitalización)")
    if not acciones_total:
        return no_determinable("sin conteo de acciones")
    wacc = a["wacc"] / 100
    ebit_norm, metodo, r2, plano, ult3 = v.normalizar_ebit(ebit, em["slug"])
    if ebit_norm <= 0:
        return no_determinable(f"EBIT normalizado {ebit_norm:,.0f} <= 0 ({metodo}): sin poder de generación que valorar")

    caja_conocida = a.get("deuda_neta_mmm") is not None
    deuda_neta = a["deuda_neta_mmm"] if caja_conocida else (a.get("deuda_financiera") or 0)
    minoritarios = a.get("interes_minoritario_mmm") or 0
    minoritario_libros = minoritarios
    aviso_minoritario = None
    if minoritario_mercado:
        ke = (a.get("costo_patrimonio") or 0) / 100 or None
        util_min = {y: f["utilidad_minoritarios"] for y, f in anuales.items() if f.get("utilidad_minoritarios") is not None}
        valor_min, util_norm = v.minoritario_a_mercado(util_min, ke)
        if valor_min is None:
            aviso_minoritario = "minoritario a libros: sin utilidad de minoritarios cargada o Ke no válido"
        else:
            minoritarios = valor_min
            aviso_minoritario = (f"minoritario a mercado {valor_min:,.0f} (utilidad normalizada {util_norm:,.0f} / "
                                 f"(Ke {ke:.1%} - g {v.CRECIMIENTO_INFLACION:.0%})) en vez de {minoritario_libros:,.0f} en libros; "
                                 "igual en los tres escenarios")
    esc = v.escenarios_epv(plano, ult3, ebit_norm, wacc, deuda_neta, minoritarios, acciones_total,
                           ebit_ttm=None if con_asociadas else a.get("utilidad_operacional_ttm"))
    central = esc["central"]
    if central["patrimonio"] is None or central["patrimonio"] <= 0:
        return no_determinable(
            f"EPV de la empresa ({central['ev']:,.0f}) no cubre deuda neta ({deuda_neta:,.0f}) y minoritarios "
            f"({minoritarios:,.0f}): el patrimonio vale <= 0 bajo este método")

    capital = a.get("capital_invertido_mmm") or ((a.get("patrimonio") or 0) + (a.get("deuda_financiera") or 0))
    cap_mercado = a.get("capitalizacion_mmm")
    ev_mercado = (cap_mercado + deuda_neta + minoritarios) if cap_mercado is not None else None
    precio = a.get("precio")
    por_accion = {k: _r(esc[k]["por_accion"], 1) for k in ("bajo", "central", "alto")}
    avisos = []
    if not caja_conocida:
        avisos.append("caja desconocida: la deuda neta usa deuda bruta (subvalora)")
    if not minoritarios:
        avisos.append("sin interés minoritario cargado")
    if len(ebit) < 5:
        avisos.append(f"solo {len(ebit)} años de EBIT")
    if aviso_minoritario:
        avisos.append(aviso_minoritario)
    if desde:
        avisos.append(f"EBIT solo desde {desde} ({len(ebit)} años): antes de esa fecha el emisor tenía otro perímetro (operaciones "
                      "discontinuadas o ventas de filiales) y mezclarlo valoraría una empresa que ya no existe")
        if em["slug"] in v.COMMODITY_PURO:
            avisos.append("commodity con ventana corta: el promedio cubre el ciclo de precios de forma incompleta")
    if con_asociadas:
        avisos.append("EBIT incluye el resultado de asociadas (método de participación, neto de impuesto) "
                      f"de {len(asociadas)} años; el escenario alto no usa el TTM porque no hay TTM de asociadas")
    if em["slug"] == "ISA":
        avisos.append("EBIT sin verificar contra EEFF auditados (el Reporte Integrado de ISA declara ~6-7% más)")
    # Sensibilidad a la regla de normalización (informativa: no baja la confianza). Con R² >= 0,5 el central usa los últimos 3
    # años; si el promedio de TODO el período da un valor muy distinto, se dice (Terpel: la tendencia viene de la recuperación
    # del COVID de 2020 y el central usa 1.188 de EBIT contra 857 del promedio).
    aviso_sensibilidad, por_accion_promedio = None, None
    if metodo.startswith("tendencia") and acciones_total:
        _, eq_plano = v.valor_epv(plano, wacc, deuda_neta, minoritarios)
        if eq_plano is not None and por_accion["central"]:
            por_accion_promedio = _r(eq_plano * 1e9 / acciones_total, 1)
            if abs(por_accion_promedio / por_accion["central"] - 1) > 0.25:
                aviso_sensibilidad = (f"el central usa el EBIT de los últimos 3 años por tendencia (R² {r2:.2f}, {ult3:,.0f}); con el "
                                      f"promedio de todo el período ({plano:,.0f}) el valor central sería {por_accion_promedio:,.0f} por "
                                      f"acción ({(por_accion_promedio / por_accion['central'] - 1) * 100:+.0f} %): la tendencia puede venir de una "
                                      "recuperación y no de un crecimiento estructural")
    # DCF explícito (P1 de Codex, H3): contraste y, con la política vigente, tope del EPV. No aplica a commodities puros (el margen
    # sobre ingresos de un precio spot no es normalizable con esta serie) ni a emisores con asociadas (el resultado de asociadas
    # no tiene ingresos asociados). El mismo perímetro vigente que el EPV: años desde `PERIMETRO_DESDE`.
    dcf, dcf_detalle, motivo_sin_dcf = None, None, None
    if em["slug"] in v.COMMODITY_PURO:
        motivo_sin_dcf = "commodity puro: el margen sobre ingresos depende del precio spot; ver escenario spot vs normalizado"
    elif con_asociadas:
        motivo_sin_dcf = "emisor con resultado de asociadas: no hay ingresos asociados a esa utilidad"
    else:
        ingresos_serie = {y: f["ingresos"] for y, f in anuales.items() if f.get("ingresos") and (not desde or y >= desde)}
        ebit_op = {y: f["utilidad_operacional"] for y, f in anuales.items()
                   if f.get("utilidad_operacional") is not None and (not desde or y >= desde)}
        margenes = v.margenes_ebit(ingresos_serie, ebit_op)
        ingresos_base = a.get("ingresos_ttm") or (ingresos_serie[max(ingresos_serie)] if ingresos_serie else None)
        roic = (a.get("roic_ajustado") or 0) / 100 or None
        if len(margenes) < v.ANIOS_MINIMOS_MARGEN:
            motivo_sin_dcf = f"solo {len(margenes)} año(s) de margen EBIT; se exigen {v.ANIOS_MINIMOS_MARGEN}"
        elif not roic or roic <= 0:
            motivo_sin_dcf = "sin ROIC positivo para modelar la reinversión"
        else:
            esc_dcf, dcf_detalle = v.escenarios_dcf(ingresos_base, margenes, wacc, roic, deuda_neta, minoritarios, acciones_total)
            if esc_dcf and esc_dcf["central"]["por_accion"] is not None:
                dcf = {k: esc_dcf[k]["por_accion"] for k in ("bajo", "central", "alto")}
                dcf_detalle["peso_terminal_central"] = esc_dcf["central"]["peso_terminal"]
                dcf_detalle["roic_pct"] = roic * 100
                dcf_detalle["ingresos_base_mmm"] = ingresos_base
            else:
                motivo_sin_dcf = "el DCF no es calculable con estos insumos (margen o spread WACC - g)"
    epv_por_accion = {k: esc[k]["por_accion"] for k in ("bajo", "central", "alto")}
    metodo_usado, usado, avisos_conciliacion = v.conciliar_epv_dcf(epv_por_accion, dcf)
    if metodo_usado == "dcf" and usado["central"] <= 0:
        return no_determinable("el DCF da un patrimonio <= 0 (" + (avisos_conciliacion[0] if avisos_conciliacion else "sin detalle")
                               + "): la empresa no cubre su deuda neta con el flujo normalizado")
    por_accion_epv = por_accion
    if metodo_usado == "dcf":
        por_accion = {k: _r(usado[k], 1) for k in ("bajo", "central", "alto")}
        esc_usado = {k: {"patrimonio": (usado[k] * acciones_total / 1e9 if usado[k] is not None else None)} for k in usado}
        central = {**central, "patrimonio": esc_usado["central"]["patrimonio"]}
        esc = {**esc, "bajo": {**esc["bajo"], "patrimonio": esc_usado["bajo"]["patrimonio"]},
               "alto": {**esc["alto"], "patrimonio": esc_usado["alto"]["patrimonio"]}}
    avisos_info = list(avisos_conciliacion)  # informativos: no bajan la confianza, como el aviso de sensibilidad
    if motivo_sin_dcf:
        avisos_info.append("DCF no aplicado: " + motivo_sin_dcf)
    # Commodities puros: escenario spot (EBIT de los últimos 12 meses) separado del normalizado (promedio del período). No hay serie
    # de precios sostenibles de la materia prima en la base: el "normalizado" es el promedio histórico de la compañía, no un precio de ciclo.
    spot = None
    if em["slug"] in v.COMMODITY_PURO and a.get("utilidad_operacional_ttm") is not None and acciones_total:
        _, eq_spot = v.valor_epv(a["utilidad_operacional_ttm"], wacc, deuda_neta, minoritarios)
        spot = _r(eq_spot * 1e9 / acciones_total, 1) if eq_spot is not None else None
        avisos_info.append(f"escenario spot (EBIT de los últimos 12 meses {a['utilidad_operacional_ttm']:,.0f}): {spot if spot is not None else 'no determinable'} por acción "
                      "contra el central normalizado (promedio del período); no se cuenta con una serie de precios sostenibles de la materia prima")
    return {
        "determinable": True,
        "epv_mmm": _r(central["ev"]),
        "valor_activos_ajustado_mmm": _r(capital),
        "diagnostico_epv_vs_activos": v.diagnostico_greenwald(central["ev"], capital),
        "bajo": esc["bajo"]["patrimonio"], "central": central["patrimonio"], "alto": esc["alto"]["patrimonio"],
        "tasa": wacc,
        "confianza": "baja" if avisos else "media",
        "detalle": {
            "metodo": ("DCF explícito (menor de EPV y DCF)" if metodo_usado == "dcf" else "EPV (Greenwald) a valor del patrimonio por acción"),
            "metodo_usado": metodo_usado,
            "epv": {"por_accion": por_accion_epv, "margen_seguridad_pct": _r(v.margen_seguridad(por_accion_epv["central"], precio))},
            "dcf": ({"por_accion": {k: _r(dcf[k], 1) for k in dcf}, "margen_seguridad_pct": _r(v.margen_seguridad(dcf["central"], precio)),
                     "supuestos": f"{v.ANIOS_EXPLICITOS} años explícitos; ingresos crecen a la inflación ({v.CRECIMIENTO_INFLACION:.0%}) ±1 pp; margen EBIT "
                                  "normalizado sobre toda la ventana (bajo/alto = peor/mejor promedio móvil de 3 años); NOPAT con la tasa estatutaria "
                                  f"({v.TASA_NOMINAL:.0%}); reinversión = g / max(ROIC, WACC); terminal con ROIC = WACC (el crecimiento no crea valor)",
                     **{k: _r(x, 4) if isinstance(x, float) else x for k, x in (dcf_detalle or {}).items() if k != "anios"},
                     "anios_margen": (dcf_detalle or {}).get("anios")} if dcf else {"no_aplicado": motivo_sin_dcf}),
            "politica_valor_central": v.POLITICA_VALOR_CENTRAL,
            "avisos_metodo": avisos_info,
            "escenario_spot_por_accion": spot,
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total,
            "ebit_normalizado_mmm": _r(ebit_norm), "metodo_normalizacion": metodo, "r2": _r(r2, 2),
            "ebit_anios": sorted(ebit), "deuda_neta_mmm": _r(deuda_neta), "interes_minoritario_mmm": _r(minoritarios),
            "wacc_pct": _r(wacc * 100, 2),
            "crecimiento_nominal_implicito_pct": _r(v.crecimiento_implicito(ev_mercado, ebit_norm, wacc) * 100, 2)
            if ev_mercado and ev_mercado > 0 else None,
            "crecimiento_real_implicito_pct": _r((v.crecimiento_implicito(ev_mercado, ebit_norm, wacc)
                                                  - v.CRECIMIENTO_INFLACION) * 100, 2) if ev_mercado and ev_mercado > 0 else None,
            "supuesto_crecimiento": f"EBIT crece con la inflación ({v.CRECIMIENTO_INFLACION:.0%}), sin crecimiento real",
            "sensibilidad": v.sensibilidad_epv(ebit_norm, wacc, deuda_neta, minoritarios, acciones_total),
            "rango": "escenarios: EBIT (mín de 3 normalizaciones / central / máx incl. TTM) con WACC +1/0/-1 pp",
            "por_accion_promedio_periodo": por_accion_promedio,
            "avisos": avisos + ([aviso_sensibilidad] if aviso_sensibilidad else []),
        },
    }


def valorar_banco(cliente, em, a, acciones_total):
    anuales = _anuales(cliente, em["id"], ["utilidad_neta", "patrimonio"])
    # ROE sobre patrimonio PROMEDIO y sin años con ruptura de la serie (P1 de Codex: bancos). Antes: utilidad / patrimonio de cierre,
    # lo que dejó a Grupo Cibest con un ROE de 22 % en 2025 (patrimonio -36 %) como escenario alto.
    serie_roe, avisos_banco = v.roes_banco({y: f["utilidad_neta"] for y, f in anuales.items() if f.get("utilidad_neta") is not None},
                                           {y: f["patrimonio"] for y, f in anuales.items() if f.get("patrimonio")})
    roes = [r for _, r in serie_roe]
    entidad = _entidad_regulatoria(em["slug"])
    if entidad and ";" in entidad:
        avisos_banco.append("los indicadores regulatorios del emisor mezclan entidades (" + entidad + "): se usan solo como puerta de seguridad")
    if len(roes) < 3 and a.get("roe") is not None:
        # Davivienda Group cotiza desde 2025 (un solo ROE anual): se completa con el ROE de los últimos
        # 12 meses. Con una serie corta el rango bajo/alto casi solo se mueve por el Ke.
        roes = roes + [a["roe"] / 100]
        avisos_banco.append(f"serie corta: {len(roes)} observaciones de ROE (anuales + TTM); el rango casi no refleja variabilidad del ROE")
    if len(roes) < 2:
        return no_determinable(f"solo {len(roes)} ROE disponible(s); se exigen al menos 2")
    if not a.get("costo_patrimonio") or not a.get("patrimonio") or not acciones_total:
        return no_determinable("sin Ke, patrimonio o conteo de acciones")
    ke = a["costo_patrimonio"] / 100
    esc = v.escenarios_banco(roes, ke, a["patrimonio"], acciones_total)
    if esc["central"]["patrimonio"] is None:
        return no_determinable(f"Ke {ke:.1%} <= crecimiento perpetuo {v.CRECIMIENTO_PERPETUO_BANCOS:.1%}")
    precio = a.get("precio")
    por_accion = {k: _r(esc[k]["por_accion"], 1) for k in ("bajo", "central", "alto")}
    g_sost = v.crecimiento_sostenible(esc["roe_central"], a.get("payout_pct"))
    if g_sost is not None and g_sost < v.CRECIMIENTO_PERPETUO_BANCOS:
        avisos_banco.append(f"crecimiento sostenible con utilidades retenidas {g_sost:.1%} (ROE {esc['roe_central']:.1%} x (1 - payout {a['payout_pct']:.0f} %)) "
                            f"por debajo del g de la fórmula ({v.CRECIMIENTO_PERPETUO_BANCOS:.0%}): crecer a ese ritmo exige capital nuevo")
    return {
        "determinable": True,
        "bajo": esc["bajo"]["patrimonio"], "central": esc["central"]["patrimonio"], "alto": esc["alto"]["patrimonio"],
        "tasa": ke, "confianza": "baja",
        "detalle": {
            "metodo": "P/VL justificado = (ROE - g) / (Ke - g)",
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total, "ke_pct": _r(ke * 100, 2),
            "g_pct": v.CRECIMIENTO_PERPETUO_BANCOS * 100,
            "roe_anuales_pct": [_r(r * 100, 1) for r in roes], "roe_central_pct": _r(esc["roe_central"] * 100, 1),
            "roe_anios": [y for y, _ in serie_roe], "roe_base": "utilidad neta / patrimonio promedio, sin años con ruptura de patrimonio",
            "crecimiento_sostenible_pct": _r(g_sost * 100, 1) if g_sost is not None else None,
            "pvl_justificado": {k: _r(esc[k]["pvl"], 2) for k in ("bajo", "central", "alto")},
            "avisos": avisos_banco + ["el ROE histórico no descuenta el deterioro futuro de cartera; los indicadores "
                       "regulatorios (db/semillas/bancos_regulatorio.csv) solo entran como puerta de seguridad"],
        },
    }


def valorar_inmobiliario(cliente, em, a, acciones_total):
    patrimonio = a.get("patrimonio")
    if not patrimonio or not acciones_total:
        return no_determinable("sin patrimonio o conteo de títulos")
    f_bajo, f_central, f_alto = FACTOR_NAV_INMOBILIARIO
    precio = a.get("precio")
    por_accion = {"bajo": _r(patrimonio * f_bajo * 1e9 / acciones_total), "central": _r(patrimonio * f_central * 1e9 / acciones_total),
                  "alto": _r(patrimonio * f_alto * 1e9 / acciones_total)}
    sens = None
    op = DATOS_OPERATIVOS.get(em["slug"])
    if op and a.get("activos") and precio:
        sens = v.sensibilidad_nav_inmobiliario(
            noi_anual=op["noi_trimestre"] * 4, valor_inmuebles=a["activos"] * op["participacion_inmuebles_en_activos"],
            nav_total=patrimonio, titulos=acciones_total, precio=precio,
            ingresos_anuales=op["ingresos_trimestre"] * 4, vacancia_economica_pct=op["vacancia_economica_pct"])
        sens["fuente"] = op["fuente"]
        sens["vacancia_fisica_pct"] = op["vacancia_fisica_pct"]
        sens["advertencia"] = ("sensibilidad del NAV declarado, no una valoración independiente de inmuebles: "
                               "NOI anualizado del último trimestre y valor de inmuebles estimado")
    return {
        "determinable": True, "bajo": patrimonio * f_bajo, "central": patrimonio * f_central, "alto": patrimonio * f_alto,
        "tasa": None, "confianza": "media",
        "detalle": {
            "metodo": "NAV por título = patrimonio contable (inmuebles a valor razonable, NIC 40)",
            "por_accion": por_accion, "precio": precio,
            "margen_seguridad_pct": _r(v.margen_seguridad(por_accion["central"], precio)),
            "acciones_total": acciones_total, "sensibilidad_nav": sens,
            "perfil_deuda": (v.perfil_deuda_vehiculo(op["tramos_deuda"], op["ebitda_trimestre"])
                             if op and op.get("tramos_deuda") else None),
            "avisos": ((op or {}).get("avisos") or []) + [
                       "títulos en circulación: 49.953.606 al 31-mar-2026 (informe del Representante Legal, Fiducoldex)",
                       "NAV = patrimonio a valor razonable: el informe 1T-2026 reporta NAV de COP 144.620 por título contra "
                       "COP 66.000 de precio (descuento 54,4 %) y ventas recientes cerca del libro (Plaza Central 51 % al 96 % del libro)",
                       "el rango bajo/central/alto es un supuesto (0,90/1,00/1,00 del libro), no una valoración "
                       "independiente de los inmuebles"],
        },
    }


RUTAS = {"real": valorar_real, "banco": valorar_banco, "vehiculo_inmobiliario": valorar_inmobiliario}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    emisores = cliente.table("emisores").select("id,slug,arquetipo").execute().data
    if args.emisor:
        emisores = [e for e in emisores if e["slug"] == args.emisor]
    analisis = {a["slug"]: a for a in cliente.table("fundamentales_analisis").select("*").execute().data}

    print(f"{'EMISOR':26s}{'RUTA':14s}{'BAJO':>10s}{'CENTRAL':>10s}{'ALTO':>10s}{'PRECIO':>10s}{'MARGEN':>9s}  DIAGNÓSTICO / NOTA")
    for em in emisores:
        arq = v.ARQUETIPO_VALORACION.get(em["slug"], em.get("arquetipo"))
        a = analisis.get(em["slug"])
        if arq == "infraestructura_mercado":
            res = no_determinable("BVC: el balance incluye saldos de liquidación y márgenes de terceros que no son "
                                  "activos operativos propios; necesita un ajuste de balance específico")
            ruta = "activos_epv"
        elif arq in RUTAS and a:
            acciones = (a.get("acciones") or 0) + ACCIONES_PREFERENCIALES.get(em["slug"], (0, ""))[0]
            res = RUTAS[arq](cliente, em, a, acciones)
            ruta = RUTA_DB[arq]
        else:
            continue  # holdings: valor_engine.py

        anio, periodo = _ultimo_periodo(cliente, em["id"])
        if anio is None:
            continue
        if res["determinable"] and a and a.get("alerta_multiplos"):
            # Una alerta de datos (precio o conteo de acciones implausible, ingresos inconsistentes)
            # invalida la comparación contra el precio aunque el valor intrínseco se calcule.
            res["detalle"]["avisos"].append("alerta de datos del analizador: " + a["alerta_multiplos"][:200])
            res["confianza"] = "baja"
        d = res.get("detalle") or {}
        pa = d.get("por_accion") or {}
        if res["determinable"]:
            print(f"{em['slug']:26s}{ruta:14s}{pa.get('bajo') or 0:>10,.0f}{pa.get('central') or 0:>10,.0f}"
                  f"{pa.get('alto') or 0:>10,.0f}{d.get('precio') or 0:>10,.0f}{(d.get('margen_seguridad_pct') or 0):>8.0f}%  "
                  f"{res.get('diagnostico_epv_vs_activos') or ''}")
        else:
            print(f"{em['slug']:26s}{ruta:14s}  NO DETERMINABLE: {res['motivo_no_determinable'][:90]}")
        if args.dry_run:
            continue
        fila = {
            "emisor_id": em["id"], "anio": anio, "periodo": periodo, "ruta": ruta,
            "determinable": res["determinable"], "motivo_no_determinable": res.get("motivo_no_determinable"),
            "epv_mmm": res.get("epv_mmm"), "valor_activos_ajustado_mmm": res.get("valor_activos_ajustado_mmm"),
            "diagnostico_epv_vs_activos": res.get("diagnostico_epv_vs_activos"),
            "valor_bajo_mmm": _r(res.get("bajo")), "valor_central_mmm": _r(res.get("central")), "valor_alto_mmm": _r(res.get("alto")),
            "precio_mercado_mmm": a.get("capitalizacion_mmm") if a else None,
            "descuento_pct": _r(v.margen_seguridad(res.get("central"), a.get("capitalizacion_mmm")) if a else None, 2),
            "tasa_descuento_pct": _r(res["tasa"] * 100, 2) if res.get("tasa") else None,
            "tasa_descuento_detalle": d or None,
            "confianza": res["confianza"],
            "fecha_corte_eeff": f"{anio}-{FIN_PERIODO[periodo]}",
        }
        upsert_valor_estimado(cliente, fila)


if __name__ == "__main__":
    main()
