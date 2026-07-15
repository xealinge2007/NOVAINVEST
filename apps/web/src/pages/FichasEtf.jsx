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
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-8">
      <h1 className="text-2xl font-semibold">Fichas de ETF</h1>

      <section className="flex flex-col gap-2">
        <div className="flex gap-2">
          {TICKERS_DISPONIBLES.map((t) => (
            <button key={t} onClick={() => verFicha(t)} className={`text-sm border rounded px-3 py-1 ${ticker === t ? "bg-slate-900 text-white" : ""}`}>
              {t}
            </button>
          ))}
        </div>
        {ficha && (
          <div className="text-sm bg-slate-50 rounded p-3 flex flex-col gap-1">
            <p className="font-medium">{ficha.nombre}</p>
            <p>TER: {ficha.ter_pct}%</p>
            <p className="text-xs text-slate-400">Referencia al {ficha.fecha_referencia}</p>
            <div className="mt-2">
              {Object.entries(ficha.top_holdings).length === 0 && <p className="text-xs text-slate-500">Sin holdings de renta variable (deuda del Tesoro).</p>}
              {Object.entries(ficha.top_holdings).map(([h, w]) => (
                <p key={h}>{h}: {w}%</p>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Solapamiento entre dos ETFs</h2>
        <form onSubmit={verSolapamiento} className="flex gap-2 max-w-sm">
          <select className="border rounded px-2 py-1" value={tickerA} onChange={(e) => setTickerA(e.target.value)}>
            {TICKERS_DISPONIBLES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="border rounded px-2 py-1" value={tickerB} onChange={(e) => setTickerB(e.target.value)}>
            {TICKERS_DISPONIBLES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <button className="bg-slate-900 text-white rounded px-4">Comparar</button>
        </form>
        {solapamiento && (
          <div className="text-sm bg-slate-50 rounded p-3 flex flex-col gap-1">
            <p>{solapamiento.cantidad_comunes} holdings en común: {solapamiento.holdings_comunes.join(", ") || "ninguno"}</p>
            <p>Solapamiento estimado: {solapamiento.solapamiento_pct_estimado}%</p>
            <p className="text-xs text-slate-400">{solapamiento.nota}</p>
          </div>
        )}
      </section>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
