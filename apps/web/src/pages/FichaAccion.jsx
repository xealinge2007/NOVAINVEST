import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getHistorialRankingValor, getRankingValor } from "../api/client";
import { fmt } from "../lib/fundamentalesUtils";
import { LENTE, VEREDICTO, VeredictoChip } from "../components/Veredicto";
import backtest from "../data/backtest_v3.json";

const MULTIPLO = { per: "P/U", precio_valor_libro: "P/VL", ev_ebitda: "EV/EBITDA" };
const CRITERIO = {
  roa_positivo: "Rentabilidad sobre activos positiva", flujo_operativo_positivo: "Flujo operativo positivo",
  roa_mejora: "La rentabilidad mejora", flujo_mayor_que_utilidad: "El flujo supera a la utilidad (calidad)",
  apalancamiento_baja: "Baja o mantiene el apalancamiento", sin_emision_de_acciones: "No emite acciones",
  margen_bruto_mejora: "Mejora el margen bruto", rotacion_activos_mejora: "Mejora la rotación de activos",
};

// Precios que cambiarían el veredicto. Con el margen exigido m, una lente vota "infravalorada" si precio <= valor(1-m)
// y "sobrevalorada" si precio >= valor/(1-m). Hacen falta 2 lentes, así que el umbral es el de la segunda.
function umbrales(valores, margen) {
  const v = valores.filter((x) => x > 0).sort((a, b) => a - b);
  if (v.length < 2) return null;
  const m = margen / 100;
  return { infra: v[v.length - 2] * (1 - m), sobre: v[1] / (1 - m) };
}

export default function FichaAccion() {
  const { emisorId } = useParams();
  const [f, setF] = useState(null);
  const [hist, setHist] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getRankingValor()
      .then((filas) => {
        const fila = filas.find((x) => String(x.emisor_id) === String(emisorId));
        if (!fila) setError("Este emisor no está en el ranking calculado.");
        setF(fila || null);
      })
      .catch((e) => setError(e.message));
    getHistorialRankingValor(emisorId).then(setHist).catch(() => setHist([]));
  }, [emisorId]);

  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!f) return <p className="text-sm text-slate-500">Cargando…</p>;
  const d = f.detalle || {};
  const L = d.lentes || {};
  const c = L.consenso || {};
  const valores = { intrinseco: L.intrinseco?.valor, historia: L.historia?.valor, pares: L.pares?.valor };
  const u = c.margen_exigido_pct ? umbrales(Object.values(valores), c.margen_exigido_pct) : null;
  const pio = L.calidad?.piotroski;

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="border-b border-slate-200 pb-4">
        <Link to="/fundamentales/ranking" className="text-xs text-brand-700 hover:underline">← Ranking de valor</Link>
        <h1 className="mt-1 font-serif text-2xl font-semibold text-slate-900">{d.nombre || d.slug}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Estados financieros a {d.fechas?.balance || "—"} · resultados: {d.fechas?.resultados || "—"}
          {d.fechas?.atraso_trimestres > 0 ? ` · ${d.fechas.atraso_trimestres} trimestre(s) de atraso` : " · al día"}
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase text-slate-400">Veredicto (3 lentes)</p>
          <p className="mt-2"><VeredictoChip consenso={c} /></p>
          {c.motivo && <p className="mt-1 text-xs text-slate-500">{c.motivo}</p>}
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase text-slate-400">Precio justo</p>
          <p className="cifra mt-1 text-2xl font-semibold text-slate-900">{fmt(c.precio_justo, 0)}</p>
          <p className="cifra text-xs text-slate-500">rango {fmt(c.rango_justo?.[0], 0)} – {fmt(c.rango_justo?.[1], 0)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs uppercase text-slate-400">Precio de hoy</p>
          <p className="cifra mt-1 text-2xl font-semibold text-slate-900">{fmt(f.precio, 0)}</p>
          <p className={`cifra text-xs ${c.margen_vs_justo_pct >= 0 ? "text-emerald-700" : "text-red-700"}`}>
            {c.margen_vs_justo_pct != null ? `${c.margen_vs_justo_pct >= 0 ? "+" : ""}${fmt(c.margen_vs_justo_pct, 0)}% frente al precio justo` : "—"}
          </p>
        </div>
      </section>

      <section>
        <h2 className="font-serif text-lg font-semibold text-slate-900">Las tres lentes</h2>
        <p className="text-sm text-slate-500">
          Rige lo que digan al menos 2. Incertidumbre {c.incertidumbre || "—"} ({(c.motivos_incertidumbre || []).join("; ")}): por eso se
          exige un margen de {c.margen_exigido_pct ?? "—"}% antes de llamarla barata o cara.
        </p>
        <div className="overflow-x-auto">
          <table className="mt-2 w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr><th className="py-1">Lente</th><th className="text-right">Valor por acción</th><th className="pl-3">Voto</th><th className="pl-3">Cómo sale</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {["intrinseco", "historia", "pares"].map((k) => (
                <tr key={k}>
                  <td className="py-2 font-medium text-slate-800">{LENTE[k]}</td>
                  <td className="cifra text-right">{fmt(valores[k], 0)}</td>
                  <td className="pl-3 text-xs">{(VEREDICTO[c.votos?.[k]] || VEREDICTO.no_determinable).texto}</td>
                  <td className="pl-3 text-xs text-slate-500">
                    {k === "intrinseco" && (L.intrinseco?.valor
                      ? `${d.metodo || L.intrinseco.metodo || ""} (escenarios ${fmt(L.intrinseco.rango?.[0], 0)} – ${fmt(L.intrinseco.rango?.[1], 0)})`
                      : "no determinable")}
                    {k === "historia" && (L.historia
                      ? L.historia.multiplos.map((m) => `${MULTIPLO[m.multiplo]} ${fmt(m.actual, 1)} hoy vs mediana ${fmt(m.mediana, 1)} (percentil ${m.percentil_actual}, ${m.n} trimestres)`).join(" · ")
                      : "menos de 8 trimestres con múltiplos válidos")}
                    {k === "pares" && (L.pares
                      ? L.pares.multiplos.map((m) => `${MULTIPLO[m.multiplo]} ${fmt(m.actual, 1)} vs mediana de pares ${fmt(m.mediana_pares, 1)} (${Object.keys(m.pares).join(", ")})`).join(" · ")
                      : "sin grupo de al menos 3 pares comparables")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <div>
          <h2 className="font-serif text-lg font-semibold text-slate-900">Qué cambiaría el veredicto</h2>
          {u ? (
            <ul className="mt-1 list-disc pl-4 text-sm text-slate-600">
              <li>Por debajo de <strong className="cifra">{fmt(u.infra, 0)}</strong> al menos 2 lentes la verían infravalorada.</li>
              <li>Por encima de <strong className="cifra">{fmt(u.sobre, 0)}</strong> al menos 2 lentes la verían sobrevalorada.</li>
              <li>Unos resultados trimestrales nuevos mueven las tres lentes; menos incertidumbre baja el margen exigido.</li>
            </ul>
          ) : <p className="text-sm text-slate-500">Hacen falta al menos 2 lentes con valor.</p>}
          {L.dcf_inverso?.crecimiento_real_implicito_pct != null && (
            <p className="mt-2 text-sm text-slate-600">
              DCF inverso: el precio de hoy descuenta un crecimiento real perpetuo de{" "}
              <strong>{fmt(L.dcf_inverso.crecimiento_real_implicito_pct, 1)}%</strong> anual con un WACC de {fmt(L.costo_capital?.wacc_pct, 1)}%.
              Si ese crecimiento parece razonable y el valor intrínseco dice lo contrario, el que exagera es el modelo.
            </p>
          )}
        </div>
        <div>
          <h2 className="font-serif text-lg font-semibold text-slate-900">Calidad y costo de capital</h2>
          <p className="mt-1 text-sm text-slate-600">
            Piotroski F ({L.calidad?.piotroski_anio || "—"}):{" "}
            {pio?.puntaje != null ? <strong>{pio.puntaje}/{pio.evaluados} ({pio.lectura})</strong> : (pio?.nota || "—")}
          </p>
          {pio?.criterios && (
            <ul className="mt-1 text-xs text-slate-500">
              {Object.entries(pio.criterios).map(([k, x]) => <li key={k}>{x ? "✓" : "✗"} {CRITERIO[k] || k}</li>)}
            </ul>
          )}
          <p className="mt-1 text-xs text-slate-500">Altman Z: {L.calidad?.altman_z || "—"}. Beneish M: {L.calidad?.beneish_m || "—"}.</p>
          <p className="mt-2 text-sm text-slate-600">
            Ke {fmt(L.costo_capital?.ke_pct, 1)}% · beta {fmt(L.costo_capital?.beta, 2)} ({L.costo_capital?.beta_fuente || "—"}).
            {L.costo_capital?.beta_regresion != null && ` La regresión contra el COLCAP daba ${fmt(L.costo_capital.beta_regresion, 2)}: mide liquidez, no riesgo, y ya no se usa.`}
          </p>
        </div>
      </section>

      <section>
        <h2 className="font-serif text-lg font-semibold text-slate-900">Riesgos</h2>
        {(d.riesgos || []).length ? (
          <ul className="list-disc pl-4 text-sm text-slate-600">{d.riesgos.map((r, i) => <li key={i}>{r.texto}</li>)}</ul>
        ) : <p className="text-sm text-slate-500">—</p>}
        <p className="mt-1 text-sm text-slate-600">Seguridad financiera: {d.seguridad || "—"}</p>
      </section>

      <section>
        <h2 className="font-serif text-lg font-semibold text-slate-900">Qué dijo antes</h2>
        {hist.length === 0 ? <p className="text-sm text-slate-500">Sin fotos guardadas.</p> : (
          <table className="mt-1 text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr><th className="pr-4 text-left">Fecha</th><th className="pr-4 text-left">Veredicto</th><th className="pr-4 text-right">Precio justo</th><th className="text-right">Precio</th></tr>
            </thead>
            <tbody>
              {hist.slice(0, 10).map((h) => (
                <tr key={h.id}>
                  <td className="pr-4">{String(h.calculado_en).slice(0, 10)}</td>
                  <td className="pr-4 text-xs">{h.cambio?.veredicto ? (VEREDICTO[h.cambio.veredicto] || {}).texto : `motor: margen ${fmt(h.margen_seguridad_pct, 0)}%`}</td>
                  <td className="cifra pr-4 text-right">{fmt(h.cambio?.precio_justo ?? h.valor_central, 0)}</td>
                  <td className="cifra text-right">{fmt(h.precio, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p className="rounded-md bg-amber-50 p-3 text-xs text-amber-800">
        Prueba contra la historia (V3, {backtest.fecha}): en {backtest.observaciones_motor} observaciones, el valor intrínseco tuvo una correlación de
        rangos de {fmt(backtest.spearman_motor_1a, 2)} con el retorno a 1 año; el rendimiento por dividendo, {fmt(backtest.spearman_rival_1a, 2)}.
        {backtest.supera_al_rival
          ? " El motor supera al rival simple en esta muestra."
          : " No lo supera: por eso el valor intrínseco es solo una de tres lentes y el ranking ordena por dividendo dentro de cada veredicto."}{" "}
        La muestra es corta (fundamentales desde 2019): sirve para descartar, no para probar. No es una recomendación de compra.{" "}
        <Link to="/fundamentales/aciertos" className="underline">Ver la prueba y el historial de aciertos</Link>.
      </p>
    </div>
  );
}
