# Informe de obstáculos — motor de extracción de fundamentales (F4a)

Fecha: 03-sep-2026. Alcance: lo encontrado construyendo y probando la extracción de
ECOPETROL (2 plantillas, 4 periodos consolidados verificados). Este documento es para
retomar el trabajo en otra sesión sin repetir el mismo camino — no repite lo que ya
funciona (ver `ESTADO_PROYECTO.md` para eso), se concentra en **lo que costó tiempo, por
qué, y cómo quedó resuelto o qué falta**.

---

## 1. Un PDF venía protegido y era ilegible por cualquier herramienta

`ECOPETROL/2026-T1_Informe-Periodico-Trimestral.pdf` (la primera versión descargada)
estaba envuelto en Microsoft Information Protection / Azure Rights Management: al abrirlo
con `pypdf`/`pdfplumber` solo aparece una página de aviso ("use un visor compatible con
Azure RMS"), sin acceso al contenido real — no es un problema de la herramienta, es
cifrado genuino a nivel de documento.

- **Alcance real:** 1 de 409 archivos del corpus completo (se escaneó todo).
- **Resuelto:** Alex lo volvió a descargar directo del SIMEV público y quedó legible.
- **Para la próxima vez:** el pipeline debe seguir detectando este caso (buscar la firma
  "Information Protection"/"Rights Management" en el texto de la página 1) y marcarlo
  `irrecuperable` en `reportes_archivo` en vez de fallar sin explicación — la detección ya
  existe como chequeo manual, falta automatizarla dentro de `ingesta_simev.py`.

## 2. El detector de tablas por defecto de `pdfplumber` no sirve para estos PDF

Con la configuración por defecto (detección de tablas por líneas dibujadas), `pdfplumber`
devuelve fragmentos de una sola fila por tabla en vez de la tabla completa — los PDF de
resultados trimestrales casi nunca dibujan líneas de cuadrícula completas, usan sombreado
alterno de fondo en su lugar.

- **Solución encontrada:** `extract_table({'vertical_strategy': 'text',
  'horizontal_strategy': 'text'})` reconstruye las columnas por posición del texto en vez
  de por líneas dibujadas. Funciona, pero con dos efectos secundarios (ver puntos 3 y 4).

## 3. Una etiqueta de fila queda partida en 2 a 4 celdas

Con la estrategia de texto, `pdfplumber` corta "Utilidad operacional" en celdas como
`['Utilidad operacion', 'al']`, o "Utilidad neta atribuible a accionistas" en 4-5
fragmentos. No es aleatorio pero tampoco es predecible por posición fija.

- **Solución:** concatenar todas las celdas de texto de la fila antes de comparar contra
  la etiqueta buscada, y comparar **sin espacios ni acentos** (`normalizar()` en
  `pdf_utils.py`) — así la fragmentación deja de importar.

## 4. Un número partido entre celdas es indistinguible de dos números distintos y adyacentes

Ejemplo real: la fila de "Efectivo neto generado por las actividades de operación" trae
`['6,', '122', '6,015']` — el primer valor (6,122) está partido en dos celdas, pero el
segundo valor (6,015) es una celda aparte, sin ninguna celda vacía de por medio que marque
el límite. Concatenar todo a ciegas produce "6,1226,015", un solo número basura.

- **Solución:** heurística de "número bien formado" — una celda numérica que termina en
  coma/paréntesis abierto/guion se considera incompleta y sigue acumulando con la
  siguiente; en cuanto el acumulado coincide con el patrón de un número completo
  (`-?\(?\d{1,3}(,\d{3})*(\.\d+)?%?\)?`), se cierra ese valor y empieza el siguiente.
  Probado y funciona en los casos reales encontrados, pero es una heurística, no una
  garantía — un caso no visto todavía podría romperla.

## 5. Buscar una etiqueta "por contiene" es peligroso — hace falta igualdad exacta

Dos formas reales de que esto salga mal:
- Un párrafo narrativo que menciona "...generó un EBITDA de COP 13.3 billones..." se
  confunde con la fila real de la tabla llamada "EBITDA" si se busca por subcadena.
- "Total activos" es subcadena literal de "Total activos corrientes" (un subtotal
  distinto) — buscar por "contiene" agarra el subtotal equivocado.

- **Solución:** `buscar_fila`/`buscar_valor_en_texto` exigen **igualdad exacta** de la
  etiqueta ya normalizada, nunca "contiene". Resolvió ambos casos reales encontrados.

## 6. Bug puntual de renderizado: "Total" pierde sus dos primeras letras

En la tabla de balance de ECOPETROL específicamente (no en otras tablas del mismo
documento), toda fila que empieza con "Total" en negrita llega como "tal" ("tal activos",
"tal pasivos", "tal patrimoni"+"o") — probablemente un problema de medición de ancho de
carácter en negrita que descarta el "To" inicial. No se reprodujo en otras tablas.

- **Solución:** se agregaron ambas variantes ("total activos" y "tal activos", etc.) como
  alternativas válidas de búsqueda. Es un parche puntual — si aparece en otro emisor habrá
  que repetirlo o generalizar la detección.

## 7. El mismo emisor cambia de formato de reporte varias veces, y no limpio por año

Esto fue el hallazgo más caro en tiempo. Se asumió inicialmente (como hipótesis de
trabajo, no como hecho verificado) que el formato de Ecopetrol cambiaría de forma estable
por rango de fechas ("vigente_desde"). La realidad, verificada contra los 20 reportes
reales disponibles:

| Periodo | Formato real |
|---|---|
| 2022, 2023, 2024 completos, 2025-T2, 2025-T3, 2025-ANUAL, 2026-T2 | Narrativo por secciones numeradas (1. Mensaje del Presidente... 5. Resultados Financieros) |
| 2025-T1, 2026-T1 | Tabla resumen "Tabla 1: Resumen Financiero" (infografía con tablas numeradas) |

**2025-T1 y 2025-T2 tienen formatos distintos, dentro del mismo año.** La columna
`vigente_desde` de `plantillas_extraccion` sirve para *no intentarlo* en años claramente
anteriores, pero no garantiza que todo lo posterior comparta formato. Cada intento de
extracción debe seguir verificando si encontró su tabla ancla, y marcar
`requiere_revision` si no — nunca asumir que "cae en el rango, entonces debe funcionar".

**Implicación para CIBEST y SURA:** hay que verificar esto mismo para cada uno antes de
asumir que una sola plantilla cubre todo su rango de fechas.

## 8. El formato narrativo, pese a llamarse "Informe Periódico Trimestral", no trae cifras

Se abrió varios ejemplares del formato narrativo (2023-T2, 2024-T2) esperando encontrar
las cifras en prosa en algún lado. En cambio, el documento dice explícitamente: *"La
información relacionada con los resultados financieros... fue reportada... en el Sistema
Integral de Información del Mercado de Valores: SIMEV"* y remite a la página web de
Ecopetrol para los estados financieros. Es decir: **el documento delibera y
deliberadamente no repite las cifras**, para evitar duplicarlas con lo que ya se radicó
en SIMEV como un archivo separado.

- **Consecuencia:** para los años con este formato, no hay forma de obtener las cifras del
  informe periódico mismo, sin importar cuánto se mejore el parser — el dato
  simplemente no está en ese documento.

## 9. Las cifras reales de esos años sí existen, pero en un tercer tipo de documento

`EEFF-Consolidados` (`tipo_documento = 'estados_financieros'`) sí trae los tres estados
financieros completos (situación financiera, ganancias y pérdidas, flujos de efectivo), en
**texto plano línea por línea** — una estructura totalmente distinta a la de tabla
reconstruida de los puntos 2-4, y que exigió una técnica de extracción nueva
(`buscar_valor_en_texto`/`separar_etiqueta_y_valores_linea`, sin pasar por
`extract_table` en absoluto).

- Encontrar esto tomó abrir el documento completo (138 páginas) y buscar manualmente,
  porque el nombre del archivo no anticipa qué tan limpia viene la estructura interna.

## 10. La tabla de contenido de un documento largo hace fallar la búsqueda de páginas por palabra clave

`localizar_pagina` (busca la primera página cuyo texto contiene cierta frase) encontraba
la **tabla de contenido** en vez de la página real, porque el título de cada estado
financiero también aparece ahí como entrada de índice — y la tabla de contenido siempre
sale primero en el documento.

- **Solución:** se agregó un parámetro `posicion_maxima` — el texto ancla debe aparecer
  dentro de los primeros N caracteres de la página (justo después del encabezado fijo
  "Ecopetrol S.A. / Cifras expresadas..."), no en cualquier parte. La tabla de contenido
  tiene mucho texto antes de cada título, así que queda descartada.
- **Para la próxima vez:** cualquier documento largo (100+ páginas) con tabla de
  contenido va a tener este mismo problema — aplicar `posicion_maxima` por defecto en
  documentos largos, no solo cuando falla.

## 11. Referencias de nota al pie pegadas al final de la etiqueta

En los EEFF-Consolidados, cada línea trae el número de nota antes de la cifra:
"Efectivo y equivalentes de efectivo 6 12,336,115 15,401,058". Al principio solo se
contempló un solo dígito al final (`\s+\d{1,3}$`); una línea real trae una referencia
compuesta ("Depreciación, agotamiento y amortización 13-14-15-16 ...") que ese patrón no
capturaba, dejando la etiqueta contaminada y sin poder hacer match exacto.

- **Solución:** el patrón se amplió a `\s+[\d]{1,3}(-\d{1,3})*$` (uno o más números
  separados por guion). Puede seguir habiendo variantes no vistas (ej. notas separadas
  por coma en vez de guion) — si una etiqueta no matchea y se sospecha esto, revisar el
  texto crudo de la línea antes de asumir que la cifra no está.

## 12. El mismo concepto contable aparece dos veces en la misma tabla

"Préstamos y financiaciones" aparece una vez en pasivo corriente y otra en pasivo no
corriente — para calcular deuda financiera total hay que sumar **ambas** ocurrencias, no
quedarse con la primera que encuentra la búsqueda.

- **Resuelto** puntualmente para este caso en `plantilla_ecopetrol_eeff_anual.py`. Al
  construir CIBEST/SURA, revisar si hay otros conceptos con el mismo patrón (ej.
  provisiones, otros pasivos) antes de asumir que una sola ocurrencia basta.

## 13. Un PDF "Firmado" resultó ser un escaneo desde cierta página

`2024-ANUAL_EEFF-Consolidados-Firmados.pdf` tiene texto extraíble normal en las primeras
~10 páginas (informe del revisor fiscal, tabla de contenido) pero **texto vacío desde la
página 11 en adelante** — exactamente donde deberían estar los estados financieros. Es
casi seguro un documento impreso, firmado a mano, y vuelto a escanear para esa versión
"Firmados" en particular.

- **No resuelto — requiere OCR** (ej. `pytesseract` + preprocesamiento de imagen), una
  capacidad que el pipeline no tiene todavía. Queda marcado `SIN_TABLAS_RECONOCIDAS` en
  vez de forzarse.
- **Alternativa más barata que OCR:** preguntarle a Alex si en SIMEV existe una versión NO
  firmada/escaneada del EEFF-Consolidados 2024 (a veces existen ambas) — evitaría construir
  OCR para un solo archivo.

## 14. EBITDA no es una línea de los estados financieros auditados

Al ser una métrica no-NIIF, `EEFF-Consolidados` no la reporta directamente — se deriva
como `resultado de la operación + depreciación, agotamiento y amortización` (tomada del
estado de flujo de efectivo). Es una aproximación razonable pero **no es el número exacto
que la empresa reporta en sus propios comunicados** (que puede incluir ajustes
adicionales) — al hacer doble extracción contra el subagente, esta línea derivada
probablemente va a mostrar más discrepancia que las demás y quizás necesite una tolerancia
distinta, o aceptar que para años con esta fuente el EBITDA queda con menor confianza que
el resto de campos.

## 15. Tensión de diseño no resuelta: el comunicado de prensa es a veces la única fuente con cifras

Para trimestres donde el informe periódico es narrativo (sin cifras) y no hay un
`EEFF-Consolidados` trimestral disponible (solo existen para ANUAL), la única fuente con
números es el `Comunicado-Resultados` — que el plan clasifica explícitamente como
precedencia baja ("nunca fuente de un número", solo contexto). Ejemplo concreto:
2023-T1/T2/T3 no tienen ninguna otra fuente descargada con cifras.

- **No se resolvió esta sesión.** Dos caminos posibles para la próxima:
  1. Aceptar el hueco (esos trimestres quedan `historial insuficiente` hasta que Alex
     descargue algo mejor de SIMEV, si existe).
  2. Definir una excepción explícita y documentada: permitir extraer de comunicados
     **solo** cuando no exista ninguna otra fuente para ese periodo, marcando
     `metodo_validacion` de forma que quede clarísimo que la cifra viene de una fuente de
     menor confianza (nunca mezclado con el mismo estado que una cifra de EEFF).
  - Esto es una decisión de producto, no solo técnica — vale la pena que Alex la tome
    explícitamente antes de construirla.

## 16. Cobertura actual: 1 de 3 emisores piloto, 2 de N formatos de ese emisor

Todo lo anterior es **solo de ECOPETROL**. CIBEST (formato de banco, con Estado de
Situación Financiera / Estado de Resultados en páginas fijas del índice, Consolidado vs
Separado en la misma tabla) y SURA (infografía + sección de EEFF aparte en un reporte de
60+ páginas, holding con consolidado vs individual) tienen reconocimiento hecho pero
**ninguna plantilla construida todavía** — es razonable esperar que cada uno traiga sus
propios obstáculos de esta misma familia (formato que cambia en el tiempo, tablas que se
fragmentan distinto, subtotales que colisionan con totales, etc.), no una lista distinta
de problemas nuevos.

## 17. Nota de rendimiento (no bloqueante, pero afecta cómo se corre)

Los `EEFF-Consolidados` son documentos de 100-150 páginas; escanear página por página en
busca de un texto ancla (una vez por cada uno de los 3 estados financieros) tarda uno o
dos minutos por archivo. No es un problema de diseño, pero al escalar a CIBEST/SURA y al
resto de los ~500-700 PDF del universo comprometido, correr esto en serie sobre todo el
lote histórico puede tardar horas — considerar correrlo en lotes nocturnos como ya prevé
el plan (§5.1.2), no como una corrida interactiva.

---

## Resumen para decidir qué atacar primero

| # | Obstáculo | Estado | Esfuerzo estimado para resolver |
|---|---|---|---|
| 1 | PDF protegido (IRM) | Resuelto (caso único) | — |
| 2-6 | Extracción de tabla con pdfplumber | Resuelto, reutilizable | — |
| 7 | Formato no cambia limpio por fecha | Diagnosticado, sin solución general | Medio — cada plantilla debe autoverificarse |
| 8-9 | Narrativo sin cifras / EEFF sí las tiene | Resuelto para ECOPETROL | Bajo — repetir patrón en otros emisores |
| 10-12 | TOC, notas al pie, conceptos duplicados | Resuelto, reutilizable | — |
| 13 | PDF escaneado (2024-ANUAL) | Sin resolver | Alto (OCR) o bajo (pedir versión no escaneada) |
| 14 | EBITDA derivado, no exacto | Aceptado como limitación conocida | — |
| 15 | Comunicado como única fuente para algunos trimestres | **Decisión de producto pendiente** | Bajo una vez decidido |
| 16 | CIBEST y SURA sin plantilla | Reconocimiento hecho, no construido | Alto — un ciclo completo por emisor |
