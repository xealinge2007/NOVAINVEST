-- P4 (05-oct-2026): participación en el resultado de asociadas y negocios conjuntos (método de
-- participación), tomada del XBRL (ShareOfProfitLossOfAssociatesAndJointVenturesAccountedForUsingEquityMethod).
-- La necesita GEB, cuyo EBIT consolidado la excluye. Miles de millones de COP, flujo, igual que el resto.
-- Aplicar en el SQL Editor. El job de carga funciona sin esta columna (avisa y no la escribe).

alter table fundamentales_reportados
    add column if not exists resultado_asociadas numeric;  -- flujo, después de impuestos de la asociada
