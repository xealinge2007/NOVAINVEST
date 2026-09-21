// Isotipo de NOVAINVEST: la matriz de 2x2 del Motor de Valor
// (Safe&Cheap / Safe pero cara / Trampa de valor / Ni safe ni cheap,
// ver db/DOCTRINA_VALOR.md). No es un glifo genérico -- es la doctrina
// del producto convertida en marca: la celda "Safe & Cheap" siempre
// se marca sólida, las otras tres quedan en trazo.
export default function MarcaNovainvest({ className = "h-6 w-6", title = "NOVAINVEST" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} role="img" aria-label={title}>
      <rect x="2" y="2" width="9.5" height="9.5" rx="2" fill="var(--color-cuadrante-safe-cheap)" />
      <rect
        x="12.5"
        y="2"
        width="9.5"
        height="9.5"
        rx="2"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.35"
        strokeWidth="1.5"
      />
      <rect
        x="2"
        y="12.5"
        width="9.5"
        height="9.5"
        rx="2"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.35"
        strokeWidth="1.5"
      />
      <rect
        x="12.5"
        y="12.5"
        width="9.5"
        height="9.5"
        rx="2"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.35"
        strokeWidth="1.5"
      />
    </svg>
  );
}
