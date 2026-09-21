import { useEffect, useState } from "react";
import { compararEstrategias, crearDeuda, eliminarDeuda, getMisDeudas } from "../api/client";

const NOMBRES_ESTRATEGIA = { avalancha: "Avalancha", nieve: "Bola de nieve", hibrida: "Híbrida" };
const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";

export default function Deudas() {
  const [deudas, setDeudas] = useState([]);
  const [form, setForm] = useState({ nombre: "", saldo: "", tasa_anual_pct: "", pago_minimo: "" });
  const [extraMensual, setExtraMensual] = useState("");
  const [comparacion, setComparacion] = useState(null);
  const [error, setError] = useState(null);

  async function cargar() {
    setDeudas(await getMisDeudas());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function agregar(e) {
    e.preventDefault();
    setError(null);
    try {
      await crearDeuda({
        nombre: form.nombre,
        saldo: Number(form.saldo),
        tasa_anual_pct: Number(form.tasa_anual_pct),
        pago_minimo: Number(form.pago_minimo),
      });
      setForm({ nombre: "", saldo: "", tasa_anual_pct: "", pago_minimo: "" });
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function borrar(id) {
    await eliminarDeuda(id);
    await cargar();
  }

  async function comparar(e) {
    e.preventDefault();
    setError(null);
    setComparacion(null);
    try {
      setComparacion(await compararEstrategias({ extra_mensual: Number(extraMensual) }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Deudas</h1>
      </div>

      <ul className="divide-y divide-slate-200 text-sm">
        {deudas.map((d) => (
          <li key={d.id} className="flex items-start justify-between gap-3 py-2.5">
            <span className="cifra">
              {d.nombre} — {d.saldo.toLocaleString("es-CO")} COP @ {d.tasa_anual_pct}% anual (mínimo{" "}
              {d.pago_minimo.toLocaleString("es-CO")})
            </span>
            <button onClick={() => borrar(d.id)} className="shrink-0 cursor-pointer text-xs text-red-600 hover:underline">
              eliminar
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex max-w-sm flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Agregar deuda</h2>
        <input placeholder="Nombre" className={INPUT} value={form.nombre}
          onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
        <input type="number" placeholder="Saldo (COP)" className={INPUT} value={form.saldo}
          onChange={(e) => setForm((f) => ({ ...f, saldo: e.target.value }))} required />
        <input type="number" placeholder="Tasa anual (%)" className={INPUT} value={form.tasa_anual_pct}
          onChange={(e) => setForm((f) => ({ ...f, tasa_anual_pct: e.target.value }))} required />
        <input type="number" placeholder="Pago mínimo (COP)" className={INPUT} value={form.pago_minimo}
          onChange={(e) => setForm((f) => ({ ...f, pago_minimo: e.target.value }))} required />
        <button className={BOTON}>Agregar</button>
      </form>

      <form onSubmit={comparar} className="flex max-w-sm flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Comparar estrategias</h2>
        <input type="number" placeholder="Extra disponible al mes (COP)" className={INPUT}
          value={extraMensual} onChange={(e) => setExtraMensual(e.target.value)} required />
        <button className={BOTON}>Comparar</button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {comparacion && (
        <div className="flex flex-col gap-3">
          <p className="text-sm">
            Recomendada: <b className="uppercase">{NOMBRES_ESTRATEGIA[comparacion.recomendada]}</b> —{" "}
            {comparacion.razon}
          </p>
          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="p-2 text-left text-xs uppercase tracking-wide text-slate-500">Estrategia</th>
                  <th className="p-2 text-right text-xs uppercase tracking-wide text-slate-500">Interés total</th>
                  <th className="p-2 text-right text-xs uppercase tracking-wide text-slate-500">Meses hasta liberar todo</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparacion.resultados).map(([nombre, r]) => (
                  <tr key={nombre} className="border-t border-slate-100">
                    <td className="p-2">{NOMBRES_ESTRATEGIA[nombre]}</td>
                    <td className="cifra p-2 text-right">{r.interes_total.toLocaleString("es-CO")} COP</td>
                    <td className="cifra p-2 text-right">{r.meses_totales}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
