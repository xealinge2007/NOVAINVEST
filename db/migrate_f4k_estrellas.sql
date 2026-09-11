-- F4k (11-sep-2026) — "Estrellas de la BVC": el ranking del §5.1/F4c del plan.
--
-- Elegible: spread de creación de valor (ROIC - WACC, ya calculado en F4g)
-- positivo, y sin alerta de múltiplos implausibles. Ordenado por spread
-- descendente. `ranking_estrella` = 1 es el mejor; NULL significa que el
-- emisor no es elegible para el ranking (no que sea malo -- puede ser un
-- banco sin ROIC, o sin datos suficientes).
--
-- Esto NO es asesoría de inversión ni está respaldado por backtest todavía
-- -- el backtest walk-forward es la siguiente pieza pendiente de F4c.
--
-- Aplicar en el SQL editor de Supabase.

alter table fundamentales_analisis
    add column if not exists ranking_estrella int;

comment on column fundamentales_analisis.ranking_estrella is
    '1 = mejor creador de valor elegible (spread ROIC-WACC positivo, sin '
    'alerta de múltiplos). NULL = no elegible, no necesariamente malo. '
    'No es asesoría financiera ni recomendación de inversión.';
