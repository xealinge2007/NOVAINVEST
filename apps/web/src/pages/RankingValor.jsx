import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getRankingValor } from "../api/client";
import { fmt } from "../lib/fundamentalesUtils";

const CUADRANTE = {
  safe_cheap: { texto: "Segura y barata", clase: "bg-emerald-100 text-emerald-800" },
  trampa_descuento: { texto: "Trampa de descuento", clase: "bg-amber-100 text-amber-800" },
  safe_cara: { texto: "Segura, sin descuento", clase: "bg-slate-100 text-slate-700" },
  seguridad_no_evaluada: { texto: "Seguridad no evaluada", clase: "bg-sky-100 text-sky-800" },
};
const EVIDENCIA = {
  provisional: { texto: "Provisional", clase: "bg-red-50 text-red-700" },
  estructura: { texto: "Estructura", clase: "bg-amber-50 text-amber-700" },
  verificado: { texto: "Verificado", clase: "bg-emerald-50 text-emerald-700" },
};
const PUERTA = { liquidez: "Liquidez", datos: "Datos", seguridad: "Seguridad", valor: "Valor" };
const VENTAJA = { amplia: "Amplia", estrecha: "Estrecha", ninguna: "Ninguna", no_aplica: "No aplica", no_evaluable: "No evaluable" };

function Etiqueta({ def, valor }) {
  const d = def[valor];
  if (!d) return <span className="text-slate-400">—</span>;
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${d.clase}`}>{d.texto}</span>;
}

function Detalle({ f }) {
  const d = f.detalle || {};
  const avisos = [...(d.avisos || []), ...((d.ventaja && d.ventaja.avisos) || [])];
  return (
    <div className="grid gap-3 bg-slate-50 px-4 py-3 text-xs text-slate-600 sm:grid-cols-2">
      <div>
        <p className="font-semibold text-slate-700">Cómo se valoró</p>
        <p>{d.metodo || "—"}</p>
        {d.crecimiento_real_implicito_pct !== null && d.crecimiento_real_implicito_pct !== undefined && (
          <p className="mt-1">
            El precio descuenta un crecimiento real de {fmt(d.crecimiento_real_implicito_pct)}% anual.
          </p>
        )}
        <p className="mt-1">
          Percentil propio del P/E: {fmt(d.percentil_propio?.per, 0)} · del P/VL: {fmt(d.percentil_propio?.pvl, 0)} (0 = más barato de su historia).
        </p>
      </div>
      <div>
        <p className="font-semibold text-slate-700">Seguridad, ventaja, catalizador y renta</p>
        <p>{d.seguridad || "—"}</p>
        <p className="mt-1">
          Ventaja competitiva: {VENTAJA[d.ventaja?.nivel] || "—"}
          {d.ventaja?.puntaje !== null && d.ventaja?.puntaje !== undefined ? ` (${fmt(d.ventaja.puntaje, 0)}/100)` : ""}
          {d.ventaja?.tendencia ? `, ${d.ventaja.tendencia}` : ""}. Fuente declarada: {d.ventaja?.fuente || "—"}.
        </p>
        <p className="mt-1">Catalizador: {d.catalizador || "—"}.</p>
        <p className="mt-1">
          Dividendo: {fmt(d.renta?.yield_pct)}% sobre el precio, payout {fmt(d.renta?.payout_pct, 0)}%.
        </p>
      </div>
      {avisos.length > 0 && (
        <div className="sm:col-span-2">
          <p className="font-semibold text-amber-700">Avisos sobre los datos</p>
          <ul className="list-disc pl-4">
            {avisos.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function RankingValor() {
  const [filas, setFilas] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [abierta, setAbierta] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setFilas(await getRankingValor());
      } catch (err) {
        setError(err.message);
      } finally {
        setCargando(false);
      }
    })();
  }, []);

  const ranking = filas.filter((f) => !f.excluido);
  const excluidos = filas.filter((f) => f.excluido);
  const nombre = (f) => f.detalle?.nombre || f.detalle?.slug || `#${f.emisor_id}`;

  return (
    <div className="flex flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">Motor de valor</p>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Ranking de valor — BVC</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Cada emisor pasa cuatro puertas en orden — liquidez, integridad de los datos, seguridad financiera y valor por
          acción determinable — y solo entonces se ordena por el margen de seguridad de su valor central frente al precio.
          El valor es un rango (bajo / central / alto) de escenarios, no una predicción.{" "}
          <strong className="text-amber-700">
            No es una recomendación de compra ni tiene backtest: es un punto de partida para investigar. La evidencia de
            cada fila dice qué tan firme es el dato (aún ninguna está “verificada”: falta la auditoría externa).
          </strong>{" "}
          Para la ficha de cada emisor, ve a{" "}
          <Link to="/fundamentales" className="text-brand-700 underline">
            Fundamentales
          </Link>
          .
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && filas.length === 0 && (
        <p className="text-sm text-slate-500">Todavía no hay ranking calculado.</p>
      )}

      {ranking.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">Emisor</th>
                <th className="px-3 py-2">Cuadrante</th>
                <th className="px-3 py-2 text-right">Valor por acción (bajo · central · alto)</th>
                <th className="px-3 py-2 text-right">Precio</th>
                <th className="px-3 py-2 text-right">Margen</th>
                <th className="px-3 py-2">Ventaja</th>
                <th className="px-3 py-2">Evidencia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {ranking.map((f) => (
                <FilaRanking key={f.emisor_id} f={f} nombre={nombre(f)} abierta={abierta === f.emisor_id}
                  alternar={() => setAbierta(abierta === f.emisor_id ? null : f.emisor_id)} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {excluidos.length > 0 && (
        <div>
          <h2 className="font-serif text-lg font-semibold text-slate-900">No entran al ranking ({excluidos.length})</h2>
          <p className="mb-2 text-sm text-slate-500">
            La lista de descartes es parte del producto: cada uno dice qué puerta no pasó.
          </p>
          <div className="flex flex-col divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
            {excluidos.map((f) => (
              <div key={f.emisor_id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-3 py-2 text-sm">
                <span className="w-56 shrink-0 font-medium text-slate-800">{nombre(f)}</span>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                  {PUERTA[f.puerta_fallida] || f.puerta_fallida}
                </span>
                <span className="flex-1 text-xs text-slate-500">{f.motivo_exclusion}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FilaRanking({ f, nombre, abierta, alternar }) {
  const margen = f.margen_seguridad_pct;
  return (
    <>
      <tr className="cursor-pointer hover:bg-slate-50" onClick={alternar}>
        <td className="px-3 py-2 font-mono text-xs text-slate-400">{f.posicion}</td>
        <td className="px-3 py-2 font-medium text-slate-800">{nombre}</td>
        <td className="px-3 py-2"><Etiqueta def={CUADRANTE} valor={f.cuadrante} /></td>
        <td className="cifra px-3 py-2 text-right text-slate-700">
          {fmt(f.valor_bajo, 0)} · <strong>{fmt(f.valor_central, 0)}</strong> · {fmt(f.valor_alto, 0)}
        </td>
        <td className="cifra px-3 py-2 text-right text-slate-700">{fmt(f.precio, 0)}</td>
        <td className={`cifra px-3 py-2 text-right font-semibold ${margen === null || margen === undefined ? "text-slate-400" : margen >= 0 ? "text-emerald-700" : "text-red-700"}`}>
          {margen === null || margen === undefined ? "—" : `${margen >= 0 ? "+" : ""}${fmt(margen, 0)}%`}
        </td>
        <td className="px-3 py-2 text-xs text-slate-600">{VENTAJA[f.ventaja_nivel] || "—"}</td>
        <td className="px-3 py-2"><Etiqueta def={EVIDENCIA} valor={f.nivel_evidencia} /></td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={8} className="p-0"><Detalle f={f} /></td>
        </tr>
      )}
    </>
  );
}
