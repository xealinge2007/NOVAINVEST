# -*- coding: utf-8 -*-
"""Valor por activos (estilo Graham) de un emisor desde su XBRL consolidado: contraste para empresas cuyo poder de
generación no sostiene el precio (Constructora Conconcreto). NO entra al ranking: es exploratorio.

Lee el balance del último período del XBRL consolidado del corpus, parte el activo total en partidas SIN doble conteo (se
verifica que sumen el total), aplica factores de realizabilidad bajo / central / alto (convención de la casa, ver
`FACTORES`) y resta los pasivos a libros. Además calcula el factor uniforme que hace justo al precio actual: cuánto de su libro
tendrían que valer los activos no líquidos.

Uso: python jobs/valor_por_activos.py [--emisor CONSTRUCTORA_CONCONCRETO]
Salida: consola y db/VALOR_POR_ACTIVOS_<EMISOR>.md
"""

import argparse
import io
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services import valoracion as v  # noqa: E402

CORPUS_XBRL = Path(r"C:\Proyectos\BVC\SIMEV_XBRL")

# Factores de realizabilidad sobre libros (bajo, central, alto). Convención de la casa en la línea de Graham (caja 100 %, cuentas por
# cobrar y existencias con descuento, intangibles cero) y del factor de 50/75/100 % que ya se usa para participaciones no cotizadas
# (`valoracion.FACTOR_NO_COTIZADAS`); la propiedad de inversión usa el 0,90 / 1,00 de PEI (ya está a valor razonable, NIC 40). No están medidos.
FACTORES = {
    "efectivo": (1.0, 1.0, 1.0),
    "cuentas_por_cobrar": (0.70, 0.85, 1.00),
    "contratos_y_otros_corrientes": (0.50, 0.75, 1.00),
    "inventarios": (0.50, 0.65, 0.80),
    "participaciones_metodo_participacion": (0.50, 0.75, 1.00),
    "otras_inversiones_financieras": (0.70, 0.85, 1.00),
    "propiedad_de_inversion": (0.80, 0.90, 1.00),
    "propiedad_planta_equipo": (0.40, 0.60, 0.80),
    "intangibles_y_plusvalia": (0.0, 0.0, 0.0),
    "impuesto_diferido_activo": (0.0, 0.50, 1.00),
    "otros_no_corrientes": (0.50, 0.75, 1.00),
}
DESCRIPCION = {
    "efectivo": "Efectivo y equivalentes", "cuentas_por_cobrar": "Cuentas por cobrar corrientes (comerciales, relacionadas, otras)",
    "contratos_y_otros_corrientes": "Activos por contratos y otros corrientes (residual del activo corriente)",
    "inventarios": "Inventarios (obra en curso e inmuebles)",
    "participaciones_metodo_participacion": "Asociadas y negocios conjuntos (método de participación)",
    "otras_inversiones_financieras": "Otras inversiones financieras no corrientes (valor razonable)",
    "propiedad_de_inversion": "Propiedad de inversión (valor razonable)", "propiedad_planta_equipo": "Propiedad, planta y equipo",
    "intangibles_y_plusvalia": "Intangibles y plusvalía", "impuesto_diferido_activo": "Impuesto diferido activo",
    "otros_no_corrientes": "Otros activos no corrientes (residual del activo no corriente)",
}


def leer_balance(slug):
    """({concepto: miles de millones}, fecha) del último balance (contexto de instante sin dimensiones) del XBRL consolidado."""
    archivos = sorted((CORPUS_XBRL / slug).glob("*_EEFF-Consolidados-XBRL.xbrl"))
    if not archivos:
        raise SystemExit(f"sin XBRL consolidado de {slug} en {CORPUS_XBRL}")
    ruta = archivos[-1]
    s = ruta.read_text(encoding="utf-8", errors="replace")
    instantes = {}
    for cid, cuerpo in re.findall(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', s, flags=re.S):
        m = re.search(r"<xbrli:instant>([^<]+)", cuerpo)
        if m and "segment" not in cuerpo and "xbrldi" not in cuerpo:
            instantes[cid] = m.group(1)
    fecha = max(instantes.values())
    ctx = {c for c, d in instantes.items() if d == fecha}
    valores = {}
    for tag, c, x in re.findall(r'<([\w\-]+:\w+)[^>]*contextRef="([^"]+)"[^>]*>([^<]+)</', s):
        if c in ctx:
            try:
                valores[tag] = float(x) / 1e6   # miles de pesos -> miles de millones
            except ValueError:
                pass
    return valores, fecha, ruta.name


def partir_activo(b):
    """Partidas que suman el activo total sin doble conteo: las líneas principales y dos residuales explícitos."""
    efectivo = b["ifrs:CashAndCashEquivalents"]
    cxc = b["ifrs:TradeAndOtherCurrentReceivables"]
    inventarios = b["ifrs:Inventories"]
    corriente_resto = b["ifrs:CurrentAssets"] - efectivo - cxc - inventarios
    partic = b["ifrs:InvestmentAccountedForUsingEquityMethod"]
    otras_inv = b["ifrs:NoncurrentFinancialAssets"]
    prop_inv = b["ifrs:InvestmentProperty"]
    ppe = b["ifrs:PropertyPlantAndEquipment"]
    intang = b["ifrs:IntangibleAssetsAndGoodwill"]
    dta = b["ifrs:DeferredTaxAssets"]
    no_corriente_resto = b["ifrs:NoncurrentAssets"] - partic - otras_inv - prop_inv - ppe - intang - dta
    return {
        "efectivo": efectivo, "cuentas_por_cobrar": cxc, "contratos_y_otros_corrientes": corriente_resto,
        "inventarios": inventarios, "participaciones_metodo_participacion": partic, "otras_inversiones_financieras": otras_inv,
        "propiedad_de_inversion": prop_inv, "propiedad_planta_equipo": ppe, "intangibles_y_plusvalia": intang,
        "impuesto_diferido_activo": dta, "otros_no_corrientes": no_corriente_resto,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", default="CONSTRUCTORA_CONCONCRETO")
    args = parser.parse_args()
    slug = args.emisor

    b, fecha, archivo = leer_balance(slug)
    partidas = partir_activo(b)
    total = b["ifrs:Assets"]
    assert abs(sum(partidas.values()) - total) < 0.5, f"las partidas ({sum(partidas.values()):,.1f}) no suman el activo total ({total:,.1f})"
    assert min(partidas.values()) > -0.5, "una partida residual salió negativa: revisar los conceptos"
    pasivos, minoritarios = b["ifrs:Liabilities"], b.get("ifrs:NoncontrollingInterests", 0.0) or 0.0
    patrimonio = b["ifrs:EquityAttributableToOwnersOfParent"]
    assert abs(total - pasivos - patrimonio - minoritarios) < 1.0, "activo != pasivo + patrimonio"

    from app.database import cliente_servicio
    cliente = cliente_servicio()
    em = cliente.table("emisores").select("id").eq("slug", slug).execute().data[0]
    a = cliente.table("fundamentales_analisis").select("precio,acciones,capitalizacion_mmm,wacc,roe").eq("emisor_id", em["id"]).execute().data[0]
    acciones, precio, cap = a["acciones"], a["precio"], a["capitalizacion_mmm"]

    esc = v.valor_por_activos(partidas, FACTORES, pasivos, minoritarios, acciones)
    f_impl = v.factor_implicito_activos(partidas, ("efectivo",), pasivos, minoritarios, cap)
    por_accion = {k: esc[k]["por_accion"] for k in esc}
    margenes = {k: v.margen_seguridad(por_accion[k], precio) for k in por_accion}

    lineas = [f"# Valor por activos de {slug} (exploratorio)", "",
              f"Balance consolidado al **{fecha}** (`{archivo}`), miles de millones de COP. Precio {precio:,.0f}, {acciones:,.0f} acciones, capitalización {cap:,.1f}. "
              "**No entra al ranking:** es un contraste. Los factores son una convención de la casa, no una medición.", "",
              "| Partida | Libros | Factor bajo / central / alto | Realizable (central) |", "|---|---:|---|---:|"]
    for k, valor in partidas.items():
        fb, fc, fa = FACTORES[k]
        lineas.append(f"| {DESCRIPCION[k]} | {valor:,.1f} | {fb:.0%} / {fc:.0%} / {fa:.0%} | {valor * fc:,.1f} |")
    lineas += [f"| **Activo total** | **{total:,.1f}** | | **{esc['central']['activos_realizables']:,.1f}** |",
               f"| Pasivos a libros (100 %) | {pasivos:,.1f} | | {pasivos:,.1f} |", "",
               "| Escenario | Activos realizables | Patrimonio | Por acción | Margen de seguridad |", "|---|---:|---:|---:|---:|"]
    for k in ("bajo", "central", "alto"):
        m = margenes[k]
        lineas.append(f"| {k} | {esc[k]['activos_realizables']:,.1f} | {esc[k]['patrimonio']:,.1f} | {por_accion[k]:,.0f} | {'—' if m is None else f'{m:+.0f} %'} |")
    lineas += ["", f"- **Libro por acción:** {patrimonio * 1e9 / acciones:,.0f}; P/VL {precio / (patrimonio * 1e9 / acciones):.2f}.",
               f"- **Factor implícito en el precio:** {f_impl:.1%}. Para que {precio:,.0f} sea justo, los activos no líquidos tendrían que valer {f_impl:.1%} de su libro "
               "(sin ningún supuesto de la casa).",
               f"- **Rentabilidad de esos activos:** ROE de los últimos 12 meses {a.get('roe')} % contra un costo de capital (WACC) de {a.get('wacc')} %: mientras los activos no "
               "rindan más que su costo, su valor depende de venderlos, no de conservarlos."]
    texto = "\n".join(lineas) + "\n"
    print(texto)
    (RAIZ / "db" / f"VALOR_POR_ACTIVOS_{slug}.md").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
