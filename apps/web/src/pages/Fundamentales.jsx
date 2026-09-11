import { useEffect, useState } from "react";
import { getFundamentales } from "../api/client";

function fmt(v, dec = 1) {
  if (v === null || v === undefined) return "—";
  return Number(v).toLocaleString("es-CO", { maximumFractionDigits: dec, minimumFractionDigits: 0 });
}

export default function Fundamentales() {
  const [filas, setFilas] = useState([]);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [expandido, setExpandido] = useState(null);

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

  return (
    <div className="max-w-6xl mx-auto p-6 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Fundamentales BVC</h1>
        <p className="text-sm text-slate-500">
          Análisis fundamental de los emisores de la Bolsa de Valores de Colombia: TTM de resultados,
          márgenes, ROE, múltiplos de mercado y creación de valor (ROIC vs. costo de capital). Doble canal
          (PDF + XBRL radicado ante la Superfinanciera). No es asesoría financiera ni recomendación de inversión.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {cargando && <p className="text-sm text-slate-500">Cargando…</p>}
      {!cargando && filas.length === 0 && <p className="text-sm text-slate-500">Todavía no hay análisis cargado.</p>}

      {filas.length > 0 && (
        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Emisor</th>
                <th className="px-3 py-2">Sector</th>
                <th className="px-3 py-2 text-right">Precio</th>
                <th className="px-3 py-2 text-right">Cap. (MMM)</th>
                <th className="px-3 py-2 text-right">P/E</th>
                <th className="px-3 py-2 text-right">P/VL</th>
                <th className="px-3 py-2 text-right">Margen neto</th>
                <th className="px-3 py-2 text-right">ROE</th>
                <th className="px-3 py-2 text-right">Deuda/Patr.</th>
                <th className="px-3 py-2 text-right">ROIC</th>
                <th className="px-3 py-2 text-right">WACC</th>
                <th className="px-3 py-2 text-right">Spread</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <>
                  <tr
                    key={f.emisor_id}
                    className="border-t hover:bg-slate-50 cursor-pointer"
                    onClick={() => setExpandido(expandido === f.emisor_id ? null : f.emisor_id)}
                  >
                    <td className="px-3 py-2">
                      <div className="font-medium">{f.nombre}</div>
                      <div className="text-xs text-slate-400">{f.ticker}</div>
                    </td>
                    <td className="px-3 py-2 text-slate-500">{f.sector || "—"}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.precio, 0)}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.capitalizacion_mmm)}</td>
                    <td className="px-3 py-2 text-right">
                      {fmt(f.per)}
                      {f.alerta_multiplos && <span title={f.alerta_multiplos} className="ml-1 text-amber-600">⚠</span>}
                    </td>
                    <td className="px-3 py-2 text-right">{fmt(f.precio_valor_libro)}</td>
                    <td className="px-3 py-2 text-right">{f.margen_neto === null ? "—" : `${fmt(f.margen_neto)}%`}</td>
                    <td className="px-3 py-2 text-right">{f.roe === null ? "—" : `${fmt(f.roe)}%`}</td>
                    <td className="px-3 py-2 text-right">{fmt(f.deuda_patrimonio, 2)}</td>
                    <td className="px-3 py-2 text-right">{f.roic === null ? "—" : `${fmt(f.roic)}%`}</td>
                    <td className="px-3 py-2 text-right">{f.wacc === null ? "—" : `${fmt(f.wacc)}%`}</td>
                    <td className={`px-3 py-2 text-right font-medium ${
                      f.spread_valor === null ? "" : f.spread_valor >= 0 ? "text-emerald-700" : "text-red-700"
                    }`}>
                      {f.spread_valor === null ? "—" : `${f.spread_valor >= 0 ? "+" : ""}${fmt(f.spread_valor)}pp`}
                    </td>
                  </tr>
                  {expandido === f.emisor_id && (
                    <tr key={`${f.emisor_id}-detalle`} className="border-t bg-slate-50/60">
                      <td colSpan={12} className="px-3 py-3">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                          <Dato etiqueta="Ingresos TTM" valor={fmt(f.ingresos_ttm)} />
                          <Dato etiqueta="Utilidad neta TTM" valor={fmt(f.utilidad_neta_ttm)} />
                          <Dato etiqueta="EBITDA TTM" valor={fmt(f.ebitda_ttm)} />
                          <Dato etiqueta="Patrimonio" valor={fmt(f.patrimonio)} />
                          <Dato etiqueta="Activos" valor={fmt(f.activos)} />
                          <Dato etiqueta="Deuda financiera" valor={fmt(f.deuda_financiera)} />
                          <Dato etiqueta="EPS (COP)" valor={fmt(f.eps_cop, 2)} />
                          <Dato etiqueta="Acciones" valor={fmt(f.acciones, 0)} />
                          <Dato etiqueta="Beta vs. COLCAP" valor={fmt(f.beta, 2)} />
                          <Dato etiqueta="Costo de patrimonio" valor={f.costo_patrimonio === null ? "—" : `${fmt(f.costo_patrimonio)}%`} />
                          <Dato etiqueta="Costo de deuda (dt)" valor={f.costo_deuda_dt === null ? "—" : `${fmt(f.costo_deuda_dt)}%`} />
                          <Dato etiqueta="EVA (MMM)" valor={fmt(f.eva_mmm)} />
                          <Dato etiqueta="Clase de precio" valor={f.clase_precio || "—"} />
                          <Dato etiqueta="Serie de resultados" valor={f.serie_resultados || "—"} />
                          <Dato etiqueta="Fuente resultados" valor={f.fuente_resultados || "—"} />
                          <Dato etiqueta="Fuente ingresos" valor={f.fuente_ingresos || "—"} />
                          <Dato etiqueta="Balance de" valor={f.balance_de || "—"} />
                          <Dato etiqueta="Acciones de" valor={f.acciones_de || "—"} />
                          <Dato etiqueta="Períodos con cifras" valor={f.periodos_con_cifras ?? "—"} />
                          <Dato etiqueta="Actualizado" valor={f.actualizado_en ? new Date(f.actualizado_en).toLocaleString("es-CO") : "—"} />
                        </div>
                        {f.filas_descartadas_por_escala && (
                          <p className="text-xs text-amber-700 mt-2">⚠ Descartadas por escala: {f.filas_descartadas_por_escala}</p>
                        )}
                        {f.alerta_multiplos && <p className="text-xs text-amber-700 mt-2">⚠ {f.alerta_multiplos}</p>}
                        {f.motivo_sin_roic && <p className="text-xs text-slate-400 mt-2">Sin ROIC/WACC: {f.motivo_sin_roic}</p>}
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Dato({ etiqueta, valor }) {
  return (
    <div>
      <p className="text-slate-400">{etiqueta}</p>
      <p className="font-medium text-slate-800">{valor}</p>
    </div>
  );
}
