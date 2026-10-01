# Traspaso — `deuda_financiera` en NOVAINVEST

> Estado al 25-sep-2026 (actualizado más tarde el mismo día, ver §7). Documento autocontenido:
> se puede leer sin haber visto la sesión anterior. Si vas a seguir con esto, **lee primero la
> sección "Antes de tocar nada"**.

---

## 1. La respuesta corta

**El trabajo de fondo está hecho.** 14 de 24 emisores tenían la deuda mal o en cero y quedaron
corregidos contra la nota de su propio informe. Eso **cambió el signo del EVA en tres emisores**,
que es un cambio de conclusión de inversión, no un ajuste cosmético.

**Actualización del mismo día (§7): la cobertura de GRUPO_SURA que este documento daba por
estructuralmente cerrada NO lo estaba.** 13 de sus 23 huecos se llenaron en la misma sesión con
archivos que ya estaban en el corpus — el diagnóstico original ("su informe trimestral no trae
balance") era incorrecto para esos 13. Ver §7 antes de asumir que el §4 de abajo sigue vigente
tal cual para GRUPO_SURA.

| | al empezar | tras la sesión original | tras §7 (mismo día) |
|---|---|---|---|
| filas con deuda | 349 de 630 (55,4 %) | 543 de 677 (80,2 %) | **556 de 677 (82,1 %)** |
| emisores verificados contra su nota | 0 | 20 de 23 | **20 de 23** (GRUPO_SURA ahora bien parcialmente, no en 0) |

---

## 2. Lo que cambió, emisor por emisor

Todas las cifras en miles de millones de pesos (MMM).

| emisor | deuda antes | deuda hoy | EVA antes | EVA hoy |
|---|---|---|---|---|
| **GEB** | 972 | **19.486** | −935 | **−2.806** |
| **GRUPO_AVAL** | 19.999 | **70.424** | −1.199 | −1.184 |
| **GRUPO_NUTRESA** | 0 | **16.440** | **+726** | **−1.034** |
| **BANCO_DE_BOGOTA** | 5.663 | **17.949** | −857 | −857 |
| **CORFICOLOMBIANA** | 12.204 | **26.649** | −1.545 | −1.533 |
| **GRUPO_SURA** | 0 | **11.050** | −4.195 | −4.944 |
| **PROMIGAS** | 0 | **5.558** | **+285** | **−235** |
| **TERPEL** | 0 | **3.702** | +499 | +158 |
| **CEMENTOS_ARGOS** | 0 | **2.757** | −878 | −1.178 |
| DAVIVIENDA_GROUP | 9.042 | 15.437 | −1.542 | −1.459 |
| GRUPO_CIBEST | 12.918 | 13.202 | −393 | −354 |
| MINEROS | 9 | 192 | +516 | +492 |
| EXITO | 2.143 | 1.748 | −281 | −243 |
| PEI | (16 huecos) | serie completa 25/25 | — | — |

**Los tres que cambiaron de signo — NUTRESA, PROMIGAS y TERPEL (este se acercó a cero)— aparecían
como creadores de valor sólo porque su deuda estaba en cero.** No lo son.

---

## 3. Antes de tocar nada: las cinco trampas que ya se pisaron

Cada una costó una ronda entera. Están documentadas en detalle en `db/DOCTRINA_VALOR.md`.

1. **No existe un mapeo genérico de `deuda_financiera`.** Cada preparador de XBRL mete cosas
   distintas en las mismas etiquetas. Hay una fórmula por emisor en
   `DEUDA_FINANCIERA_POR_EMISOR` (`apps/api/app/services/extraccion/lector_xbrl.py`), cada una con
   su nivel de evidencia. **No la "simplifiques".**

2. **Verificar el cierre más reciente contra la nota NO basta.** ETB reproduce su Nota 17 al peso
   en 2025 con `Borrowings`, y esa misma etiqueta da 12,5 en 2019-T1 cuando el real es 542,7. Hay
   que mirar **la serie completa** de cada emisor.

3. **Ni dentro de un mismo sector se puede generalizar.** Se usó una fórmula única para los 4
   bancos habiéndola verificado en 3, y el cuarto (Bancolombia) era el contraejemplo: allí
   `Borrowings` ya agrega los títulos emitidos y sumarlos aparte los contaba dos veces.

4. **`C-I` en el nombre de SIMEV no es "individual"**, es consolidado **INTermedio** (trimestral),
   frente a `C-C` = consolidado de **CIErre**. Los dos sirven. Casi se descartan 16 archivos
   buenos por leer mal esa letra.

5. **Un reproceso borraba las cargas manuales.** `extraer_xbrl.py` no fusionaba las filas con
   `metodo_validacion='manual'`, así que las reemplazaba con el `None` del XBRL — sin dar error.
   Ya está corregido, pero **si vuelves a tocar esa fusión, vuelve a mirarlo**.

---

## 4. Lo que queda, y por qué casi nada vale la pena

**Esta sección describe el estado ANTES de §7. Para GRUPO_SURA, la fila de "sin estado de
situación financiera" de la tabla de abajo estaba mal diagnosticada — ver §7.** Se deja tal cual
se escribió porque el resto (78 + 33) sigue vigente y verificado.

**134 filas sin deuda** (121 después de §7). Repartidas así:

| causa | filas | ¿se puede arreglar? |
|---|---|---|
| el período **no existe en SIMEV** | 78 | **No.** Verificado uno por uno |
| hay XBRL pero **el emisor no etiquetó** la deuda ese trimestre | 33 | **No.** Volver a bajarlo da el mismo archivo |
| trimestrales de GRUPO_SURA "sin estado de situación financiera" | ~~23~~ **10** | **Estaba mal.** 13 de los 23 SÍ tenían balance (páginas escaneadas, canal B) — corregido en §7. Los 10 que quedan (2019-ANUAL, 2020/2021/2022 T1-T3) sí carecen de archivo local |

Y por antigüedad: **81 son de 2020 o antes**, 34 de 2021-2023, y **solo 19 de 2024-2026**. El
análisis usa el último saldo y el TTM, así que **los huecos viejos no afectan ninguna conclusión
actual** — salvo la excepción real que sí importaba: antes de §7, el "último saldo" de GRUPO_SURA
caía en 2025-T3 porque 2025-T4/2026-T1/2026-T2 estaban vacíos — es decir, el emisor SÍ tenía un
hueco en su dato más reciente, no solo en la historia vieja. Ya está cerrado.

### Lo único con pista concreta

**CELSIA en tipo 0066 / entidad 000061.** La sesión de descarga buscó Celsia en
`tipo=261/entidad=026`, que es **EPSA E.S.P., la filial** (activos 6.189 MMM contra los
11.378-12.590 de Celsia). Así que sus conclusiones sobre 2019-T1, 2019-T2, 2019-T3 y 2020-T2 **no
valen**: hay que rehacerlas en la entidad correcta. Son 4 filas de 2019-2020, de impacto bajo.

Todo el detalle de qué se verificó y qué no está en `VERIFICAR_EN_SIMEV.csv`, con el `tipo` y
`entidad` de cada emisor y la URL de consulta.

---

## 5. Dudas abiertas, por si alguien quiere cerrarlas

Ninguna es urgente. Están en orden de cuánto rinde resolverlas.

1. **Zigzag ANUAL-vs-trimestres en ETB y ENKA.** Sus cierres anuales no cuadran con sus propios
   trimestres (ETB 2019-ANUAL 362,1 contra ~541 en T1/T2/T3; 2021-ANUAL 530,3 contra ~361). Puede
   ser amortización real de diciembre o un artefacto de etiquetado. Son los dos emisores más
   pequeños del universo (EV 1.381 y 262).

2. **DAVIVIENDA está incompleta a propósito.** Su cifra completa 2025 sería 28.907 (créditos
   16.144 + instrumentos de deuda emitidos 12.764), pero solo 2 de sus 7 períodos tienen informe
   local parseable: completar esos dos rompería la serie. Está marcada `nota_parcial`. Si aparece
   el resto de sus informes, se puede cerrar.

3. **GRUPO_CIBEST sigue en nivel `estructura`** para los trimestres: su XBRL trimestral solo
   etiqueta `TitulosEmitidos`, sin las bolsas de créditos. El ANUAL sí está verificado contra los
   EEFF de Bancolombia S.A.

4. **`extractor_xlsx.py` escribe `deuda_financiera` sumando dos etiquetas de texto fijas** — el
   mapeo genérico que toda la §3.1 desaconseja. Hoy solo produjo un dato (ETB 2019-T3, marcado
   `provisional`) y coincide con la fórmula verificada de ETB. **Antes de usar ese canal en más
   emisores, hay que darle el mismo tratamiento por emisor que tiene el canal XBRL.**

---

## 6. Recomendación

**Dar el trabajo por cerrado y no perseguir el 20 % restante.** El valor ya se capturó: los
emisores cuya deuda estaba mal o en cero están corregidos y verificados contra sus notas, y eso
cambió conclusiones reales de inversión. Lo que queda son huecos sin fuente, en su mayoría de
2020 o antes, que no afectan ninguna decisión.

Si aun así se quiere seguir, el orden por rendimiento es: **(1)** CELSIA en la entidad correcta,
**(2)** la duda del zigzag de ETB/ENKA, **(3)** el resto. Ninguna de las tres mueve una decisión
de inversión.

---

## 7. Corrección — 13 de los 23 huecos de GRUPO_SURA sí tenían balance (25-sep-2026, misma tarde)

Alex pidió revisar si había forma de acercar esto al 100 %. Antes de tocar nada se verificaron
los tres números de §1/§4 contra Supabase en vivo — coinciden exactos (543/677, el desglose por
causa y por antigüedad también). El documento no estaba desactualizado. El error estaba en el
diagnóstico de una de las tres causas.

**La fila "GRUPO_SURA sin estado de situación financiera" (23) estaba mal explicada.** Revisando
`fundamentales_reportados` fila por fila: 18 de esos 23 SÍ tenían `activos_totales`,
`pasivos_totales` y `patrimonio` cargados (varios vía XBRL, otros vía la lectura visual de
`db/CANAL_B_GRUPO_SURA_STAGING.md`) — si el balance no existiera, esos campos también estarían
vacíos. La razón real, ya documentada en `DEUDA_FINANCIERA_POR_EMISOR["GRUPO_SURA"]`
(`lector_xbrl.py`): **el XBRL consolidado de SURA nunca etiqueta la deuda**, a propósito, así que
esa columna sale vacía por diseño — pero la cifra sí está en el balance del PDF (línea
"Obligaciones financieras" + línea "Bonos emitidos"), sin necesidad de nota aparte. Ya se había
hecho esta lectura para 6 períodos (2023/2024/2025-ANUAL, 2025-T1/T2/T3). Para los otros 18 nadie
había repetido el ejercicio — `jobs/cargar_staging_sura_canal_b.py` cargó activos/pasivos/
patrimonio pero nunca tocó la línea de deuda.

**De esos 18, 13 tenían el PDF fuente ya descargado en `SIMEV_BVC/GRUPO_SURA/`** (los otros 5 —
2021 completo y 2022-T1/T2/T3 — no tienen archivo local, son huecos reales de descarga). Las
páginas del Estado de Situación Financiera Consolidado en estos informes trimestrales son
**imágenes escaneadas sin capa de texto** (por eso ningún `grep`/regex las encontró antes — el
mismo patrón de bug #1 de `db/DOCTRINA_VALOR.md`, "residuo de texto real en el pie de página").
Se renderizaron a imagen (`pdfplumber.to_image()`) y se leyeron visualmente, canal B, el mismo
método que ya usa el proyecto para GRUPO_SURA y PEI.

**Bono inesperado**: el informe 2022-ANUAL trae en sus columnas comparativas el cierre de
2020 ("1 de enero de 2021 Re-expresado") y de 2021 ("Diciembre 2021 Re-expresado") — dos períodos
más, de un solo documento, sin necesitar archivo propio.

**Cada cifra se verificó cruzando el `activos_totales` de la imagen contra el valor YA cargado
en Supabase — coincidieron exactos en los 13, 0 discrepancias**, y dos de los trece coinciden
además al peso con un período hermano ya cargado por otro canal (2023-T4 = 2023-ANUAL =
9.784,262; 2025-T4 = 2025-ANUAL = 11.049,958, misma fecha de corte, dos filas separadas en la
tabla).

| período | Obligaciones financieras + Bonos emitidos (MMM) | fuente |
|---|---:|---|
| 2020-ANUAL | 10.267,702 | comparativo en 2022-ANUAL, pág. 116 |
| 2021-ANUAL | 9.587,228 | comparativo en 2022-ANUAL, pág. 116 |
| 2022-ANUAL | 10.453,457 | 2022-ANUAL, pág. 116 |
| 2023-T1 | 10.328,234 | 2023-T1, pág. 58 |
| 2023-T2 | 9.434,168 | 2023-T2, pág. 52 |
| 2023-T3 | 9.679,796 | 2023-T3, pág. 51 |
| 2023-T4 | 9.784,262 | 2023-T4, pág. 42 (= 2023-ANUAL) |
| 2024-T1 | 10.044,907 | 2024-T1, pág. 46 |
| 2024-T2 | 10.935,419 | 2024-T2, pág. 9 |
| 2024-T3 | 11.269,524 | 2024-T3, pág. 9 |
| 2025-T4 | 11.049,958 | 2025-T4, pág. 26 (= 2025-ANUAL) |
| 2026-T1 | 11.422,601 | 2026-T1, pág. 37 |
| 2026-T2 | 10.613,167 | 2026-T2, pág. 38 |

Cargado con `jobs/cargar_deuda_sura_canal_b2.py` (deja el script y el razonamiento documentado
para la próxima vez). `python jobs/test_lector_xbrl.py` sigue pasando completo.
`python jobs/analizador_fundamental.py` corrido de nuevo: sin errores nuevos, y el "último saldo"
de GRUPO_SURA que usa el motor de valor pasó de 2025-T3 (11.284,865, un dato de hace un año) a
**2026-T2 (10.613,167, el trimestre más reciente que existe)** — esto sí movía la cifra que
alimenta el EVA/ROIC actual de uno de los 5 holdings del MVP W3a, no solo una serie histórica.

**Resultado**: 543 → **556 de 677 (82,1 %)**. GRUPO_SURA pasó de 6/29 a **19/29 (65,5 %)**.

**Lo que sigue sin tener arreglo** (121 filas, verificado que la causa no cambió para las otras
dos categorías): los 78 períodos que no existen en SIMEV, los 33 que el emisor no etiquetó, y
ahora **10** de GRUPO_SURA (2019-ANUAL, 2020 completo, 2021 completo, 2022-T1/T2/T3) — estos sí
son huecos de descarga genuinos, sin PDF local, mismo patrón que el resto del universo.

**No se tocó CELSIA en esta pasada** (2019-T1/T3, §4 punto 1 de arriba): se confirmó que
tampoco tienen archivo local (`SIMEV_BVC/CELSIA/` solo tiene 2019-ANUAL y 2019-T2), así que
requieren una sesión de descarga con navegador autenticado (mismo método de
`INSTRUCCION_SESION_DESCARGA_DEUDA.md`), no lectura de un archivo que ya esté en el corpus. Bajo
impacto (2 filas de 2019), no se persiguió.

**Lección para la próxima sesión que toque cobertura**: antes de aceptar "no se puede arreglar"
para un emisor, comprobar si `activos_totales`/`pasivos_totales` ya están cargados en esa fila —
si lo están, el balance existe y el hueco es de una línea puntual (deuda, en este caso), no del
documento completo. La sesión original de este documento no hizo esa comprobación fila por fila
para GRUPO_SURA, solo revisó la causa a nivel de emisor.

---

## 8. Dónde está cada cosa

| qué | dónde |
|---|---|
| la tabla de fórmulas por emisor | `apps/api/app/services/extraccion/lector_xbrl.py`, `DEUDA_FINANCIERA_POR_EMISOR` |
| el razonamiento completo, con las trampas | `db/DOCTRINA_VALOR.md` |
| el diario de la sesión | `ESTADO_PROYECTO.md` |
| pruebas con las cifras de las notas | `jobs/test_lector_xbrl.py` |
| qué se verificó en SIMEV y qué no | `VERIFICAR_EN_SIMEV.csv` |
| el informe de la sesión de descarga | `PROGRESO_DESCARGA_2026-09-23.txt` (ojo: su párrafo sobre CIBEST quedó superado, tiene una nota al final) |
| la instrucción de descarga | `INSTRUCCION_SESION_DESCARGA_DEUDA.md` — **operación cerrada**, se conserva por el método |
| archivos descartados y por qué | `C:\Proyectos\BVC\_descartados\LEEME.txt` |
| los 13 períodos de deuda de GRUPO_SURA leídos por canal B (§7) | `jobs/cargar_deuda_sura_canal_b2.py` |

Para reprocesar después de agregar XBRL:

```bash
cd C:/Proyectos/novainvest && python jobs/extraer_xbrl.py --dry-run
```

luego sin `--dry-run`, después `python jobs/analizador_fundamental.py`, y **siempre**
`python jobs/test_lector_xbrl.py` — si alguna prueba falla, algo movió una cifra ya verificada
contra el informe de un emisor.
