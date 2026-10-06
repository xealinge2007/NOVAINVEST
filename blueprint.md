# Blueprint — novainvest
<!-- Actualizado: 2026-10-04 18:30 -->

## 1. Qué quiero lograr
Identificar el valor de cada empresa de la BVC a partir de sus estados financieros, ROIC, márgenes,
FCF, deuda, valoración, múltiplos y ventajas competitivas, con datos trazables y etiquetas que no
induzcan a error. Auditoría independiente pendiente.

## 2. En qué punto está
P0-P3 de la auditoría propia hechos y en producción (ranking por puertas en /fundamentales/ranking).
Aplicada la revisión de Codex del 04-oct: renta exige payout, seguridad no evaluada nunca favorable,
desfase de resultados bloquea, sin tamaño de posición, endpoint con error visible, escenarios rotulados.
PEI pasó de "segura y barata" a "trampa de descuento". Falta push de esta tanda y la auditoría humana.

## 3. Archivos en juego
- apps/api/app/services/ranking_valor.py — reglas de cuadrantes y puertas
- jobs/ranking_valor.py — arma el ranking (fechas, desfase, subida, distribución)
- jobs/analizador_fundamental.py — TTM (T4 acumulado como anual), distribución de PEI fuera del dividendo
- apps/web/src/pages/RankingValor.jsx — escenarios, margen y subida por separado
- db/CONCILIACION_PEI_CONCONCRETO.md — insumos y fuentes de ambas valoraciones
- db/NOTA_AUDITORIA_EXTERNA.md — nota para el auditor humano (pendiente de enviar)

## 4. Cambios hechos
- Tanda Codex del 04-oct-2026: ver commit siguiente a e28c51a; sin push.

## 5. Intentos fallidos — no repetir
- [2026-09-25] Probé navegar SIMEV (BVC tipo 082/entidad 000004) con el navegador automatizado →
  falló porque el filtro devuelve "No hay información" de forma intermitente; causa no resuelta.
  No repetir con navegador automatizado.
- [2026-09-25] Probé buscar estados financieros de BVC en bvc.com.co → falló porque solo hay
  presentaciones corporativas, no estados financieros. No repetir.
- [2026-10-04] Probé leer PDF de pei.com.co con WebFetch → falló (404 o binario); funciona descargar y
  extraer con pdfplumber, o usar los informes de Fiducoldex. No repetir WebFetch directo sobre PDF.

## 6. Siguientes pasos
- Publicar esta tanda (git push origin main) con el OK de Alex.
- PEI (6-oct): cerrado con fuente primaria (EEFF 30-jun-2026 en pei.com.co): deuda 2.676 al 11,89 %, 4,73x EBITDA, cobertura 1,78x, sin covenants, vencimientos, capex 1S 42,5, sin impuestos latentes, rentas contratadas 2.979. CORREGIDO un error mío (costo 11,4 % inferido; el real es 11,89 %). ABIERTO: concentración por activo/arrendatario (no se publica). EVENTO: Terranum 2.181.025 M aprobado por la asamblea del 22-sep (70,76 %), parte vinculada, pendiente de autoridades: recalcular títulos/NAV al cierre.
- Reexpresiones y perímetro (6-oct): política + revisión de 8 casos pusheadas (aa29f8c, 5fddb0a); ventana de perímetro vigente (`PERIMETRO_DESDE`, `jobs/diagnostico_perimetro.py`) aplicada a EPV y ventaja. Conconcreto y Cementos Argos no determinables, Mineros 11.760, Terpel igual. ABIERTO: reconstruir las series previas a una ruptura (hoy se descartan); EBITDA 1T-2026 de Conconcreto (D&A del XBRL incompleta: 5.289 vs 3.370).
- Terpel (#1) revisado (6-oct): central 37.338 usa EBIT de los últimos 3 años por tendencia (R² 0,79, influida por el COVID); con el promedio del período vale 22.673 (+20 % sobre el precio). Aviso informativo agregado a todos los EPV (`por_accion_promedio_periodo`). ABIERTO: confirmar en el prospecto/nota 24 si los arrendamientos (881) están dentro de la deuda de 3.651.
- GEB: hecho el 5-oct (migrate_p4_resultado_asociadas.sql aplicada; EPV con minoritario a mercado (migrate_p5): 2.454 por acción, margen -24 %, safe_cara #9). ISA igual (minoritario a mercado + asociadas): 10.796 por acción, margen -168 %, #17; depende del WACC CAPM 12,2 %.
- Enviar db/NOTA_AUDITORIA_EXTERNA.md a un auditor humano (falta destinatario).
