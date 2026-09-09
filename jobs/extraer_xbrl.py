"""Carga los informes XBRL radicados ante la Superfinanciera (canal D, F4c).

Recorre `C:\\Proyectos\\BVC\\SIMEV_XBRL\\<EMISOR>\\AAAA-PERIODO_*.xbrl`, los
registra en `reportes_xbrl` y escribe las cifras en `fundamentales_reportados`.

**Cada archivo rinde DOS períodos.** El XBRL trae el del informe y su
comparativo, así que 109 archivos dan 218 filas potenciales. No aprovecharlo
sería tirar la mitad de la descarga.

**La escala se hereda dentro del emisor.** El lector la deduce archivo por
archivo (ver `lector_xbrl._escala_del_archivo`), pero es una propiedad del
emisor: su generador de XBRL y su convención de presentación no cambian de un
año a otro. Por eso el job hace dos pasadas —primero pregunta qué escala
deduce cada archivo, y si todos coinciden se la presta a los años que no
pudieron deducirla— y avisa fuerte si un emisor deduce escalas contradictorias,
porque eso significa que una de las dos está mal.

**El canal de PDF no se pisa a ciegas: se contrasta.** Donde ya hay una fila
del mismo período extraída del PDF, se comparan los campos comunes. Si
coinciden dentro del ±0,5 % que fija la arquitectura, la fila sube a
`metodo_validacion = 'doble_extraccion'` — dos canales independientes, que no
comparten ni la fuente ni el código, diciendo lo mismo. Si discrepan, manda el
XBRL (es la radicación oficial, etiquetada por concepto) pero la discrepancia
se reporta para mirarla, no se entierra.

Uso:
    python jobs/extraer_xbrl.py [--emisor GEB] [--dry-run]
"""

import argparse
import csv
import hashlib
import io
import re
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from app.services.extraccion import lector_xbrl  # noqa: E402

CARPETA_XBRL = Path(r"C:\Proyectos\BVC\SIMEV_XBRL")
NOMBRE_MANIFIESTO = ("MANIFESTO.csv", "MANIFIESTO.csv")
PATRON_NOMBRE = re.compile(r"^(\d{4})-(ANUAL|T[1-4])_", re.IGNORECASE)

CAMPOS_NUMERICOS = [
    "ingresos", "utilidad_operacional", "utilidad_neta", "ebitda",
    "activos_totales", "pasivos_totales", "patrimonio", "flujo_caja_operativo",
    "deuda_financiera", "acciones_en_circulacion", "dividendos_decretados",
]
# Campos que los dos canales extraen y significan LO MISMO. La lista es corta
# a propósito.
#
# `patrimonio` y `utilidad_neta` quedan fuera aunque los dos canales los
# tengan, porque no siempre miden lo mismo: el XBRL toma
# `EquityAttributableToOwnersOfParent` (la controladora) y el canal de PDF suele
# quedarse con la fila "Total patrimonio" (el grupo, que incluye el interés no
# controlante). Verificado real en GEB, cuyo propio PDF trae las dos líneas:
# "Total patrimonio de la controladora ... 20.502.514" y "Total patrimonio ...
# 21.277.906". Contrastarlos daba siete discrepancias que no eran errores de
# nadie -- eran dos conceptos distintos, ambos correctos. Compararlos sería
# fabricar ruido y, peor, impedir que períodos bien extraídos suban a
# `doble_extraccion`.
#
# `ebitda` también queda fuera: es derivado en ambos, con fórmulas distintas.
CAMPOS_CONTRASTABLES = ["activos_totales", "pasivos_totales", "ingresos"]
TOLERANCIA_CONTRASTE = 0.005  # ±0,5%, el que fija db/DECISION_ARQUITECTURA_EXTRACCION.md
MINIMO_CAMPOS_CONTRASTE = 2

# Misma limitación aceptada que el canal de PDF (`extractor_generico`): en
# bancos y holdings financieros no se publica `ingresos` ni
# `utilidad_operacional`. Un banco no reporta una línea de ingresos comparable
# con la de una petrolera —su métrica es el margen neto de interés— y el XBRL,
# a diferencia del PDF, sí trae etiquetado un `Revenue` que tienta a usarlo.
# Usarlo daba disparates: Davivienda salía con 268 % de margen neto (utilidad
# 1.954 sobre "ingresos" 729). Se dejan en None a propósito, no se rellenan.
SECTORES_FINANCIEROS = {"banca", "holding_financiero"}
CAMPOS_NO_APLICABLES_FINANCIEROS = ("ingresos", "utilidad_operacional", "ebitda")


def _hash(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_manifiesto(carpeta: Path) -> dict:
    """{(emisor, archivo): url_descarga}. La procedencia es obligatoria por
    §5.1.4; si no está el manifiesto se avisa y se sigue, pero las filas quedan
    sin URL y eso se ve en la tabla."""
    for nombre in NOMBRE_MANIFIESTO:
        ruta = carpeta / nombre
        if ruta.is_file():
            with open(ruta, encoding="utf-8-sig", newline="") as f:
                return {(r["emisor"].strip(), r["archivo"].strip()): (r.get("url_descarga") or "").strip()
                        for r in csv.DictReader(f) if r.get("emisor") and r.get("archivo")}
    return {}


def escala_del_emisor(archivos: list[Path]) -> tuple:
    """(escala, aviso). Pregunta a cada archivo qué escala deduce por su cuenta;
    si todos los que pudieron deducirla coinciden, esa es la del emisor."""
    deducidas = set()
    for arch in archivos:
        m = PATRON_NOMBRE.match(arch.name)
        if not m:
            continue
        try:
            e = lector_xbrl.leer(arch, int(m.group(1)), m.group(2).upper())["xbrl"].get("escala")
            if e:
                deducidas.add(e)
        except Exception:
            continue
    if len(deducidas) == 1:
        return deducidas.pop(), None
    if len(deducidas) > 1:
        return None, f"deduce escalas contradictorias {sorted(deducidas)} -- ninguna se hereda"
    return None, None


def _contrastar(fila_previa: dict, campos: dict) -> tuple:
    """(coinciden, detalle). Compara los campos comunes con la fila que dejó el
    canal de PDF."""
    comparados, discrepan = [], []
    for c in CAMPOS_CONTRASTABLES:
        viejo, nuevo = fila_previa.get(c), campos.get(c)
        if viejo is None or nuevo is None or viejo == 0:
            continue
        comparados.append(c)
        if abs(float(nuevo) - float(viejo)) / abs(float(viejo)) > TOLERANCIA_CONTRASTE:
            discrepan.append(f"{c}: pdf={float(viejo):,.1f} xbrl={float(nuevo):,.1f}")
    if len(comparados) < MINIMO_CAMPOS_CONTRASTE:
        # No es un desacuerdo: es que la fila del PDF no trae suficientes
        # campos comunes. Se distingue a propósito -- llamar "discrepancia" a
        # una falta de datos enseña a ignorar la lista de discrepancias.
        return None, f"no contrastable: solo {len(comparados)} campo(s) en común con la fila del PDF"
    if discrepan:
        return False, " | ".join(discrepan)
    return True, f"{len(comparados)} campos coinciden dentro de ±0,5%"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emisor", type=str, default=None)
    parser.add_argument("--carpeta", type=Path, default=CARPETA_XBRL)
    parser.add_argument("--dry-run", action="store_true", help="lee y reporta, no escribe en Supabase")
    args = parser.parse_args()

    from app.database import cliente_servicio

    cliente = cliente_servicio()
    datos_emisores = cliente.table("emisores").select("id,slug,sector").execute().data
    emisores = {e["slug"]: e["id"] for e in datos_emisores}
    sectores = {e["slug"]: e["sector"] for e in datos_emisores}

    previas = {}
    for f in cliente.table("fundamentales_reportados").select("*").execute().data:
        previas[(f["emisor_id"], f["anio"], f["periodo"])] = f

    carpetas = sorted(p for p in args.carpeta.iterdir() if p.is_dir())
    if args.emisor:
        carpetas = [p for p in carpetas if p.name == args.emisor]

    manifiesto = cargar_manifiesto(args.carpeta)
    if not manifiesto:
        print("AVISO: sin manifiesto de procedencia -- las filas quedarán sin url_descarga")

    resumen = defaultdict(int)
    dobles, discrepancias, avisos = [], [], []

    for carpeta in carpetas:
        slug = carpeta.name
        if slug not in emisores:
            print(f"  [{slug}] no está en `emisores` -- se salta")
            resumen["emisor_desconocido"] += 1
            continue
        emisor_id = emisores[slug]
        archivos = sorted(carpeta.glob("*.xbrl"))
        if not archivos:
            continue

        escala, aviso = escala_del_emisor(archivos)
        if aviso:
            avisos.append(f"{slug}: {aviso}")
            print(f"  [{slug}] AVISO: {aviso}")

        for arch in archivos:
            m = PATRON_NOMBRE.match(arch.name)
            if not m:
                resumen["nombre_no_parseable"] += 1
                continue
            anio_informe, periodo = int(m.group(1)), m.group(2).upper()

            leidos = []
            for indice, anio in ((1, anio_informe), (2, anio_informe - 1)):
                try:
                    r = lector_xbrl.leer(arch, anio, periodo, indice_periodo=indice, escala_conocida=escala)
                except Exception as e:
                    print(f"  {slug} {anio}-{periodo} idx{indice}: ERROR {type(e).__name__}: {e}")
                    resumen["error"] += 1
                    continue
                campos = {c: r["campos"][c]["valor"] for c in CAMPOS_NUMERICOS
                          if c in r["campos"] and r["campos"][c]["valor"] is not None}
                if sectores.get(slug) in SECTORES_FINANCIEROS:
                    for c in CAMPOS_NO_APLICABLES_FINANCIEROS:
                        campos.pop(c, None)
                if not campos:
                    resumen["sin_cifras"] += 1
                    continue
                if r["cuadra_balance"] is False:
                    print(f"  {slug} {anio}-{periodo}: el balance no cuadra -- no se escribe")
                    resumen["balance_no_cuadra"] += 1
                    continue
                leidos.append((anio, campos, r))

            if not args.dry_run and leidos:
                cliente.table("reportes_xbrl").upsert({
                    "emisor_id": emisor_id, "anio": anio_informe, "periodo": periodo, "consolidado": True,
                    "nombre_archivo": arch.name, "ruta_local": str(arch), "hash_sha256": _hash(arch),
                    "punto_entrada": leidos[0][2]["xbrl"].get("punto_entrada"),
                    "escala_deducida": leidos[0][2]["xbrl"].get("escala"),
                    "fuente_origen": "superfinanciera",
                    "url_descarga": manifiesto.get((slug, arch.name)) or None,
                    "estado": "procesado",
                }, on_conflict="emisor_id,anio,periodo,consolidado").execute()

            for anio, campos, r in leidos:
                previa = previas.get((emisor_id, anio, periodo))
                metodo, nota = "xbrl_radicado", ""
                if previa and previa.get("metodo_validacion") not in (None, "xbrl_radicado"):
                    coinciden, detalle = _contrastar(previa, campos)
                    if coinciden is True:
                        metodo = "doble_extraccion"
                        dobles.append(f"{slug} {anio}-{periodo}: {detalle}")
                    elif coinciden is False:
                        discrepancias.append(f"{slug} {anio}-{periodo}: {detalle}")
                    else:
                        resumen["no_contrastable"] += 1
                    nota = detalle

                fila = {
                    "emisor_id": emisor_id, "anio": anio, "periodo": periodo, "consolidado": True,
                    "origen": "reportado", "metodo_validacion": metodo,
                    "moneda": "COP", "unidad": "miles_de_millones",
                    **{c: None for c in CAMPOS_NUMERICOS},
                    **campos,
                }
                if not args.dry_run:
                    cliente.table("fundamentales_reportados").upsert(
                        fila, on_conflict="emisor_id,anio,periodo,consolidado"
                    ).execute()
                resumen[metodo] += 1
                print(f"  {slug:26s} {anio}-{periodo:5s} {len(campos):2d} campos  {metodo}"
                      + (f"  [{nota[:70]}]" if nota else ""))

    print("\n" + "=" * 76)
    for k, v in sorted(resumen.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    if dobles:
        print(f"\n{len(dobles)} período(s) confirmados por los DOS canales (doble_extraccion):")
        for d in dobles[:15]:
            print(f"   {d}")
    if discrepancias:
        print(f"\n{len(discrepancias)} período(s) donde PDF y XBRL DISCREPAN — manda el XBRL, revisar:")
        for d in discrepancias[:20]:
            print(f"   {d}")
    if avisos:
        print(f"\n{len(avisos)} aviso(s) de escala:")
        for a in avisos:
            print(f"   {a}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
