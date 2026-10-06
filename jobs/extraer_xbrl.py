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
# Un archivo con sufijo después de `-XBRL` es una SERIE PARALELA del mismo
# emisor y período, no un reemplazo. Verificado real: Grupo Cibest empezó a
# radicar XBRL propio desde 2025-T2, y Cowork lo bajó junto al de Bancolombia
# S.A. dentro de la misma carpeta (`...-XBRL-CIBEST.xbrl`). Las dos series
# comparten (emisor, año, período), así que cargarlas sin distinguir haría que
# una pisara a la otra en silencio -- exactamente el cambio de perímetro que se
# quería poder ver. Se saltan y se reportan hasta decidir cómo empalmarlas.
PATRON_SERIE_PARALELA = re.compile(r"-XBRL-(.+)\.xbrl$", re.IGNORECASE)

CAMPOS_NUMERICOS = [
    "ingresos", "utilidad_operacional", "utilidad_neta", "ebitda",
    "activos_totales", "pasivos_totales", "patrimonio", "flujo_caja_operativo",
    "deuda_financiera", "acciones_en_circulacion", "dividendos_decretados",
]
CAMPOS_NUMERICOS_BASE = list(CAMPOS_NUMERICOS)
# No se reexpresan: el conteo de acciones y los dividendos decretados son hechos de la fecha, no del estado.
CAMPOS_SIN_REEXPRESION = ("acciones_en_circulacion", "dividendos_decretados")
# Variación de la línea de ventas (utilidad neta en financieros) por encima de la cual una reexpresión se trata
# como cambio de perímetro y no se aplica sola. Conconcreto 2021 (la corrección que motivó la política) varió 7,7 %.
UMBRAL_CAMBIO_PERIMETRO = 0.10
# Reexpresiones con salto de ventas revisadas a mano el 5-oct-2026 (XBRL de ambos años + notas). "aplicar": la cifra
# nueva es la base vigente del negocio; "conservar": no hay reexpresión real. Ver db/CRITERIOS_VALORACION.md.
REEXPRESION_REVISADA = {
    ("MINEROS", 2022): ("aplicar", "operación discontinuada (-238,5); utilidad total idéntica (19,08); la nueva es la base de operaciones continuas"),
    ("BVC", 2019): ("aplicar", "operación discontinuada (7,07); la nueva es la base de operaciones continuas"),
    ("GRUPO_ARGOS", 2023): ("aplicar", "operación discontinuada (697,8); utilidad total idéntica (1.460,0)"),
    ("GRUPO_ARGOS", 2024): ("aplicar", "operación discontinuada (7.486,1); utilidad total idéntica (7.646,8)"),
    ("CEMENTOS_ARGOS", 2023): ("aplicar", "perímetro sin EE. UU. (ingresos 12.717 -> 3.916); la serie del EPV arranca en 2023 (PERIMETRO_DESDE)"),
    ("CEMENTOS_ARGOS", 2024): ("aplicar", "segundo cambio de perímetro: 3.968 -> 5.299, base vigente del informe 2025"),
    ("ENKA", 2021): ("aplicar", "sin operaciones discontinuadas; la utilidad total también cambia (57,7 -> 42,0); causa no verificada"),
    ("GRUPO_CIBEST_BANCOLOMBIA", 2021): ("conservar", "falso positivo: el comparativo del XBRL 2022 rotula con 2020 los valores de 2021 (4.207,8 = el original)"),
}
# P1: se leen siempre, pero solo se escriben si ya está aplicado db/migrate_p1_estados_ampliados.sql
CAMPOS_NUMERICOS += list(lector_xbrl.CAMPOS_AMPLIADOS)
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

# Bug real encontrado el 18-sep-2026 cruzando el Bloque 2 contra PDF: en un
# archivo TRIMESTRAL, el comparativo de un campo de BALANCE (activos,
# pasivos, patrimonio, deuda, acciones en circulacion, dividendos -- todos
# de "instante", no de "duracion") es el CIERRE ANUAL anterior, no el mismo
# trimestre del año anterior -- asi lo exige la NIIF para el estado de
# situacion financiera (el estado de resultados si compara el mismo
# trimestre, y esos campos SI son correctos). Verificado real: el
# comparativo de CORFICOLOMBIANA leido desde 2024-T1/T2/T3 da el MISMO
# activos_totales (57.281,2) en los tres -- es el cierre de 2023-ANUAL
# (confirmado identico), no marzo/junio/septiembre-2023. Escribirlo como si
# fuera (2023, T1/T2/T3) corrompe la fila. Por eso estos campos del
# comparativo se descartan salvo cuando el periodo del archivo YA es ANUAL
# (ahi el comparativo tambien es un cierre anual, y coincide).
CAMPOS_INSTANTANEOS_NO_COMPARABLES_TRIMESTRE = {
    "activos_totales", "pasivos_totales", "patrimonio", "deuda_financiera",
    "acciones_en_circulacion", "dividendos_decretados",
}

# Misma limitación aceptada que el canal de PDF (`extractor_generico`): en
# bancos y holdings financieros no se publica `ingresos` ni
# `utilidad_operacional`. Un banco no reporta una línea de ingresos comparable
# con la de una petrolera —su métrica es el margen neto de interés— y el XBRL,
# a diferencia del PDF, sí trae etiquetado un `Revenue` que tienta a usarlo.
# Usarlo daba disparates: Davivienda salía con 268 % de margen neto (utilidad
# 1.954 sobre "ingresos" 729). Se dejan en None a propósito, no se rellenan.
SECTORES_FINANCIEROS = {"banca", "holding_financiero"}
CAMPOS_NO_APLICABLES_FINANCIEROS = ("ingresos", "utilidad_operacional", "ebitda", "utilidad_bruta", "gasto_financiero")

# Emisores donde la serie paralela (sufijo `-XBRL-<SERIE>.xbrl`) reemplaza a
# la principal, en vez de ignorarse. GRUPO_CIBEST_BANCOLOMBIA: desde 2025-T2
# el emisor radica DOS XBRL por trimestre -- el original (Bancolombia S.A.,
# perímetro angosto) y uno con sufijo "-CIBEST" (Grupo Cibest S.A., el nuevo
# holding que reemplazó a Bancolombia como matriz cotizada; perímetro ~17-31%
# más grande: activos 2026-T2 363.082 vs 311.296, patrimonio 38.124 vs
# 29.080). El ticker CIBEST.CL cotiza acciones del grupo NUEVO, así que su
# serie es la que describe lo que un accionista posee hoy -- se prefiere esa.
#
# El salto de perímetro entre 2025-ANUAL (viejo, sin versión "-CIBEST") y
# 2025-T1..2026-T2 (nuevo) NO es crecimiento real. `analizador_fundamental.py`
# lo sabe y no extiende el TTM de este emisor más allá del ANUAL por eso.
EMISORES_SERIE_PARALELA_REEMPLAZA = {"GRUPO_CIBEST_BANCOLOMBIA"}


# Cifras que el propio XBRL radicado trae mal y que se verificaron contra el informe
# auditado. El XBRL pisa lo manual en la fusión, así que se reaplican al final de cada carga.
# (slug, año, período, campo) -> (valor en miles de millones, fuente)
CORRECCIONES_VERIFICADAS = {
    ("CELSIA", 2025, "ANUAL", "ingresos"): (
        5395.120, "informe 2025-ANUAL pág. 50 (KPMG); el XBRL declara 2.097,753 -- DOCTRINA_VALOR.md §11"),
}


def decidir_reexpresion(previos: dict, comparativo: dict, financiero: bool = False, revisada: str = None):
    """(campos fusionados, estado, detalle) para el comparativo de un cierre ANUAL frente al valor ya leído.

    Política de reexpresión (05-oct-2026): el comparativo del cierre anual SIGUIENTE es la versión más reciente
    de ese año y manda sobre el original. Conconcreto 2021 se reexpresó de EBIT 74,3 a -250,2 en el XBRL de 2022
    (contrato oneroso de Vía 40, nota 2.7 de los estados auditados); usar el original sobrevaloraba el EPV 9 veces.
    Solo para cierres anuales: en trimestres el comparativo trae contextos mal etiquetados (caso Promigas) y el
    propio sigue mandando.

    Salvaguarda: un salto de más de `UMBRAL_CAMBIO_PERIMETRO` en la línea de ventas (en la utilidad neta, para los
    financieros, que no tienen ventas) es la firma de un CAMBIO DE PERÍMETRO (operaciones discontinuadas, venta
    de filiales), no de la corrección de un error: el año reexpresado y los anteriores quedarían en bases
    distintas. No se aplica solo: se conserva el original (estado "no_aplicada") para revisión a mano.

    `revisada`: decisión humana ya tomada para ese (emisor, año) en `REEXPRESION_REVISADA`; salta la salvaguarda.

    estado: "aplicada" (cambió alguna cifra clave), "no_aplicada" (salto de perímetro) o "sin_cambio"."""
    previos = {c: v for c, v in previos.items() if v is not None}
    reexpresion = {c: v for c, v in comparativo.items() if c not in CAMPOS_SIN_REEXPRESION}
    cambios = {c: (previos[c], v) for c, v in reexpresion.items()
               if c in previos and abs(v - previos[c]) > max(0.02 * abs(previos[c]), 0.05)}
    clave = [c for c in ("ingresos", "utilidad_operacional", "utilidad_neta") if c in cambios]
    detalle = "; ".join(f"{c} {cambios[c][0]:,.1f} -> {cambios[c][1]:,.1f}" for c in clave)
    if revisada == "conservar":
        return {**comparativo, **previos}, "no_aplicada", detalle
    if revisada == "aplicar":
        return {**previos, **reexpresion}, ("aplicada" if clave else "sin_cambio"), detalle
    base = "utilidad_neta" if financiero else "ingresos"
    if base in cambios and cambios[base][0] and             abs(cambios[base][1] - cambios[base][0]) > UMBRAL_CAMBIO_PERIMETRO * abs(cambios[base][0]):
        return {**comparativo, **previos}, "no_aplicada", detalle
    return {**previos, **reexpresion}, ("aplicada" if clave else "sin_cambio"), detalle


def sanear_ingresos_anuales(cliente, emisores_por_id, aplicar=True):
    """Último paso de la carga (auditoría 01-oct-2026, E4). Un ANUAL con ingresos MENORES que
    un trimestre acumulado del mismo año es imposible: el XBRL del emisor está mal. Si hay una
    corrección verificada contra el informe se aplica; si no, el ingreso del ANUAL se deja en
    None (no se adivina) y el período queda marcado en el reporte."""
    filas = cliente.table("fundamentales_reportados").select(
        "id,emisor_id,anio,periodo,ingresos,acumulado").execute().data
    max_acum = {}
    for f in filas:
        if f["periodo"] != "ANUAL" and f.get("acumulado") is True and f.get("ingresos"):
            k = (f["emisor_id"], f["anio"])
            max_acum[k] = max(max_acum.get(k, 0), f["ingresos"])
    cambios = []
    for f in filas:
        if f["periodo"] != "ANUAL" or not f.get("ingresos"):
            continue
        slug = emisores_por_id.get(f["emisor_id"])
        corr = CORRECCIONES_VERIFICADAS.get((slug, f["anio"], "ANUAL", "ingresos"))
        if corr and abs(f["ingresos"] - corr[0]) > 0.001:
            nuevo, motivo = corr[0], f"corregido a {corr[0]:,.3f}: {corr[1]}"
        elif f["ingresos"] < max_acum.get((f["emisor_id"], f["anio"]), 0) * 0.999:
            nuevo, motivo = None, "ingresos ANUAL menores que un trimestre acumulado: se descartan, sin verificar"
        else:
            continue
        cambios.append(f"{slug} {f['anio']}-ANUAL ingresos {f['ingresos']:,.3f} -> {nuevo}  [{motivo}]")
        if aplicar:
            cliente.table("fundamentales_reportados").update({"ingresos": nuevo}).eq("id", f["id"]).execute()
    return cambios


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

    # `acumulado` y `dias_periodo` los agrega db/migrate_f4d_acumulado.sql. El
    # job funciona con o sin ellos: si la migración no está aplicada, escribe
    # todo lo demás y avisa, en vez de morir a mitad de una carga de 200
    # archivos por una columna que falta.
    muestra = cliente.table("fundamentales_reportados").select("*").limit(1).execute().data
    hay_periodicidad = bool(muestra) and "acumulado" in muestra[0]
    if not hay_periodicidad:
        print("AVISO: falta db/migrate_f4d_acumulado.sql -- se cargan las cifras, "
              "pero sin registrar si el flujo es acumulado o del trimestre suelto")

    if not (muestra and "efectivo" in muestra[0]):
        print("AVISO: falta db/migrate_p1_estados_ampliados.sql -- no se escriben caja, capex, "
              "gasto financiero, etc.")
        CAMPOS_NUMERICOS[:] = CAMPOS_NUMERICOS_BASE
    else:
        for campo, migracion in (("resultado_asociadas", "migrate_p4_resultado_asociadas.sql"),
                                 ("utilidad_minoritarios", "migrate_p5_utilidad_minoritarios.sql")):
            if campo not in muestra[0]:
                print(f"AVISO: falta db/{migracion} -- no se escribe {campo}")
                CAMPOS_NUMERICOS[:] = [c for c in CAMPOS_NUMERICOS if c != campo]

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
    dobles, discrepancias, avisos, paralelas = [], [], [], []
    propios_leidos = set()  # (emisor_id, anio, periodo) leídos de SU propio archivo en esta corrida
    reexpresados = []       # cierres anuales cuyo comparativo posterior cambió cifras clave
    no_aplicados = []       # reexpresiones con salto de perímetro: se conserva el original, a revisión

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

        if slug in EMISORES_SERIE_PARALELA_REEMPLAZA:
            # Para estos emisores la serie paralela ES la vigente -- se
            # descarta el archivo principal de cada (año, período) que tenga
            # contraparte paralela, para no procesar ambos.
            claves_con_paralela = set()
            for a in archivos:
                if PATRON_SERIE_PARALELA.search(a.name):
                    mm = PATRON_NOMBRE.match(a.name)
                    if mm:
                        claves_con_paralela.add((mm.group(1), mm.group(2).upper()))
            archivos = [
                a for a in archivos
                if PATRON_SERIE_PARALELA.search(a.name) or (
                    (mm := PATRON_NOMBRE.match(a.name)) is None
                    or (mm.group(1), mm.group(2).upper()) not in claves_con_paralela
                )
            ]

        escala, aviso = escala_del_emisor(archivos)
        if aviso:
            avisos.append(f"{slug}: {aviso}")
            print(f"  [{slug}] AVISO: {aviso}")

        for arch in archivos:
            m = PATRON_NOMBRE.match(arch.name)
            if not m:
                resumen["nombre_no_parseable"] += 1
                continue
            paralela = PATRON_SERIE_PARALELA.search(arch.name)
            if paralela and slug not in EMISORES_SERIE_PARALELA_REEMPLAZA:
                paralelas.append(f"{slug}/{arch.name} (serie '{paralela.group(1)}')")
                resumen["serie_paralela_no_cargada"] += 1
                continue
            anio_informe, periodo = int(m.group(1)), m.group(2).upper()

            leidos = []
            for indice, anio in ((1, anio_informe), (2, anio_informe - 1)):
                try:
                    r = lector_xbrl.leer(arch, anio, periodo, indice_periodo=indice,
                                         escala_conocida=escala, emisor=slug)
                except Exception as e:
                    print(f"  {slug} {anio}-{periodo} idx{indice}: ERROR {type(e).__name__}: {e}")
                    resumen["error"] += 1
                    continue
                campos = {c: r["campos"][c]["valor"] for c in CAMPOS_NUMERICOS
                          if c in r["campos"] and r["campos"][c]["valor"] is not None}
                if indice == 2 and periodo != "ANUAL":
                    for c in CAMPOS_INSTANTANEOS_NO_COMPARABLES_TRIMESTRE:
                        campos.pop(c, None)
                if sectores.get(slug) in SECTORES_FINANCIEROS:
                    for c in CAMPOS_NO_APLICABLES_FINANCIEROS:
                        campos.pop(c, None)
                if not campos:
                    resumen["sin_cifras"] += 1
                    continue
                # El chequeo de cuadre usa activos/pasivos/patrimonio con la
                # fecha de BALANCE que trae el archivo -- para el comparativo
                # de un trimestre eso es el cierre anual anterior (ver el
                # aviso de CAMPOS_INSTANTANEOS_NO_COMPARABLES_TRIMESTRE
                # arriba), no lo que se etiqueta como (anio, periodo). Como
                # esos campos ya se descartaron de `campos` para ese caso, el
                # chequeo no aplica a lo que realmente se va a escribir.
                aplica_chequeo_cuadre = not (indice == 2 and periodo != "ANUAL")
                if aplica_chequeo_cuadre and r["cuadra_balance"] is False:
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

                # Un mismo período se lee dos veces: una vez como período propio
                # de su archivo, otra como comparativo dentro del archivo del
                # período siguiente. El comparativo suele traer menos campos
                # (el contexto de "flujo" del año anterior no siempre está
                # completo). Fusionar en vez de reemplazar evita que la segunda
                # lectura, más pobre, borre con `None` lo que la primera ya
                # había extraído bien -- verificado real en TERPEL 2025-T1
                # (11 campos desde su propio archivo, reducido a 5 al procesar
                # 2026-T1 como comparativo, en la misma corrida).
                # `manual` va en la lista a propósito. Una fila cargada a mano es una
                # decisión humana con su fuente citada (la página del informe), no un
                # residuo de otra corrida: si no se fusiona, el reproceso la borra en
                # silencio. Verificado real el 25-sep-2026: al recargar el corpus,
                # GRUPO_SURA perdió los 6 períodos que se habían leído de su balance
                # consolidado y volvió a salir con deuda cero, que es justo el bug que
                # esa carga venía a corregir.
                #
                # El orden de la fusión sigue siendo el correcto: lo que el XBRL trae
                # PISA a lo manual. La carga a mano solo sobrevive donde el canal no
                # tiene nada que decir, que es para lo que existe.
                campos_previos_xbrl = (
                    {c: previa.get(c) for c in CAMPOS_NUMERICOS}
                    if previa and previa.get("metodo_validacion") in (
                        "xbrl_radicado", "doble_extraccion", "manual")
                    else {}
                )
                # El archivo PROPIO de un período manda sobre su comparativo en el archivo
                # siguiente: el comparativo solo rellena huecos. Verificado real (auditoría
                # 01-oct-2026, E3): el XBRL 2026-T2 de PROMIGAS trae como "comparativo 2025-T2"
                # los ingresos del ANUAL 2024, y al pisar la fila propia (correcta) dejaba dos
                # períodos distintos con las mismas cifras.
                clave_periodo = (emisor_id, anio, periodo)
                es_comparativo = anio != anio_informe
                if es_comparativo and clave_periodo in propios_leidos and periodo == "ANUAL":
                    # Política de reexpresión (05-oct-2026), ver `decidir_reexpresion`.
                    campos_fusionados, estado, detalle_cambio = decidir_reexpresion(
                        campos_previos_xbrl, campos, financiero=sectores.get(slug) in SECTORES_FINANCIEROS,
                        revisada=REEXPRESION_REVISADA.get((slug, anio), (None,))[0])
                    if estado == "no_aplicada":
                        no_aplicados.append(f"{slug} {anio}: {detalle_cambio} (informe {anio_informe}; posible cambio de perímetro, "
                                            "se conserva el original)")
                        resumen["anual_reexpresion_no_aplicada_perimetro"] += 1
                    elif estado == "aplicada":
                        reexpresados.append(f"{slug} {anio}: {detalle_cambio} (reexpresado en el informe {anio_informe})")
                        resumen["anual_reexpresado_por_comparativo"] += 1
                elif es_comparativo and clave_periodo in propios_leidos:
                    campos_fusionados = {**campos, **{c: v for c, v in campos_previos_xbrl.items() if v is not None}}
                else:
                    campos_fusionados = {**campos_previos_xbrl, **campos}
                    if not es_comparativo:
                        propios_leidos.add(clave_periodo)

                # Guarda anti-duplicado: un trimestre con exactamente los mismos ingresos y
                # utilidad neta que el ANUAL de OTRO año es la firma de un defecto de la propia
                # radicación del emisor (Promigas 2026-T2 declara como acumulado a junio los
                # ingresos de todo 2025). No se adivina la cifra buena: se descartan los flujos
                # de ese trimestre y el período queda con solo los saldos.
                if periodo != "ANUAL" and campos_fusionados.get("ingresos") and campos_fusionados.get("utilidad_neta") is not None:
                    huella = (round(campos_fusionados["ingresos"], 3), round(campos_fusionados["utilidad_neta"], 3))
                    for (e_id, a_prev, p_prev), fila_prev in previas.items():
                        if (e_id == emisor_id and p_prev == "ANUAL" and a_prev != anio
                                and fila_prev.get("ingresos") and fila_prev.get("utilidad_neta") is not None
                                and (round(fila_prev["ingresos"], 3), round(fila_prev["utilidad_neta"], 3)) == huella):
                            for c in ("ingresos", "utilidad_operacional", "utilidad_neta", "ebitda", "flujo_caja_operativo"):
                                campos_fusionados[c] = None
                            nota = f"flujos descartados: idénticos al ANUAL {a_prev} (defecto del emisor)"
                            resumen["flujos_descartados_por_duplicado"] += 1
                            break
                if len(campos) < sum(1 for v in campos_previos_xbrl.values() if v is not None):
                    resumen["comparativo_mas_pobre_fusionado"] += 1

                fila = {
                    "emisor_id": emisor_id, "anio": anio, "periodo": periodo, "consolidado": True,
                    "origen": "reportado", "metodo_validacion": metodo,
                    "moneda": "COP", "unidad": "miles_de_millones",
                    **({"acumulado": r["xbrl"].get("acumulado"),
                        "dias_periodo": r["xbrl"].get("dias_periodo")} if hay_periodicidad else {}),
                    **{c: None for c in CAMPOS_NUMERICOS},
                    **campos_fusionados,
                }
                if not args.dry_run:
                    cliente.table("fundamentales_reportados").upsert(
                        fila, on_conflict="emisor_id,anio,periodo,consolidado"
                    ).execute()
                previas[(emisor_id, anio, periodo)] = {**(previa or {}), **fila}
                resumen[metodo] += 1
                print(f"  {slug:26s} {anio}-{periodo:5s} {len(campos_fusionados):2d} campos  {metodo}"
                      + (f"  [{nota[:70]}]" if nota else ""))

    print("\n" + "=" * 76)
    for k, v in sorted(resumen.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    if reexpresados:
        print(f"\n{len(reexpresados)} cierre(s) ANUAL reexpresado(s) por el informe del año siguiente (rige la versión nueva):")
        for d in reexpresados:
            print(f"   {d}")
    if no_aplicados:
        print(f"\n{len(no_aplicados)} reexpresión(es) ANUAL NO aplicadas por posible cambio de perímetro (revisar a mano):")
        for d in no_aplicados:
            print(f"   {d}")
    if dobles:
        print(f"\n{len(dobles)} período(s) confirmados por los DOS canales (doble_extraccion):")
        for d in dobles[:15]:
            print(f"   {d}")
    if discrepancias:
        print(f"\n{len(discrepancias)} período(s) donde PDF y XBRL DISCREPAN — manda el XBRL, revisar:")
        for d in discrepancias[:20]:
            print(f"   {d}")
    if paralelas:
        print(f"\n{len(paralelas)} archivo(s) de SERIE PARALELA no cargados (pisarían la serie principal):")
        for x in paralelas:
            print(f"   {x}")
    if avisos:
        print(f"\n{len(avisos)} aviso(s) de escala:")
        for a in avisos:
            print(f"   {a}")
    cambios = sanear_ingresos_anuales(cliente, {v: k for k, v in emisores.items()}, aplicar=not args.dry_run)
    if cambios:
        print(f"\n{len(cambios)} ingreso(s) ANUAL saneados (E4):")
        for x in cambios:
            print(f"   {x}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
