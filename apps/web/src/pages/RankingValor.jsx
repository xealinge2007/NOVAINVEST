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

  // Todas las acciones, de mejor a peor puntaje (spread de valor ROIC-WACC).
  // Sin dato de spread se manda al final -- no es "peor", es "sin calcular".
  const filasOrdenadas = useMemo(() => {
    return [...filas].sort((a, b) => {
      if (a.spread_valor === null && b.spread_valor === null) return 0;
      if (a.spread_valor === null) return 1;
      if (b.spread_valor === null) return -1;
      return b.spread_valor - a.spread_valor;
    });
  }, [filas]);

  return (
    <div className="flex flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-400">Screener</p>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Ranking de valor — BVC</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500">
          Todos los emisores, de mejor a peor spread de creación de valor (ROIC − WACC; en bancos y holdings
          financieros, ROE − Ke). Las marcadas con ★ crean valor por encima de su costo de capital y no tienen
          múltiplos fuera de rango ("Estrellas de la BVC"). No es una recomendación de inversión — sin backtest
          todavía. Para la ficha completa de cada emisor, ve a{" "}
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
          {filasOrdenadas.map((f, i) => (
            <div key={f.emisor_id} className="flex items-center gap-3 px-3 py-2 text-sm">
              <span className="w-6 shrink-0 text-right font-mono text-xs text-slate-400">{i + 1}</span>
              <span className="w-4 shrink-0 text-center text-amber-500">{esEstrella(f) ? "★" : ""}</span>
              <span className="flex-1 truncate font-medium text-slate-800">{f.nombre}</span>
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
