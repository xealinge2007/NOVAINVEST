import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAciertosValor } from "../api/client";
import { fmt } from "../lib/fundamentalesUtils";
import { VEREDICTO } from "../components/Veredicto";
import backtest from "../data/backtest_v3.json";

export default function Aciertos() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [h, setH] = useState("1");

  useEffect(() => {
    getAciertosValor().then(setDatos).catch((e) => setError(e.message));
  }, []);

  const actual = datos?.[h];
  const horizontes = datos ? Object.values(datos) : [];

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <Link to="/fundamentales/ranking" className="text-xs text-brand-700 hover:underline">← Ranking de valor</Link>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">Aciertos del sistema</h1>
        <p className="mt-2 text-sm text-slate-500">
          Dos validaciones: la prueba contra la historia (hecha una vez, con los datos 2019-2025) y el historial en vivo, que
          crece solo con cada corrida semanal. Ninguna es una garantía: con pocos emisores sirven para descartar, no para probar.
        </p>
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700">
        <h2 className="font-serif text-lg font-semibold text-slate-900">1. Prueba contra la historia (V3)</h2>
        <p className="mt-1">
          {backtest.observaciones} observaciones emisor-año ({backtest.observaciones_motor} con valor intrínseco). Cartera formada cada 1 de abril con
          el anual del año anterior; retorno total a 1 año.
        </p>
        <ul className="mt-2 list-disc pl-4">
          <li>Valor intrínseco: correlación de rangos {fmt(backtest.spearman_motor_1a, 2)}; tercio barato menos tercio caro {fmt((backtest.tercios_motor_1a || 0) * 100, 1)} pp.</li>
          <li>Rendimiento por dividendo (mejor rival simple): {fmt(backtest.spearman_rival_1a, 2)}; {fmt((backtest.tercios_rival_1a || 0) * 100, 1)} pp.</li>
        </ul>
        <p className="mt-2 font-medium">
          {backtest.supera_al_rival
            ? "El valor intrínseco supera al rival simple en esta muestra."
            : "El valor intrínseco no supera al rival simple: es prácticamente un empate. Por regla fijada antes de la prueba, el dividendo pasa a ordenar el ranking dentro de cada veredicto y el valor intrínseco queda como una de las tres lentes."}
        </p>
        <p className="mt-1 text-xs text-slate-500">Informe completo y límites: db/BACKTEST_V3.md en el repositorio.</p>
      </section>

      <section>
        <h2 className="font-serif text-lg font-semibold text-slate-900">2. Historial en vivo (V4)</h2>
        <p className="text-sm text-slate-500">
          Qué dijo el sistema hace N meses y cuánto se movió el precio desde entonces (sin dividendos). Las fotos anteriores al 17-nov-2026 no tienen
          veredicto de 3 lentes: se clasifican por el margen del motor (±20 %).
        </p>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="mt-2 flex gap-2">
          {horizontes.map((x) => (
            <button key={x.meses} onClick={() => setH(String(x.meses))}
              className={`rounded px-2 py-1 text-xs ${h === String(x.meses) ? "bg-brand-900 text-white" : "border border-slate-300"}`}>
              {x.meses} {x.meses === 1 ? "mes" : "meses"} ({x.filas.length})
            </button>
          ))}
        </div>
        {actual && actual.filas.length === 0 && (
          <p className="mt-2 text-sm text-slate-500">Todavía no hay fotos de hace {actual.meses} meses: el historial empezó el 6-oct-2026.</p>
        )}
        {actual && actual.filas.length > 0 && (
          <>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              {Object.entries(actual.resumen).filter(([k]) => k !== "_todos").map(([k, r]) => (
                <div key={k} className="rounded border border-slate-200 bg-white p-2 text-sm">
                  <p className="text-xs text-slate-500">{(VEREDICTO[k] || { texto: k }).texto} ({r.n})</p>
                  <p className="cifra font-semibold">{r.variacion_media_pct >= 0 ? "+" : ""}{fmt(r.variacion_media_pct, 1)}%</p>
                  <p className="cifra text-xs text-slate-500">{r.contra_la_media_pp >= 0 ? "+" : ""}{fmt(r.contra_la_media_pp, 1)} pp contra la media</p>
                </div>
              ))}
            </div>
            <table className="mt-3 w-full text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr><th className="text-left">Emisor</th><th className="text-left">Foto</th><th className="text-left">Dijo</th><th className="text-right">Precio entonces</th><th className="text-right">Hoy</th><th className="text-right">Variación</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actual.filas.sort((a, b) => b.variacion_pct - a.variacion_pct).map((f) => (
                  <tr key={f.emisor_id}>
                    <td className="py-1"><Link to={`/valor/${f.emisor_id}`} className="hover:underline">{f.nombre || f.emisor_id}</Link></td>
                    <td className="text-xs">{f.fecha_foto}</td>
                    <td className="text-xs">{(VEREDICTO[f.veredicto] || { texto: f.veredicto }).texto}{f.fuente === "motor" ? " (motor)" : ""}</td>
                    <td className="cifra text-right">{fmt(f.precio_entonces, 0)}</td>
                    <td className="cifra text-right">{fmt(f.precio_hoy, 0)}</td>
                    <td className={`cifra text-right ${f.variacion_pct >= 0 ? "text-emerald-700" : "text-red-700"}`}>{f.variacion_pct >= 0 ? "+" : ""}{fmt(f.variacion_pct, 1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </div>
  );
}
