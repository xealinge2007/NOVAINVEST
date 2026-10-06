# Blueprint — novainvest
<!-- Actualizado: 2026-10-06 -->

## 1. Qué quiero lograr
Identificar el valor de cada empresa de la BVC a partir de sus estados financieros, ROIC, márgenes,
FCF, deuda, valoración, múltiplos y ventajas competitivas, con datos trazables y etiquetas que no
induzcan a error. Auditoría independiente: la pedirá Alex cuando quiera (no hay destinatario fijado).

## 2. En qué punto está (6-oct-2026)
- Motor de valor, ranking por puertas y PWA en producción hasta el commit `220240c`. Criterios vigentes: `db/CRITERIOS_VALORACION.md`
  (fuente única); `ESTADO_PROYECTO.md` y `DOCTRINA_VALOR.md` son bitácoras históricas.
- Tras la revisión de Codex (`db/CODEX_INFORME_AUDITORIA_2026-10-04.md`) se hicieron P2 (categorías descriptivas, riesgos, retorno ilustrativo,
  historial, escenarios bajo/alto) y P1 (DCF explícito con política "menor de EPV y DCF", escenario spot en commodities, ROE de bancos
  sobre patrimonio promedio sin rupturas). Commits locales `ed67ae5` (orden del repo), `bc503e9` (P2) y el de P1; **sin push** (requiere "sí" de Alex).
- Pruebas: `python jobs/correr_pruebas.py` → 14/14.
- Respaldo del corpus `C:\Proyectos\BVC\` hecho el 6-oct-2026 en `G:\Mi unidad\Respaldos\BVC_2026-10-06` (Google Drive): 1.003 archivos, 6.499.328.408 bytes, idénticos al origen.

## 3. Archivos en juego
- apps/api/app/services/valoracion.py — EPV, DCF (`dcf_dos_etapas`), conciliación (`conciliar_epv_dcf`, `POLITICA_VALOR_CENTRAL`), bancos (`roes_banco`)
- apps/api/app/services/ranking_valor.py — puertas, categorías, riesgos, retorno ilustrativo, causa del cambio
- jobs/valoracion_por_accion.py, jobs/ranking_valor.py, jobs/compat_esquema.py — cálculo, ranking e historial
- apps/web/src/pages/RankingValor.jsx — categorías, riesgos, EPV vs DCF, historial
- db/migrate_p6_nombres_y_categorias.sql — **pendiente de aplicar por Alex** (renombra p25/p75, nuevas categorías, tabla de historial)
- db/CONCILIACION_PEI_CONCONCRETO.md, db/NOTA_AUDITORIA_EXTERNA.md — insumos y nota para un auditor humano

## 4. Cambios hechos
- 6-oct: P2 y P1 de Codex (ver sección 2). Se corrió el pipeline real (`valoracion_por_accion.py`, `ranking_valor.py`) con el esquema viejo: los jobs
  escriben `valor_p25_mmm` / `valor_p75_mmm` y las categorías viejas mientras no se aplique la migración P6. El historial no se guarda hasta aplicarla.
- Efecto en el ranking: Terpel pasa de 37.338 (margen 49,5 %, puesto 1) a 22.083 (14,7 %, puesto 3, "sin descuento"); Promigas de 7.556 a 5.058; Cibest 36.788 → 35.398 con alto 49.613 (antes 59.557).
  PEI queda 1.º como "descuento sin soporte" (no tiene catalizador ni renta sostenible).

## 5. Intentos fallidos — no repetir
- [2026-09-25] Navegar SIMEV (BVC tipo 082/entidad 000004) con el navegador automatizado → "No hay información" intermitente. No repetir.
- [2026-09-25] Buscar estados financieros de BVC en bvc.com.co → solo hay presentaciones. No repetir.
- [2026-10-04] Leer PDF de pei.com.co con WebFetch → 404 o binario; funciona descargar y extraer con pdfplumber o usar Fiducoldex.
- [2026-10-06] DCF con reinversión g/ROIC usando el ROIC TTM sin piso → GEB -431 y Celsia 113 por acción (ROIC contable de 5-6 %). Se corrigió con ROIC = max(ROIC, WACC).
- [2026-10-06] Edición por script con `str.replace` sin `assert`: dos reemplazos no coincidieron y no avisaron. Siempre afirmar que el texto existe.

## 6. Siguientes pasos
1. Alex: aplicar `db/migrate_p6_nombres_y_categorias.sql` en el SQL Editor de Supabase y luego re-correr `jobs/ranking_valor.py` (activa historial y nombres nuevos).
2. Alex: decidir si deja `POLITICA_VALOR_CENTRAL = "menor_de_epv_y_dcf"` o vuelve a `"epv"`; y dar el "sí" para el push de los 3 commits locales.
3. Disparadores de recálculo (ver memoria `novainvest-estado-y-disparadores`): cierre de Terranum por PEI, cierre anual 2026 (Cementos Argos), concentración de PEI sin fuente.
4. Pendiente P1: indicadores regulatorios de bancos de la misma entidad y período (Superfinanciera), costo del riesgo normalizado, precios sostenibles de commodities,
   DCF para ISA y GEB (requiere ingresos asociados al resultado de asociadas), holdings con participaciones no cotizadas por múltiplos.
5. Pendiente P2: guardar acciones y supuestos en el historial para separar esa causa del cambio del valor.
6. P3 (backtest punto en el tiempo): solo sirve para descartar con n ≈ 24 emisores.
