# ⛔ OPERACIÓN CERRADA (25-sep-2026) — NO EJECUTAR

> **Este documento ya se ejecutó y está cumplido. No se lo pases a una sesión nueva.**
>
> La sesión de descarga barrió SIMEV emisor por emisor y leyó los informes de la Prioridad 4.
> Resultado: la cobertura de `deuda_financiera` pasó de 44,6 % de filas vacías a **19,9 %**
> (657 filas, 526 con deuda). **No queda nada por descargar**: de lo que falta, 79 períodos
> no existen en SIMEV (verificados uno por uno), 29 son archivos que el emisor no etiquetó y
> 23 son trimestrales de GRUPO_SURA que no publican estado de situación financiera.
>
> Se conserva por el método, que sirve para la próxima descarga de SIMEV: cómo está armada la
> URL, por qué la API devuelve 401 sin sesión, el bug de estado obsoleto de la SPA y la tabla
> de identificadores tipo/entidad de cada emisor.
>
> El estado final está en `db/DOCTRINA_VALOR.md` y `ESTADO_PROYECTO.md`. Lo que la sesión
> encontró, en `PROGRESO_DESCARGA_2026-09-23.txt`.

---

# Instrucción para la sesión de descarga — cerrar `deuda_financiera`

> Pégale esto completo a una sesión nueva de Claude Code abierta en
> `C:\Proyectos\novainvest`. Está escrito para alguien que llega en frío.

## Qué hay que lograr

En `fundamentales_reportados` quedan **168 de 630 filas sin `deuda_financiera`**. La fórmula de
extracción ya está corregida y verificada emisor por emisor (commits `f335367` y `897ca7b`, ver
`db/DOCTRINA_VALOR.md`). **No hay que tocar código de extracción.** Lo único que falta son
archivos fuente.

El pedido completo, fila por fila, está en `PEDIDOS_DESCARGA_DEUDA.csv`.

## Lo que ya se probó y NO funciona — no lo repitas

La API de descarga de SIMEV **exige sesión**. Comprobado el 23-sep-2026:

```
GET https://www.superfinanciera.gov.co/sfcservices/SIMEV2/descarga-archivos-niif/descarga?ruta=...&nombreArchivo=...
  -> 401
```

Devuelve 401 **todo** lo que cuelgue de `sfcservices/SIMEV2`, incluida la raíz y cualquier
variante de listado (`/listar`, `/archivos`). Así que:

- ❌ `curl`, `WebFetch` o `requests` contra esa URL: no sirve, 401.
- ❌ Construir la URL a mano: además del 401, el `nombreArchivo` lleva un **consecutivo de
  radicación** (los 10 dígitos del principio) que no es deducible; hay que leerlo de un listado.
- ✅ **Un navegador con sesión en el portal.** Preferible **Claude in Chrome** (usa el Chrome del
  usuario, con sus cookies). Si no está disponible, el navegador interno navegando el portal
  público de la Superfinanciera (`https://www.superfinanciera.gov.co/`, responde 200) hasta la
  consulta de información relevante / estados financieros NIIF.

## Prioridad — hazlo en este orden y para cuando deje de rendir

### 1. El lote 2020-T1 / T2 / T3 (58 archivos) — ESTO es lo que rinde

Es un solo lote: 20 emisores × 3 trimestres. El corpus tiene 24 archivos de 2020 contra 85–93 de
cada año siguiente: es un bache de descarga, no un problema del emisor.

**Por qué no hay atajo:** esas 66 filas existen en la base con solo 2–5 campos, tomadas del
comparativo de FLUJO de los archivos de 2021. El comparativo de BALANCE de un trimestral es el
cierre anual anterior, no el mismo trimestre — así lo exige la NIIF — así que la deuda de
marzo/junio/septiembre de 2020 **no está dentro de ningún archivo que ya tengamos**. Tampoco hay
PDF: `SIMEV_BVC` tiene cero archivos `2020-T*`.

Al bajarlos, esas 58 filas se llenan solas: la fórmula de cada uno de esos emisores ya está
verificada. No hay análisis posterior.

### 2. Los 2019-ANUAL (5 archivos)

BANCO_DE_BOGOTA, CEMENTOS_ARGOS, CONSTRUCTORA_CONCONCRETO, CORFICOLOMBIANA, GRUPO_AVAL.
Comprobado: su archivo 2020-ANUAL sí está, pero **no etiqueta la deuda en el contexto del
comparativo 2019** — solo en el del período del informe. Hace falta el 2019-ANUAL propio.

### 3. FABRICATO (8 archivos sueltos)

2018-T1, 2018-T4, 2019-T2, 2019-T3, 2020-T1, 2022-T2, 2022-T3, 2023-T1. Baratos si ya estás
dentro del portal; de bajo impacto (es el emisor más pequeño del universo).

### 4. Los informes con notas (7 PDF, era 8) — **no bajes nada, léelos en pantalla**

Esto **no cambia ninguna cifra**: solo sube el nivel de evidencia de `estructura` a `nota`. Las 7
fórmulas de nivel `estructura` ya coinciden entre sí y dan series continuas 2019–2026.

Así que lo barato es: abrir el EEFF **consolidado** en el navegador (sirve la página de Relación
con Inversionistas del emisor, no hace falta SIMEV), buscar la nota de obligaciones financieras /
préstamos / bonos del cierre 2025, y **anotar solo el total** en el reporte final. No guardes PDF
de 400 páginas.

Todas las cifras son del cierre **2025-12-31, CONSOLIDADO**, en **miles de millones de pesos**.
Si el informe viene en millones, divide por 1.000; si viene en miles, por 1.000.000.

#### El total que tiene que dar la nota

| emisor | TOTAL objetivo | corriente | no corriente | pasivos totales (para ubicarte) |
|---|---|---|---|---|
| ECOPETROL | **109.200,642** | 10.080,406 | 99.120,236 | 174.890,272 |
| ISA | **33.790,917** | 1.753,654 | 32.037,264 | 47.823,263 |
| GRUPO_NUTRESA | **16.311,566** | 909,355 | 15.402,210 | 22.002,614 |
| EXITO | **2.143,408** | 1.992,729 | 150,678 | 9.178,903 |
| EL_CONDOR | **739,132** | 194,010 | 545,122 | 1.066,658 |
| ENKA | **38,839** | 6,125 | 32,714 | 142,442 |
| FABRICATO | **136,956** | 25,291 | 111,665 | 499,263 |
| ~~GRUPO_CIBEST_BANCOLOMBIA~~ | **YA CERRADO** | | | ver abajo |

#### Lo que tiene que pasar con los bonos — esto es lo que de verdad hay que confirmar

El punto de la revisión no es el total: es **si los bonos están dentro o fuera** de la línea de
obligaciones financieras. En estos emisores la fórmula asume que están **DENTRO**, y eso es
justamente lo que no se ha podido comprobar contra una nota.

| emisor | bonos tageados en el XBRL | qué esperamos de la nota |
|---|---|---|
| ECOPETROL | 84.207,359 (corr. 5.118,399 + no corr. 79.088,960) | que los 84.207,359 estén **dentro** de los 109.200,642, no aparte. Si la nota suma préstamos + bonos y da ~193.408, la fórmula está mal |
| ISA | 28.419,074 (corr. 1.258,480 + no corr. 27.160,594) | igual: dentro de los 33.790,917. Sumarlos aparte daría 62.210, más que los pasivos totales (47.823) — imposible, que es la razón por la que creemos que van dentro |
| GRUPO_NUTRESA | no tagea bonos | la nota debería dar un solo total, sin línea de bonos aparte |
| EL_CONDOR, ENKA, FABRICATO | no tagean bonos | íd. |
| EXITO | no tagea bonos | **ojo con este**: su `ShorttermBorrowings` (26,777) NO es la porción corriente; la corriente buena es `ObligacionesFinancierasCorrientes` (1.992,729). Confirma cuál de las dos coincide con la nota |

#### GRUPO_CIBEST_BANCOLOMBIA — YA NO HACE FALTA, quedó cerrado el 24-sep-2026

Alex consiguió los EEFF consolidados de **BANCOLOMBIA S.A.** 2025 y ya están en el corpus como
`SIMEV_BVC/GRUPO_CIBEST_BANCOLOMBIA/2025-ANUAL_BANCOLOMBIA-SA_Estados-Financieros-Consolidados.pdf`.
El emisor pasó a nivel `nota` y su total corregido es **13.201,781** (antes decía 20.452,413, que
contaba los bonos dos veces).

| línea | valor | etiqueta XBRL |
|---|---|---|
| obligaciones financieras (Nota 17) + títulos de deuda emitidos (Nota 18) | 12.917,989 | `Borrowings` — **ya trae las dos** |
| operaciones de mercado monetario / repos (Nota 16) | 283,792 | `PasivosDiversos...MercadoMonetario` |
| **TOTAL** | **13.201,781** | |

El detalle de por qué, y por qué esto NO aplica a los otros tres bancos, está más abajo.

#### La hipótesis del doble conteo en CIBEST: descartada primero, CONFIRMADA después (24-sep-2026)

**Resultado: era cierta.** Lo que sigue queda como está escrito, en orden, porque el error de
razonamiento del primer intento es tan instructivo como la corrección.

##### Primer intento — descartada, con evidencia mala de un lado y generalización indebida del otro

Se propuso que el total de CIBEST cuenta los bonos dos veces, porque
`Borrowings` (12.917,989) − `TitulosEmitidos` (7.250,632) = 5.667,358, y 5.667,358 + 7.250,632
vuelve a dar 12.917,990. **Esa igualdad es trivial** — es `a − b + b = a` — así que no prueba
nada; y el 5.667,358 no sale de ninguna nota: sale de esa misma resta.

Lo que sí dice el informe de Grupo Cibest 2025: **Nota 17 Obligaciones financieras = 9.356,428**
y **Nota 18 Títulos de deuda emitidos = 7.409,693**, dos líneas separadas del balance.

La hipótesis queda refutada por una prueba aritmética que no depende de ninguna nota: **en
BANCO_DE_BOGOTA `Borrowings` (6.538,082) es MENOR que `TitulosEmitidos` (7.607,848), y en
GRUPO_AVAL (20.491,699) también es menor (21.456,986)**. Un total no puede ser más pequeño que
una de sus partes. Y en esos dos bancos está verificado al peso contra su balance que las dos
líneas son distintas y se suman. Misma taxonomía (`ec-1-bco-con-cie_entry-point`), mismas
etiquetas: `Borrowings` NO incluye los títulos emitidos.

De paso quedó cerrado por qué el informe local no sirve para verificar a CIBEST: el propio XBRL
declara `NameOfReportingEntityOrOtherMeansOfIdentification = "BANCOLOMBIA S.A."`, mientras la
serie con sufijo `-CIBEST` declara "Grupo Cibest S.A. y compañías subsidiarias". Y ninguna cifra
del XBRL (pasivos 258.775,571, depósitos 226.848,574, títulos 7.250,632) aparece en el informe de
Grupo Cibest, ni al revés. Son dos entidades, no dos versiones del mismo dato.

##### Segundo intento — con el documento correcto en mano, la hipótesis resultó cierta

Alex consiguió los **EEFF consolidados de BANCOLOMBIA S.A. 2025** (radicación
`0054371376_0001_000007_..._C-C_2025-12-31`, Total Pasivo 258.775.569, que es el perímetro del
XBRL). Con ese documento:

- **Nota 17. Obligaciones financieras = 5.667.358** (nacionales 5.192.531 + exterior 474.827).
  Es una nota real, del documento correcto, no una resta.
- **Nota 18. Títulos de deuda emitidos = 7.250.632.**
- 5.667.358 + 7.250.632 = 12.917.990 = `Borrowings` del XBRL (12.917.989).

Lo que lo cierra sin depender de esa suma —que por sí sola seguiría siendo débil— es el **desglose
de vencimientos** de las dos notas, que reproduce las DOS etiquetas del XBRL **por separado**:

| | Nota 17 | Nota 18 | suma | etiqueta XBRL |
|---|---|---|---|---|
| corto plazo 2025 | 846.756 | 1.020.053 | **1.866.809** | `ShorttermBorrowings` = 1.866.809 ✓ |
| largo plazo 2025 | 4.820.602 | 6.230.579 | **11.051.181** | `LongtermBorrowings` = 11.051.181 ✓ |
| corto plazo 2024 | 8.108.012 | 1.297.811 | **9.405.823** | `ShorttermBorrowings` = 9.405.823 ✓ |
| largo plazo 2024 | 7.581.520 | 9.977.405 | **17.558.925** | `LongtermBorrowings` = 17.558.925 ✓ |

Cuatro ecuaciones independientes, dos años, las cuatro al peso. En BANCOLOMBIA S.A. `Borrowings`
agrega las dos notas. Sumar `TitulosEmitidos` aparte contaba los bonos dos veces.

**Corregido**: la fórmula de GRUPO_CIBEST_BANCOLOMBIA pasó de `_FORMULAS_BANCA` a
`Borrowings + mercado monetario`, y de nivel `estructura` a `nota`. El total 2025 baja de
**20.452,413 a 13.201,781**.

##### Qué se aprende de haberla descartado primero

La prueba de que `Borrowings < TitulosEmitidos` en Banco de Bogotá y Grupo Aval **sigue siendo
válida**: en esos dos bancos `Borrowings` no agrega los títulos, y está verificado contra su
balance. El error fue otro: **dar por buena para el cuarto banco una fórmula verificada en tres**,
que es exactamente contra lo que advierte el resto de esta sección. Esa prueba solo funciona en un
sentido — donde `Borrowings` < `TitulosEmitidos` queda descartado que los agregue, pero donde es
mayor no concluye nada y hay que ir a la nota.

También conviene separar las dos cosas que traía la hipótesis original: su **aritmética** era
circular (`a − b + b = a`) y merecía el rechazo; su **conclusión** era correcta. Rechazar la una
no autorizaba a dar por cerrada la otra.


#### Por qué el PDF que ya hay no sirve

| emisor | problema del archivo local |
|---|---|
| ECOPETROL | el local es el Informe Integrado de Gestión (483 pág): no trae balance ni notas |
| ISA | el local es el Reporte Integrado de Gestión (149 pág), sin estados financieros |
| GRUPO_NUTRESA | el local (72 pág) no trae balance ni nota |
| EXITO, EL_CONDOR, ENKA, FABRICATO | no hay **ningún** informe suyo en `SIMEV_BVC` |
| ~~GRUPO_CIBEST_BANCOLOMBIA~~ | resuelto: ya está el de Bancolombia S.A. en el corpus |

Si alguno **no** cuadra, no toques nada: anótalo y repórtalo. Es un hallazgo, no un error a
corregir sobre la marcha.

### 5. Lo que NO vale la pena — no lo intentes

- **Los 17 XBRL trimestrales de GRUPO_CIBEST** y los 5 de CORFICOLOMBIANA, 1 de GRUPO_AVAL, 1 de
  DAVIVIENDA marcados "XBRL que no sirve": el archivo está y cierra bien, pero **el emisor no
  etiquetó la deuda en ese trimestre**. Volver a bajarlo da el mismo archivo.
- **BVC, GRUPO_SURA y la línea que le falta a DAVIVIENDA**: su XBRL no etiqueta ninguna bolsa de
  deuda. Ningún archivo arregla eso; es una decisión de carga manual que Alex tiene pendiente.
- **GRUPO_ARGOS 2026-T1**: el .xbrl que hay cierra en 2025-09-30, está mal nombrado en el corpus.
  Ese sí es re-descarga, pero es una sola fila.

## Dónde poner los archivos y cómo se llaman

Carpeta: `C:\Proyectos\BVC\SIMEV_XBRL\<EMISOR>\`
Nombre: `<AAAA>-<PERIODO>_EEFF-Consolidados-XBRL.xbrl` — p. ej. `2020-T1_EEFF-Consolidados-XBRL.xbrl`

**Solo CONSOLIDADO.** En el nombre original de SIMEV el sufijo `C-C` es consolidado y `C-I` es
individual; el lector rechaza el individual por el punto de entrada del archivo, pero es mejor no
bajarlo.

Registra cada descarga en `C:\Proyectos\BVC\SIMEV_XBRL\MANIFESTO.csv` (columnas
`emisor,archivo,fuente_origen,url_descarga,fecha_descarga`). La procedencia es obligatoria por
§5.1.4 de la doctrina; sin URL la fila queda sin trazabilidad.

## Identificadores SIMEV de cada emisor

Sacados del MANIFESTO existente. La ruta es
`//NIIF/<AAAA>/<MM>/<TIPO>/CONS/XBRL/` con `MM` = 03/06/09/12 para T1/T2/T3/ANUAL.
El campo `entidad` es el que distingue al emisor dentro del tipo (aparece en el `nombreArchivo`,
segundo y tercer campo: `<consecutivo>_<TIPO>_<ENTIDAD>_...`).

| emisor | tipo | entidad | períodos que faltan |
|---|---|---|---|
| BANCO_DE_BOGOTA | 0001 | 000001 | 2019-ANUAL, 2020-T1, 2020-T2, 2020-T3 |
| CELSIA | 0066 | 000061 | 2020-T1, 2020-T2, 2020-T3 |
| CEMENTOS_ARGOS | 0043 | 000005 | 2019-ANUAL, 2020-T1, 2020-T2, 2020-T3 |
| CONSTRUCTORA_CONCONCRETO | 0055 | 000003 | 2019-ANUAL, 2020-T1, 2020-T2, 2020-T3 |
| CORFICOLOMBIANA | 0002 | 000011 | 2019-ANUAL, 2020-T1, 2020-T2, 2020-T3 |
| DAVIVIENDA_GROUP | 0066 | 000068 | 2025-T2 |
| ECOPETROL | 0260 | 000036 | 2020-T1, 2020-T2, 2020-T3 |
| EL_CONDOR | 0056 | 000008 | 2020-T1, 2020-T2, 2020-T3 |
| ENKA | 0039 | 000021 | 2020-T1, 2020-T2, 2020-T3 |
| ETB | 0260 | 000047 | 2020-T1, 2020-T2, 2020-T3 |
| EXITO | 0058 | 000006 | 2020-T1, 2020-T2, 2020-T3 |
| FABRICATO | 0034 | 000004 | 2018-T1, 2018-T4, 2019-T2, 2019-T3, 2020-T1, 2022-T2, 2022-T3, 2023-T1 |
| GEB | 0260 | 000043 | 2020-T1, 2020-T2, 2020-T3 |
| GRUPO_ARGOS | 0066 | 000058 | 2020-T1, 2020-T2, 2020-T3 |
| GRUPO_AVAL | 0142 | 000001 | 2019-ANUAL, 2020-T1, 2020-T2, 2020-T3 |
| GRUPO_CIBEST_BANCOLOMBIA | 0001 | 000007 | 2020-T1, 2020-T2, 2020-T3 |
| GRUPO_NUTRESA | 0066 | 000032 | 2020-T1, 2020-T2, 2020-T3 |
| ISA | 0260 | 000034 | 2020-T1, 2020-T2, 2020-T3 |
| MINEROS | 0030 | 000003 | 2020-T1, 2020-T2, 2020-T3 |
| PROMIGAS | 0261 | 000004 | 2020-T1, 2020-T2, 2020-T3 |
| TERPEL | 0053 | 000022 | 2020-T1, 2020-T2, 2020-T3 |

Ojo: el `tipo` NO identifica al emisor — 0066 lo comparten Celsia, Davivienda, Grupo Argos y
Nutresa; 0260 lo comparten Ecopetrol, ETB, GEB e ISA. Dentro de una carpeta de SIMEV vas a ver
archivos de varios emisores: el que sirve es el que trae `_<TIPO>_<ENTIDAD>_` según la tabla.

## Cuando termines de bajar

```bash
cd C:/Proyectos/novainvest && python jobs/extraer_xbrl.py --dry-run
```

Si no reporta errores nuevos, córrelo de verdad (sin `--dry-run`) y después:

```bash
cd C:/Proyectos/novainvest && python jobs/analizador_fundamental.py
```

Verificación final — cuántas filas quedaron sin deuda (eran 168):

```bash
cd C:/Proyectos/novainvest/apps/api && python -c "import sys; sys.path.insert(0,'.'); from app.database import cliente_servicio; f=cliente_servicio().table('fundamentales_reportados').select('deuda_financiera').execute().data; print(sum(1 for x in f if x['deuda_financiera'] in (None,0,0.0)), 'de', len(f))"
```

Y corre las pruebas, que llevan las cifras de las notas ya verificadas:

```bash
cd C:/Proyectos/novainvest && python jobs/test_lector_xbrl.py
```

**Si alguna prueba falla, para y repórtalo.** Significa que algo del reprocesado movió una cifra
que ya estaba cuadrada contra el informe del emisor.

## Qué reportar al final

1. Cuántos archivos bajaste y cuántas filas ganaron deuda (el número de la verificación de arriba).
2. Los totales que leíste de las notas de los 8 informes, y si cuadraron o no con la tabla.
3. Cualquier emisor/período que no encontraste en SIMEV, con el mensaje exacto del portal.

No hagas merge ni push. Deja la rama lista para que Alex la revise.
