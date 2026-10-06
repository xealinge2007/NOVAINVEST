# Auditoría de NOVAINVEST y plan de mejora

**Fecha del informe:** 4 de octubre de 2026  
**Corte del código y los datos revisados:** 3 de octubre de 2026  
**Propósito:** entregar a Claude un diagnóstico verificable y un plan de implementación para convertir NOVAINVEST en una herramienta confiable de análisis fundamental y valoración de emisores de la Bolsa de Valores de Colombia.

## Instrucción de ejecución para Claude

Usa este informe como especificación de trabajo. Antes de modificar código, revisa el estado actual del repositorio, sus instrucciones y migraciones; confirma cuáles hallazgos siguen vigentes y cuáles ya fueron corregidos. No supongas que el CSV refleja la base actual. Prioriza PEI y Conconcreto. Implementa en fases, con cambios pequeños, controles que fallen de forma visible y pruebas de regresión. No cambies datos en producción ni publiques resultados externos sin autorización explícita. Al cerrar cada fase, informa archivos cambiados, evidencia, pruebas y asuntos pendientes. Conserva el análisis histórico y las notas existentes, pero marca claramente qué queda reemplazado.

## 1. Dictamen ejecutivo

NOVAINVEST ya cuenta con extracción XBRL, métricas fundamentales, rutas de valoración por tipo de emisor, filtros de seguridad y liquidez, una rúbrica de ventajas competitivas y un ranking. Sin embargo, **todavía no es prudente presentarlo como fuente confiable de valor justo, potencial de crecimiento o recomendación por categoría**. La calidad de los datos, los supuestos de valoración y la semántica de las etiquetas no están suficientemente conectados con bloqueos y trazabilidad.

El cuello de botella ya no es simplemente “conseguir más información”. Es garantizar que cada cifra tenga período, perímetro, unidad, fuente y transformación coherentes, y que cualquier carencia material impida emitir una conclusión favorable. Las cifras que siguen son las observadas en los artefactos locales revisados y deben verificarse contra la base de datos vigente antes de actuar sobre ellas.

**Recomendación de uso actual:** considerar el ranking y los valores centrales como hipótesis de análisis, no como señales de compra. Priorizar la conciliación de PEI y Conconcreto y la integridad de períodos y distribuciones antes de ampliar el universo o añadir modelos predictivos.

## 2. Alcance y método

Se revisaron código de valoración y ranking, reglas de seguridad, cálculo de ventajas competitivas, extractos CSV presentes, nota de auditoría externa, blueprint y documentación del proyecto. Se contrastaron aspectos de PEI y Conconcreto con publicaciones públicas disponibles. No se verificó cada fila de Supabase ni cada hecho XBRL/PDF contra su documento fuente; el informe distingue por tanto entre errores demostrables en la implementación y datos que necesitan conciliación.

El código incluye, entre otros, `apps/api/app/services/valoracion.py`, `apps/api/app/services/ranking_valor.py`, `apps/api/app/services/ventaja_competitiva.py`, `jobs/analizador_fundamental.py`, `jobs/valoracion_por_accion.py` y `jobs/ranking_valor.py`. Los artefactos inspeccionados incluyen `ANALISIS_FUNDAMENTAL_BVC.csv`, `RANKING_VALOR_BVC.csv`, `db/NOTA_AUDITORIA_EXTERNA.md` y `blueprint.md`.

## 3. Hallazgos críticos

### H1. “Potencial” no es crecimiento esperado

El margen de seguridad usado por el motor es `(valor estimado − precio) / valor estimado`. Es una medida de descuento frente al valor estimado, no un rendimiento ni una tasa anual. El ranking tampoco fija un horizonte temporal ni modela una trayectoria de flujos que produzca una rentabilidad anualizada. La posición en el ranking ordena cuadrantes y margen, no el retorno esperado ajustado por riesgo.

**Acción:** mostrar por separado:

- Upside al valor estimado: `(valor / precio) − 1`.
- Margen de seguridad: `(valor − precio) / valor`.
- Retorno total anualizado esperado: solo si se declaran horizonte, dividendos/distribuciones y supuestos de evolución del valor.

No llamar “potencial de crecimiento” a un descuento estático.

### H2. Escenarios etiquetados como percentiles

El propio código describe bajo/base/alto como escenarios construidos con variaciones de EBIT y WACC, no como cuantiles estadísticos. Aun así, se guardan en campos llamados `p25` y `p75`. Esta discrepancia puede inducir a interpretar el rango como probabilidad calibrada.

**Acción:** migrar nombres en esquema/API/interfaz a `escenario_bajo`, `escenario_base`, `escenario_alto`; exponer qué supuestos se modifican y etiquetar el rango como no probabilístico.

### H3. EPV altamente sensible a supuestos discutibles

El EPV implementado usa `NOPAT / (WACC − g)`, tasa estatutaria fija del 35 %, crecimiento nominal `g = 3 %` y una normalización de EBIT basada en reglas simples de regresión/promedios. La meta de inflación colombiana sí es 3 %, pero eso no demuestra que el flujo sostenible de cada empresa crezca con la inflación, ni que 3 % sea una tasa adecuada para cada sector y emisor. La meta oficial para la inflación converge a 3 %; no es un pronóstico de crecimiento empresarial. Fuente: [Banco de la República, meta de inflación](https://www.banrep.gov.co/es/glosario/meta-inflacion).

El EBIT histórico se trata en pesos nominales, sin ajuste de inflación, y la regla de R² ≥ 0,5 para elegir los últimos tres años no trata explícitamente ciclos, adquisiciones, cambios de perímetro o eventos no recurrentes. Tampoco es una valoración completa por flujos de caja: capital de trabajo, capex de mantenimiento y reinversión deben ser explícitos o justificarse como supuestos del método.

**Acción:** conservar EPV como contraste; introducir valoración primaria acorde al sector, escenarios explícitos de flujos, impuestos normalizados y sensibilidad. Si los insumos críticos no son comparables, marcar “no determinable”.

### H4. Seguridad y renta pueden resultar favorables con evidencia incompleta

En `ranking_valor.py`, si Pilar 1 no es evaluable, la empresa puede seguir y recibir tamaño relativo mínimo cuando se estima barata. La regla de renta permite considerar “sostenible” un yield alto cuando payout es `None`. La salida convierte ausencia de datos en una clasificación insuficientemente cauta.

**Acción:** “seguridad no evaluada” no debe entrar a cuadrantes favorables ni sugerir tamaño de posición. “Renta sostenible” requiere payout y naturaleza del flujo; si faltan, clasificar como no evaluable. Tratar etiquetas como clasificación descriptiva del modelo, no recomendación personal.

### H5. PEI: NAV y distribución requieren reconciliación

En el ranking local, PEI aparece con precio de COP 66.760, valor central de COP 147.021 y margen de seguridad de 54,6 %. El cálculo inmobiliario está basado principalmente en patrimonio contable por título, con factores de rango 0,90/1,00/1,00; el código reconoce que esos factores son supuestos, no una valoración independiente. La presentación oficial de 1T26 muestra NAV por título de COP 144.620, por lo que COP 147.021 debe conciliarse contra el corte y el reporte oficial de 2T26 antes de llamarse valor justo. Fuente: [Presentación de resultados PEI 1T26](https://pei.com.co/wp-content/uploads/2026/05/Conferencia-de-Resultados-1T26.pdf).

El analizador asigna a PEI 7,6 % de dividend yield anualizando las distribuciones de 1T y 2T 2026. En 1T26, de COP 1.220 por título, COP 7 fueron utilidad distribuida y COP 1.213 restitución parcial de la inversión. La distribución total no se debe representar como dividendo recurrente. Fuente: [Circular oficial PEI sobre FCD 1T26](https://pei.com.co/wp-content/uploads/2026/05/Informacion-relevante-FCD-1Q-2026-15052026.pdf).

**Acciones específicas para PEI:**

1. Conciliar número de títulos, NAV total y NAV por título en estados e informe del representante legal de 2T26, con precio de mercado fechado.
2. Separar por título y por periodo utilidad distribuida, restitución de capital y otras partidas; recalcular payout y yield ordinario.
3. Incorporar deuda, vencimientos, ocupación, concentración por activo/arrendatario, cap rates, gastos, capex e impuestos latentes. Sensibilizar cap rate y ocupación.
4. Etiquetar el resultado como NAV y descuento frente a NAV, distinto de valor intrínseco por flujo y retorno esperado.

### H6. Conconcreto: exclusión por liquidez no equivale a valoración

El CSV local muestra para Conconcreto precio COP 479, valor de referencia central COP 334 y margen de seguridad −43,4 %, pero la empresa está excluida del ranking por el umbral de liquidez. Por tanto, el valor es una referencia de un emisor no rankeado y no una conclusión validada para invertir.

El snapshot de fundamentales muestra balances hasta 2026-T2 mientras ingresos y utilidad se describen como “anual 2025 extendido a 2026-T2”. Debe comprobarse que el TTM incorpora de forma correcta todos los estados intermedios disponibles y que no combina acumulados duplicados, flujos separados/consolidados o períodos distintos. Conconcreto publicó ingresos consolidados de COP 123.188 millones y EBITDA de COP 18.607 millones en 1T26. Fuente: [Comunicado oficial de resultados 1T26](https://conconcreto.com/wp-content/uploads/2026/05/Comunicado-resultados-1T-2026.pdf). La compañía también publica sus informes y estados en [Resultados financieros](https://conconcreto.com/resultados-financieros/) y registra la aprobación de estados de 2025 en su [página de gobierno corporativo](https://conconcreto.com/gobierno-corporativo/).

**Acciones específicas para Conconcreto:**

1. Descargar y conciliar los estados consolidados y separados más recientes publicados; nunca cruzar un perímetro con otro.
2. Rehacer TTM con los acumulados intermedios correctos y verificar cada flujo contra los trimestres precedentes.
3. Evaluar la actividad de construcción por cartera de contratos/proyectos, márgenes, avance, capital de trabajo, garantías, contingencias y deuda a nivel de compañía/proyecto.
4. Mantener dos salidas independientes: estimación fundamental con confianza explícita y riesgo de liquidez/ejecución de una orden.
5. Revisar si el umbral fijo de COP 500 millones diarios durante 20 sesiones es defendible para el usuario objetivo; añadir spread, días sin negociación, profundidad y tamaño de orden.

### H7. La integridad temporal y de perímetro debe ser bloqueante

Los extractos contienen diferencias entre la fecha del balance y la fuente/período de resultados. PEI figura con balance 2026-T2, pero fuente de resultados anual 2024. En Conconcreto, el snapshot indica resultados anuales de 2025 extendidos al corte de 2026-T2. Esto puede ser una decisión por falta de flujos, pero no debe quedar implícito ni habilitar una categoría con confianza alta.

La documentación previa registra errores reales de XBRL: duplicados, cifras cero frente a cifras reales, D&A parcial, capitalización por clase y cifras de ingresos equivocadas. Haber corregido casos concretos no garantiza la exactitud del resto.

**Acción:** cada dato y resultado calculado debe incluir período, fecha de publicación/carga, entidad y perímetro, moneda/unidad, fuente, concepto/contexto XBRL, método de extracción y transformaciones. Rechazar o degradar automáticamente valoraciones si balance, resultados, deuda, caja, acciones y precio no están sincronizados dentro de reglas sectoriales documentadas.

### H8. Ventajas competitivas y confianza tienen falsa precisión

La rúbrica de moat utiliza pesos, límites, coeficientes de variación y umbrales definidos por criterio interno. Algunos componentes dependen del mismo ROIC/WACC que está sujeto a errores de datos y costo de capital; la fuente de ventaja es una lista manual. Los puntajes de 0 a 100 y etiquetas “amplia/estrecha” pueden parecer más objetivos de lo que la evidencia permite.

**Acción:** separar evidencia cuantitativa (persistencia de ROIC/ROE sobre costo de capital, márgenes y estabilidad) de hipótesis cualitativa de ventaja; mostrar período y tamaño de muestra, intervalos y limitaciones. No emitir una clasificación categórica cuando falten años o comparabilidad.

### H9. El endpoint puede presentar fallos como ausencia de resultados

`/fundamentales/ranking-valor` captura cualquier excepción de lectura y devuelve una lista vacía. Un error de migración o base puede parecer un ranking válido con cero empresas.

**Acción:** devolver error tipado y visible, estado de cálculo, fecha de actualización y un mensaje que distinga “sin datos”, “job no ejecutado” y “fallo técnico”.

### H10. La documentación operativa está desfasada

`blueprint.md` afirma que el ranking/valoración aún no existe y que P0 no empezó, aunque el código y outputs muestran trabajo posterior. Esto impide que Claude, un revisor o Alex sepan cuál es el estado vigente.

**Acción:** actualizar blueprint y nota externa después de cada fase. Mantener una sección breve de estado vigente, fecha y evidencia; identificar los diarios históricos como tales y evitar que contradigan el estado actual.

## 4. Plan de implementación

### P0 — Datos, fechas y salidas seguras

**Objetivo:** impedir conclusiones engañosas causadas por datos inválidos, stale o mal clasificados.

1. Confirmar el estado actual de rama, migraciones, Supabase y artefactos; generar inventario por emisor de último precio, balance, resultados, caja, deuda, acciones y fuente.
2. Corregir y conciliar PEI y Conconcreto con fuentes oficiales del corte más reciente.
3. Añadir trazabilidad a nivel de dato y cálculo, incluida fecha de publicación y perímetro separado/consolidado.
4. Incorporar validaciones bloqueantes: balance contable, unidades/escala, duplicados de periodo, acumulados T1-T3 frente a anual, TTM, signo y rango, coherencia entre deuda/caja/EBITDA, acciones/clases/precio, distribución versus restitución de capital.
5. Reducir confianza o impedir clasificación cuando falte una variable material. Hacer explícitas las fechas de balance y resultados.
6. Cambiar el endpoint para informar errores de consulta/cálculo sin devolver `[]` como fallback silencioso.
7. Actualizar documentación del estado y mantener un changelog de correcciones de fuentes.

**Aceptación P0:** PEI y Conconcreto cuentan con conciliación documentada, fechas/perímetros visibles, ningún control crítico falla silenciosamente y las salidas “no evaluable/no determinable” no se convierten en recomendación.

### P1 — Valoración adecuada por modelo de negocio

**Objetivo:** que el valor base no dependa de una fórmula única y supuestos opacos.

1. Operativas: implementar flujo de caja descontado explícito como método primario o complementario a EPV; proyectar ventas/márgenes, impuestos normalizados, capital de trabajo, capex de mantenimiento, reinversión y valor terminal. Usar múltiplos comparables como control.
2. Cíclicas/commodities: normalizar con ciclo y precios sostenibles, no solo media nominal/últimos años; separar escenario spot de normalizado.
3. Bancos: ROE normalizado, costo de equity y capital regulatorio de la misma entidad y período; validar consistencia de grupo/filial.
4. Vehículos inmobiliarios: NAV por unidad y valor por flujo/NOI con supuestos de cap rate, ocupación, costos y deuda; explicar el descuento/prima respecto al NAV.
5. Holdings: suma de partes, doble conteo controlado, precios a fecha común, deuda y gastos centrales, impuestos latentes, tratamiento transparente de no cotizadas.
6. Mantener rangos como escenarios explícitos con tablas de sensibilidad; retirar nomenclatura estadística si no hay calibración.

**Aceptación P1:** cada ruta de valoración tiene especificación, fuentes y fórmulas revisables; pruebas unitarias cubren escenarios extremos y un recálculo manual independiente coincide dentro de tolerancias justificadas.

### P2 — Categorías y potencial comprensibles

**Objetivo:** que el usuario pueda distinguir descuento, retorno, riesgo y calidad de evidencia.

1. Cambiar `p25/p75` por escenario bajo/base/alto en toda la cadena.
2. Exponer upside, margen de seguridad y retorno total anualizado por separado.
3. No llamar sostenible a una distribución sin clasificar su origen y comprobar capacidad de pago.
4. Reemplazar etiquetas ambiguas como `safe_cheap` por categorías descriptivas que incluyan riesgo de datos, liquidez y deuda.
5. Eliminar tamaños de posición sugeridos sin perfil y cartera del usuario; si se conserva una escala relativa, explicar que no es recomendación personalizada y fijar una regla reproducible.
6. Añadir historial de cambio del valor y qué lo causó (precio, estados, acciones o supuesto).

**Aceptación P2:** las categorías tienen definición funcional, muestran riesgos y evidencia, y no usan “potencial” para referirse a upside estático.

### P3 — Validación y auditoría independiente

**Objetivo:** probar que los modelos son útiles fuera de la muestra de desarrollo.

1. Construir backtest punto-en-tiempo sin sesgo de supervivencia ni uso de estados publicados después de la fecha simulada.
2. Incluir dividendos/distribuciones, costos, spreads, liquidez de BVC, impuestos aplicables y deslistes/corporate actions cuando estén disponibles.
3. Evaluar error de valoración, calibración del rango, desempeño de categorías y estabilidad por sector/regímenes; comparar contra benchmarks sencillos.
4. Entregar a un profesional externo independiente datos fuente, muestra de conciliaciones, reglas, supuestos, pruebas y excepciones. No enviar solo los resultados resumidos.
5. Mantener como limitación pública lo que no pueda verificarse; no afirmar que una revisión interna de IA es una auditoría externa.

**Aceptación P3:** informe reproducible, metodología versionada, métricas contra benchmark y lista firmada de limitaciones/cambios solicitados por el revisor externo.

## 5. Criterios transversales de calidad

- **Una cifra por acción requiere** precio y número de títulos/clase con fuente y fecha congruentes.
- **Una razón financiera requiere** numerador y denominador del mismo periodo, moneda, perímetro y base contable.
- **Una valoración requiere** reconciliación entre valor de empresa y valor patrimonial, deuda neta, minoritarios, acciones diluidas y fecha del precio.
- **Un rango requiere** describir supuestos y no sugerir probabilidades no estimadas.
- **Una categoría favorable requiere** pasar calidad de datos y seguridad; falta de información no equivale a aprobación.
- **Toda automatización debe poder explicar** origen, transformación, regla que se activó y versión del modelo.

## 6. Nota para el auditor externo independiente

La nota existente en `db/NOTA_AUDITORIA_EXTERNA.md` es un punto de partida; actualizarla al completar P0. Solicitar al auditor, sin sesgarlo hacia una metodología particular:

1. Revisar una muestra estratificada de cifras XBRL/PDF, incluyendo PEI y Conconcreto, y recalcularlas desde fuente.
2. Revisar TTM, consolidación, deuda/caja, minoritarios, acciones por clase y estados de flujo.
3. Recalcular una valoración por arquetipo y examinar si el modelo, los supuestos y las etiquetas son razonables.
4. Probar validaciones, exclusiones, errores de API y actualización de fuentes.
5. Evaluar sesgo de supervivencia, backtest, liquidez y límites de uso.
6. Reportar hallazgos y severidad sin asumir que los criterios de Claude o NOVAINVEST son correctos.

## 7. Orden recomendado de ejecución

1. **P0.1:** reconciliar PEI y Conconcreto y documentar cifras/cortes.
2. **P0.2:** instalar validaciones y bloquear salidas inconsistentes.
3. **P0.3:** corregir estados de error, evidencia y documentación vigente.
4. **P1:** valoración por arquetipo y pruebas de sensibilidad.
5. **P2:** vocabulario y categorías de inversión.
6. **P3:** backtest y revisión externa independiente.

No avanzar una fase ocultando los pendientes de la anterior. Al terminar P0, entregar los cálculos de PEI y Conconcreto con cada input fuente visible para revisión humana.
