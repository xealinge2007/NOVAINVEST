import { useState } from "react";
import { getFichaEtf, getSolapamientoEtf } from "../api/client";

const TICKERS_DISPONIBLES = ["VOO", "VT", "QQQ", "SGOV", "BIL"];

export default function FichasEtf() {
  const [ticker, setTicker] = useState("VOO");
  const [ficha, setFicha] = useState(null);
  const [tickerA, setTickerA] = useState("VOO");
  const [tickerB, setTickerB] = useState("VT");
  const [solapamiento, setSolapamiento] = useState(null);
  const [error, setError] = useState(null);

  async function verFicha(t) {
    setError(null);
    setTicker(t);
    try {
      setFicha(await getFichaEtf(t));
    } catch (err) {
      setError(err.message);
    }
  }

  async function verSolapamiento(e) {
    e.preventDefault();
    setError(null);
    try {
      setSolapamiento(await getSolapamientoEtf(tickerA, tickerB));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Fichas de ETF</h1>
      </div>

      <section className="flex flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          {TICKERS_DISPONIBLES.map((t) => (
            <button
              key={t}
              onClick={() => verFicha(t)}
              className={`cursor-pointer rounded-md border px-3 py-1 text-sm font-mono transition-colors ${
                ticker === t
                  ? "border-brand-900 bg-brand-900 text-white"
                  : "border-slate-300 text-slate-700 hover:border-brand-700"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        {ficha && (
          <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-4 text-sm">
            <p className="font-serif text-base font-medium text-slate-900">{ficha.nombre}</p>
            <p>
              TER: <span className="cifra">{ficha.ter_pct}%</span>
            </p>
            <p className="text-xs text-slate-400">Referencia al {ficha.fecha_referencia}</p>
            <div className="mt-2">
              {Object.entries(ficha.top_holdings).length === 0 && (
                <p className="text-xs text-slate-500">Sin holdings de renta variable (deuda del Tesoro).</p>
              )}
              {Object.entries(ficha.top_holdings).map(([h, w]) => (
                <p key={h} className="cifra">
                  {h}: {w}%
                </p>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Solapamiento entre dos ETFs</h2>
        <form onSubmit={verSolapamiento} className="flex max-w-sm gap-2">
          <select
            className="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            value={tickerA}
            onChange={(e) => setTickerA(e.target.value)}
          >
            {TICKERS_DISPONIBLES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select
            className="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
            value={tickerB}
            onChange={(e) => setTickerB(e.target.value)}
          >
            {TICKERS_DISPONIBLES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <button className="cursor-pointer rounded-md bg-brand-900 px-4 text-sm text-white hover:opacity-90">
            Comparar
          </button>
        </form>
        {solapamiento && (
          <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-4 text-sm">
            <p>
              {solapamiento.cantidad_comunes} holdings en común: {solapamiento.holdings_comunes.join(", ") || "ninguno"}
            </p>
            <p>
              Solapamiento estimado: <span className="cifra">{solapamiento.solapamiento_pct_estimado}%</span>
            </p>
            <p className="text-xs text-slate-400">{solapamiento.nota}</p>
          </div>
        )}
      </section>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
