import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getFundamentales } from "../api/client";
import { esEstrella, fmt } from "../lib/fundamentalesUtils";

export default function RankingValor() {
  const [filas, setFilas] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setFilas(await getFundamentales());
      } catch (err) {
        setError(err.message);
      } finally {
        setCargando(false);
      }
    })();
  }, []);

  // Primero los que entran al ranking (por ranking_estrella); después los descartados, con su
  // motivo a la vista. Un emisor con alerta abierta o sin liquidez no se rankea.
  const filasOrdenadas = useMemo(() => {
    return [...filas].sort((a, b) => {
      if (a.ranking_estrella === null && b.ranking_estrella === null) return 0;
      if (a.ranking_estrella === null) return 1;
      if (b.ranking_estrella === null) return -1;
      return a.ranking_estrella - b.ranking_estrella;
    });
  }, [filas]);

  return (
    <div className="flex flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">Screener</p>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Ranking de valor — BVC</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          <strong className="text-amber-700">Criterio anterior, no validado:</strong> ordena por spread de
          creación de valor (ROIC − WACC; en bancos y holdings financieros, ROE − Ke), que castiga a los
          holdings y se calcula con datos en corrección. Será reemplazado por el Motor de Valor (valor por
          acción frente al precio). Las marcadas con ★ crean valor por encima de su costo de capital. Los
          emisores con alerta de datos o sin liquidez suficiente no se rankean y aparecen al final con su
          motivo. No es una recomendación de inversión. Para la ficha completa de cada emisor, ve a{" "}
          <Link to="/fundamentales" className="text-brand-700 underline">
            Fundamentales
          </Link>
          .
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && filas.length === 0 && <p className="text-sm text-slate-500">Todavía no hay análisis cargado.</p>}

      {filasOrdenadas.length > 0 && (
        <div className="flex flex-col divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
          {filasOrdenadas.map((f) => (
            <div key={f.emisor_id} className="flex items-center gap-3 px-3 py-2 text-sm">
              <span className="w-6 shrink-0 text-right font-mono text-xs text-slate-400">{f.ranking_estrella ?? "—"}</span>
              <span className="w-4 shrink-0 text-center text-amber-500">{esEstrella(f) ? "★" : ""}</span>
              <span className="flex-1 truncate font-medium text-slate-800">
                {f.nombre}
                {f.ranking_estrella === null && f.alerta_multiplos && (
                  <span className="ml-2 text-xs font-normal text-amber-700" title={f.alerta_multiplos}>
                    no rankeado: {f.alerta_multiplos}
                  </span>
                )}
              </span>
              <span className="hidden font-mono text-xs text-slate-400 sm:inline">{f.ticker}</span>
              <span className="hidden text-xs text-slate-400 md:inline">{f.sector || "—"}</span>
              <span
                className={`cifra w-20 shrink-0 text-right text-sm font-semibold ${
                  f.spread_valor === null ? "text-slate-400" : f.spread_valor >= 0 ? "text-emerald-700" : "text-red-700"
                }`}
              >
                {f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}pp`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
