-- P5 (05-oct-2026): utilidad atribuible a participaciones no controladoras (minoritarios), del XBRL
-- (ProfitLossAttributableToNoncontrollingInterests). Sirve para valorar el interés minoritario a mercado
-- (utilidad normalizada / (Ke - g)) en vez de a valor en libros. Miles de millones de COP, flujo.
-- Aplicar en el SQL Editor. El job de carga funciona sin esta columna (avisa y no la escribe).

alter table fundamentales_reportados
    add column if not exists utilidad_minoritarios numeric;  -- flujo, después de impuestos
