import { useMemo, useState } from "react";

// Paleta validada (dataviz skill): slot 1 azul / slot 2 naranja -- par
// adyacente que pasa CVD Delta E >= 8 en ambos modos. Un solo eje: las dos
// series se indexan a 100 en el primer punto donde ambas existen, nunca
// dos ejes-Y -- un dual-axis puede hacer que dos líneas "calcen" con solo
// cambiar la escala, y es justo lo que este gráfico existe para no fingir.
const COLOR_METRICA = "#2a78d6";
const COLOR_PRECIO = "#eb6834";
const INK_SECUNDARIO = "#52514e";
const INK_MUTED = "#898781";
const GRID = "#e1e0d9";

const ANCHO = 640;
const ALTO = 220;
const MARGEN = { top: 16, right: 16, bottom: 24, left: 16 };

function fmtFecha(iso) {
  const [y, m] = iso.split("-");
  return `${["T1", "T1", "T1", "T2", "T2", "T2", "T3", "T3", "T3", "T4", "T4", "T4"][Number(m) - 1]}-${y.slice(2)}`;
}

export default function EvolucionChart({ puntos, etiquetaMetrica, unidadMetrica = "" }) {
  const [hover, setHover] = useState(null);

  const datos = useMemo(() => {
    const conAmbos = puntos.filter((p) => p.valor != null && p.precio != null);
    if (conAmbos.length < 2) return null;
    const baseValor = conAmbos[0].valor;
    const basePrecio = conAmbos[0].precio;
    if (!baseValor || !basePrecio) return null;
    return conAmbos.map((p) => ({
      ...p,
      idxValor: (p.valor / baseValor) * 100,
      idxPrecio: (p.precio / basePrecio) * 100,
    }));
  }, [puntos]);

  if (!datos) {
    return <p className="text-xs text-slate-400 italic">Sin suficientes puntos en común para graficar.</p>;
  }

  const todos = datos.flatMap((d) => [d.idxValor, d.idxPrecio]);
  const yMin = Math.min(100, ...todos);
  const yMax = Math.max(100, ...todos);
  const pad = (yMax - yMin) * 0.1 || 10;
  const y0 = yMin - pad, y1 = yMax + pad;

  const anchoUtil = ANCHO - MARGEN.left - MARGEN.right;
  const altoUtil = ALTO - MARGEN.top - MARGEN.bottom;
  const x = (i) => MARGEN.left + (datos.length === 1 ? 0 : (i / (datos.length - 1)) * anchoUtil);
  const y = (v) => MARGEN.top + altoUtil - ((v - y0) / (y1 - y0)) * altoUtil;

  const linea = (campo) => datos.map((d, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(d[campo])}`).join(" ");

  function alMover(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * ANCHO;
    let mejor = 0, mejorDist = Infinity;
    datos.forEach((_, i) => {
      const dist = Math.abs(x(i) - px);
      if (dist < mejorDist) { mejorDist = dist; mejor = i; }
    });
    setHover(mejor);
  }

  const activo = hover != null ? datos[hover] : null;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded-full" style={{ background: COLOR_METRICA }} />
          <span style={{ color: INK_SECUNDARIO }}>{etiquetaMetrica}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 rounded-full" style={{ background: COLOR_PRECIO }} />
          <span style={{ color: INK_SECUNDARIO }}>Precio</span>
        </span>
        <span className="text-slate-400">(indexado a 100 en {fmtFecha(datos[0].fecha_cierre)})</span>
      </div>
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        className="w-full h-auto"
        onMouseMove={alMover}
        onMouseLeave={() => setHover(null)}
      >
        <line x1={MARGEN.left} y1={y(100)} x2={ANCHO - MARGEN.right} y2={y(100)} stroke={GRID} strokeWidth="1" />
        <path d={linea("idxPrecio")} fill="none" stroke={COLOR_PRECIO} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d={linea("idxValor")} fill="none" stroke={COLOR_METRICA} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {datos.map((d, i) => (
          <text key={i} x={x(i)} y={ALTO - 6} fontSize="9" fill={INK_MUTED} textAnchor="middle">
            {i % Math.ceil(datos.length / 8) === 0 ? fmtFecha(d.fecha_cierre) : ""}
          </text>
        ))}
        {activo && (
          <>
            <line x1={x(hover)} y1={MARGEN.top} x2={x(hover)} y2={ALTO - MARGEN.bottom} stroke={INK_MUTED} strokeWidth="1" strokeDasharray="2,2" />
            <circle cx={x(hover)} cy={y(activo.idxValor)} r="3.5" fill={COLOR_METRICA} />
            <circle cx={x(hover)} cy={y(activo.idxPrecio)} r="3.5" fill={COLOR_PRECIO} />
          </>
        )}
      </svg>
      {activo && (
        <div className="text-xs border rounded px-2 py-1.5 bg-slate-50 flex flex-wrap gap-x-4 gap-y-0.5">
          <span className="font-medium text-slate-700">{fmtFecha(activo.fecha_cierre)}</span>
          <span style={{ color: COLOR_METRICA }}>{etiquetaMetrica}: {activo.valor.toLocaleString("es-CO", { maximumFractionDigits: 2 })}{unidadMetrica} (idx {activo.idxValor.toFixed(0)})</span>
          <span style={{ color: COLOR_PRECIO }}>Precio: {activo.precio.toLocaleString("es-CO", { maximumFractionDigits: 0 })} (idx {activo.idxPrecio.toFixed(0)})</span>
        </div>
      )}
    </div>
  );
}
