// Compartido entre Fundamentales.jsx y RankingValor.jsx.

// Crea valor por encima de su costo de capital y sin múltiplos fuera de rango.
export function esEstrella(f) {
  return f.ranking_estrella && f.spread_valor > 0 && !f.alerta_multiplos;
}

export function fmt(v, dec = 1) {
  if (v === null || v === undefined) return "—";
  return Number(v).toLocaleString("es-CO", { maximumFractionDigits: dec, minimumFractionDigits: 0 });
}
