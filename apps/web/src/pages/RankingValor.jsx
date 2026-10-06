import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistorialRankingValor, getRankingValor } from "../api/client";
import { fmt } from "../lib/fundamentalesUtils";

// Categorías descriptivas: dicen qué se verificó, no qué hacer. Los nombres viejos (safe_cheap...) quedan por si
// la base aún no migró; la API ya los normaliza.
const CUADRANTE = {
  descuento_con_soporte: {
    texto: "Descuento con soporte",
    ayuda: "Pasa la puerta de seguridad, el valor base supera al precio en al menos 20 % del valor y hay catalizador vivo o renta sostenible.",
    clase: "bg-emerald-100 text-emerald-800",
  },
  descuento_sin_soporte: {
    texto: "Descuento sin soporte",
    ayuda: "Pasa la puerta de seguridad y tiene descuento, pero no hay catalizador ni renta sostenible: el descuento puede persistir (trampa de descuento).",
    clase: "bg-amber-100 text-amber-800",
  },
  sin_descuento: {
    texto: "Sin descuento",
    ayuda: "Pasa la puerta de seguridad, pero el precio no está al menos 20 % por debajo del valor base.",
    clase: "bg-slate-100 text-slate-700",
  },
  seguridad_no_evaluada: {
    texto: "Seguridad no evaluada",
    ayuda: "Faltan insumos para juzgar la solidez financiera: nunca es una categoría favorable.",
    clase: "bg-sky-100 text-sky-800",
  },
};
const LEGADO = { safe_cheap: "descuento_con_soporte", trampa_descuento: "descuento_sin_soporte", safe_cara: "sin_descuento" };
const RIESGO_TIPO = { datos: "Datos", deuda: "Deuda", liquidez: "Liquidez" };
const EVIDENCIA = {
  provisional: { texto: "Provisional", clase: "bg-red-50 text-red-700" },
  estructura: { texto: "Estructura", clase: "bg-amber-50 text-amber-700" },
  verificado: { texto: "Verificado", clase: "bg-emerald-50 text-emerald-700" },
};
const PUERTA = { liquidez: "Liquidez", datos: "Datos", seguridad: "Seguridad", valor: "Valor" };
const VENTAJA = { amplia: "Amplia", estrecha: "Estrecha", ninguna: "Ninguna", no_aplica: "No aplica", no_evaluable: "No evaluable" };

function Etiqueta({ def, valor }) {
  const d = def[LEGADO[valor] || valor];
  if (!d) return <span className="text-slate-400">—</span>;
  return <span title={d.ayuda} className={`rounded px-1.5 py-0.5 text-xs font-medium ${d.clase}`}>{d.texto}</span>;
}

function Historial({ f }) {
  const [filas, setFilas] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    let vivo = true;
    getHistorialRankingValor(f.emisor_id)
      .then((r) => vivo && setFilas(r))
      .catch((e) => vivo && setError(e.message));
    return () => { vivo = false; };
  }, [f.emisor_id]);
  if (error) return <p className="mt-1 text-amber-700">Historial del valor no disponible: {error}</p>;
  if (!filas) return null;
  if (filas.length === 0) return <p className="mt-1">Historial del valor: aún sin corridas guardadas.</p>;
  return (
    <div className="mt-2">
      <p className="font-semibold text-slate-700">Historial del valor base (por qué cambió)</p>
      <table className="text-right">
        <thead>
          <tr className="text-slate-500">
            <th className="pr-3 text-left font-medium">Corrida</th>
            <th className="px-2 font-medium">Valor base</th>
            <th className="px-2 font-medium">Precio</th>
            <th className="px-2 text-left font-medium">Causa</th>
          </tr>
        </thead>
        <tbody>
          {filas.slice(0, 8).map((h) => (
            <tr key={h.id}>
              <td className="pr-3 text-left">{String(h.calculado_en).slice(0, 10)}</td>
              <td className="cifra px-2">
                {fmt(h.valor_central, 0)}
                {h.cambio?.valor_cambio_pct != null ? ` (${h.cambio.valor_cambio_pct >= 0 ? "+" : ""}${fmt(h.cambio.valor_cambio_pct, 1)}%)` : ""}
              </td>
              <td className="cifra px-2">{fmt(h.precio, 0)}</td>
              <td className="px-2 text-left">{(h.cambio?.causas || []).join("; ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
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
        {d.liquidez?.mediana_cop !== null && d.liquidez?.mediana_cop !== undefined && (
          <p className="mt-1">
            Liquidez: mediana de {fmt(d.liquidez.mediana_cop / 1e6, 0)} millones al día ({d.liquidez.sesiones_con_negociacion}/{d.liquidez.sesiones}{" "}
            sesiones). Tamaño máximo sugerido de una posición: ~{fmt(d.liquidez.tamano_maximo_cop / 1e6, 0)} millones (unas 5 sesiones al 10% del volumen).
          </p>
        )}
        {d.fechas && (
          <p className="mt-1">
            Balance a {d.fechas.balance || "—"}; resultados: {d.fechas.resultados || "—"}
            {d.fechas.desfase_trimestres > 0 ? ` (${d.fechas.desfase_trimestres} trimestre(s) más viejos que el balance)` : ""}.
          </p>
        )}
        {d.renta?.distribucion && (
          <p className="mt-1 text-amber-700">
            Distribución anualizada: {fmt(d.renta.distribucion.por_titulo_anual, 0)} por título ({fmt(d.renta.distribucion.rendimiento_pct)}% sobre el
            precio). No se cuenta como renta: buena parte fue restitución de capital, no utilidad.
          </p>
        )}
        <p className="mt-1">
          Dividendo: {fmt(d.renta?.yield_pct)}% sobre el precio, payout {fmt(d.renta?.payout_pct, 0)}%.
        </p>
      </div>
      <div className="sm:col-span-2">
        <p className="font-semibold text-slate-700">Riesgos que acompañan a la categoría</p>
        {(d.riesgos || []).length === 0 ? <p>—</p> : (
          <ul className="list-disc pl-4">
            {d.riesgos.map((r, i) => (
              <li key={i}><strong>{RIESGO_TIPO[r.tipo] || r.tipo}:</strong> {r.texto}</li>
            ))}
          </ul>
        )}
        {d.retorno_ilustrativo && (
          <p className="mt-1">
            <strong>Retorno anual ilustrativo: {d.retorno_ilustrativo.retorno_pct >= 0 ? "+" : ""}{fmt(d.retorno_ilustrativo.retorno_pct, 1)}%</strong>{" "}
            ({fmt(d.retorno_ilustrativo.por_precio_pct, 1)}% por precio + {fmt(d.retorno_ilustrativo.por_renta_pct, 1)}% por renta, a {d.retorno_ilustrativo.horizonte_anios} años).{" "}
            {d.retorno_ilustrativo.supuestos}.
          </p>
        )}
        <Historial f={f} />
      </div>
      {d.sensibilidad_nav && (
        <div className="sm:col-span-2">
          <p className="font-semibold text-slate-700">Sensibilidad del NAV por título al cap rate y a la vacancia</p>
          <p>
            Cap rate de los libros {fmt(d.sensibilidad_nav.cap_rate_libros_pct, 2)}%. Para que el NAV igualara el precio haría falta un cap rate de{" "}
            {fmt(d.sensibilidad_nav.cap_rate_implicito_en_precio_pct, 2)}% (+{fmt(d.sensibilidad_nav.brecha_bps, 0)} pb): eso es lo que el precio descuenta.
          </p>
          <div className="mt-1 overflow-x-auto">
            <table className="text-right">
              <thead>
                <tr className="text-slate-500">
                  <th className="pr-3 text-left font-medium">Cap rate</th>
                  <th className="px-2 font-medium">Vacancia +0 pp</th>
                  <th className="px-2 font-medium">+3 pp</th>
                  <th className="px-2 font-medium">+6 pp</th>
                </tr>
              </thead>
              <tbody>
                {d.sensibilidad_nav.matriz.map((m) => (
                  <tr key={m.delta_bps} className={m.delta_bps === 0 ? "font-semibold text-slate-800" : ""}>
                    <td className="pr-3 text-left">{fmt(m.cap_rate_pct, 2)}% ({m.delta_bps >= 0 ? "+" : ""}{m.delta_bps} pb)</td>
                    <td className="cifra px-2">{fmt(m.vacancia_mas_0pp, 0)}</td>
                    <td className="cifra px-2">{fmt(m.vacancia_mas_3pp, 0)}</td>
                    <td className="cifra px-2">{fmt(m.vacancia_mas_6pp, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-1 text-slate-500">{d.sensibilidad_nav.advertencia}. {d.sensibilidad_nav.supuestos}.</p>
        </div>
      )}
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
          acción determinable — y solo entonces se ordena por el margen de seguridad de su valor base frente al precio.
          El valor es un rango de escenarios (bajo / base / alto) que cambia supuestos de utilidad y costo de capital:
          no son percentiles ni probabilidades. El margen de seguridad y la subida al valor base no son un retorno
          esperado, porque no tienen horizonte; el retorno anual ilustrativo sí declara uno (3 años), pero es condicional a que el precio converja al valor y no es un pronóstico.{" "}
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
                <th className="px-3 py-2" title="Categoría descriptiva; pasa el cursor sobre ella para ver su definición">Categoría</th>
                <th className="px-3 py-2 text-right" title="Escenarios de supuestos, no percentiles ni probabilidades">Escenarios por acción (bajo · base · alto)</th>
                <th className="px-3 py-2 text-right">Precio</th>
                <th className="px-3 py-2 text-right" title="(valor base − precio) / valor base">Margen de seguridad</th>
                <th className="px-3 py-2 text-right" title="valor base / precio − 1. No es un retorno esperado: no tiene horizonte">Subida al valor base</th>
                <th className="px-3 py-2 text-right" title="Si el precio converge al valor base en 3 años, más la renta solo si es sostenible. Es ilustrativo y condicional: no es un pronóstico">Retorno anual ilustrativo (3 años)</th>
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
                <span className="flex-1 text-xs text-slate-500">
                  {f.motivo_exclusion}
                  {f.valor_central !== null && f.valor_central !== undefined && (
                    <span className="mt-0.5 block text-slate-600">
                      Valor de referencia (no rankeado): {fmt(f.valor_bajo, 0)} · <strong>{fmt(f.valor_central, 0)}</strong> · {fmt(f.valor_alto, 0)} contra un precio de {fmt(f.precio, 0)}
                      {f.margen_seguridad_pct !== null && f.margen_seguridad_pct !== undefined ? ` (margen ${fmt(f.margen_seguridad_pct, 0)}%)` : ""}.
                    </span>
                  )}
                </span>
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
        <td className="cifra px-3 py-2 text-right text-slate-600">
          {f.detalle?.subida_pct === null || f.detalle?.subida_pct === undefined ? "—" : `${f.detalle.subida_pct >= 0 ? "+" : ""}${fmt(f.detalle.subida_pct, 0)}%`}
        </td>
        <td className="cifra px-3 py-2 text-right text-slate-600">
          {f.detalle?.retorno_ilustrativo ? `${f.detalle.retorno_ilustrativo.retorno_pct >= 0 ? "+" : ""}${fmt(f.detalle.retorno_ilustrativo.retorno_pct, 1)}%` : "—"}
        </td>
        <td className="px-3 py-2 text-xs text-slate-600">{VENTAJA[f.ventaja_nivel] || "—"}</td>
        <td className="px-3 py-2"><Etiqueta def={EVIDENCIA} valor={f.nivel_evidencia} /></td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={10} className="p-0"><Detalle f={f} /></td>
        </tr>
      )}
    </>
  );
}
