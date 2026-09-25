# Traspaso — `deuda_financiera` en NOVAINVEST

> Estado al 25-sep-2026. Documento autocontenido: se puede leer sin haber visto la sesión
> anterior. Si vas a seguir con esto, **lee primero la sección "Antes de tocar nada"**.

---

## 1. La respuesta corta

**El trabajo de fondo está hecho.** 14 de 24 emisores tenían la deuda mal o en cero y quedaron
corregidos contra la nota de su propio informe. Eso **cambió el signo del EVA en tres emisores**,
que es un cambio de conclusión de inversión, no un ajuste cosmético.

**Lo que no avanza es el último 20 % de cobertura**, y ahí es donde se han ido las últimas
rondas. No es un atasco por dificultad: es que **lo que queda no tiene fuente**. Ver §4.

| | al empezar | hoy |
|---|---|---|
| filas con deuda | 349 de 630 (55,4 %) | **543 de 677 (80,2 %)** |
| emisores verificados contra su nota | 0 | **20 de 23** |

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

**134 filas sin deuda.** Repartidas así:

| causa | filas | ¿se puede arreglar? |
|---|---|---|
| el período **no existe en SIMEV** | 78 | **No.** Verificado uno por uno |
| hay XBRL pero **el emisor no etiquetó** la deuda ese trimestre | 33 | **No.** Volver a bajarlo da el mismo archivo |
| trimestrales de GRUPO_SURA **sin estado de situación financiera** | 23 | **No.** Su informe trimestral no trae balance |

Y por antigüedad: **81 son de 2020 o antes**, 34 de 2021-2023, y **solo 19 de 2024-2026**. El
análisis usa el último saldo y el TTM, así que **los huecos viejos no afectan ninguna conclusión
actual** — solo las series históricas y los backtests.

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

## 7. Dónde está cada cosa

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

Para reprocesar después de agregar XBRL:

```bash
cd C:/Proyectos/novainvest && python jobs/extraer_xbrl.py --dry-run
```

luego sin `--dry-run`, después `python jobs/analizador_fundamental.py`, y **siempre**
`python jobs/test_lector_xbrl.py` — si alguna prueba falla, algo movió una cifra ya verificada
contra el informe de un emisor.
