# Blueprint — novainvest
<!-- Actualizado: 2026-10-02 09:00 -->

## 1. Qué quiero lograr
Identificar el valor de cada empresa de la BVC a partir de sus estados financieros, ROIC, márgenes,
FCF, deuda, valoración, múltiplos y ventajas competitivas. Auditar lo implementado, el plan y las
fuentes, corregir errores y potenciar el motor.

## 2. En qué punto está
Auditoría hecha y escrita (18 errores, plan y fuentes, acciones P0–P3); no se cambió código ni datos.
Hoy no se entrega el valor de ninguna empresa: la PWA muestra el ranking ROIC−WACC viejo y EPV/NAV
viven como constantes en el código. Falta que Alex apruebe arrancar P0 (EBITDA, acciones por clase,
validaciones, retirar el ranking viejo). Pruebas: 8/8 OK, pero ninguna cubre la valoración.

## 3. Archivos en juego
- db/AUDITORIA_MOTOR_VALOR_2026-10-01.md — informe completo (errores E1–E18, acciones A1–A12)
- apps/api/app/services/extraccion/lector_xbrl.py — CONCEPTOS y D&A (E1); ampliar a caja, capex, minoritarios
- jobs/analizador_fundamental.py — capitalización por clase (E2), calcular_estrellas, TTM, ROIC
- jobs/epv_engine.py — EPV con constantes a mano; debe leer de la base y valorar por acción
- jobs/valor_engine.py y jobs/ingesta_participaciones.py — NAV de holdings con precios fijos del 14-sep
- jobs/solidez_financiera.py — vetos por deuda/EBITDA afectados por E1

## 4. Cambios hechos
- Nuevo (sin commit): db/AUDITORIA_MOTOR_VALOR_2026-10-01.md, docs/blueprint-archivo.md.
- Cambia el objetivo: ya no se persigue el 18 % restante de deuda_financiera (queda archivado).

## 5. Intentos fallidos — no repetir
- [2026-09-25] Probé navegar SIMEV (BVC tipo 082/entidad 000004) con el navegador automatizado →
  falló porque el filtro devuelve "No hay información" de forma intermitente; causa no resuelta.
  No repetir con navegador automatizado.
- [2026-09-25] Probé buscar estados financieros de BVC en bvc.com.co → falló porque solo hay
  presentaciones corporativas, no estados financieros. No repetir.

## 6. Siguientes pasos
- Confirmar con Alex arrancar P0 y retirar o etiquetar el ranking viejo (jobs/analizador_fundamental.py).
- Corregir la D&A usando AdjustmentsForDepreciationAndAmortisationExpense (lector_xbrl.py) y recorrer solidez_financiera.py.
- Capitalización por todas las clases de acción (jobs/analizador_fundamental.py).
- Corregir duplicados e ingresos erróneos de Promigas, Enka, Ecopetrol, Celsia, Conconcreto y GEB.
- Ampliar CONCEPTOS del XBRL con caja, capex, gasto financiero y minoritarios (lector_xbrl.py).
