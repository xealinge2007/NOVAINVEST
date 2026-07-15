import { useEffect, useState } from "react";
import { compararEstrategias, crearDeuda, eliminarDeuda, getMisDeudas } from "../api/client";

const NOMBRES_ESTRATEGIA = { avalancha: "Avalancha", nieve: "Bola de nieve", hibrida: "Híbrida" };

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
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-8">
      <h1 className="text-2xl font-semibold">Deudas</h1>

      <ul className="divide-y text-sm">
        {deudas.map((d) => (
          <li key={d.id} className="py-2 flex justify-between items-center">
            <span>
              {d.nombre} — {d.saldo.toLocaleString("es-CO")} COP @ {d.tasa_anual_pct}% anual (mínimo{" "}
              {d.pago_minimo.toLocaleString("es-CO")})
            </span>
            <button onClick={() => borrar(d.id)} className="text-red-600 text-xs">
              eliminar
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={agregar} className="flex flex-col gap-2 max-w-sm">
        <h2 className="font-medium">Agregar deuda</h2>
        <input placeholder="Nombre" className="border rounded px-3 py-2" value={form.nombre}
          onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
        <input type="number" placeholder="Saldo (COP)" className="border rounded px-3 py-2" value={form.saldo}
          onChange={(e) => setForm((f) => ({ ...f, saldo: e.target.value }))} required />
        <input type="number" placeholder="Tasa anual (%)" className="border rounded px-3 py-2" value={form.tasa_anual_pct}
          onChange={(e) => setForm((f) => ({ ...f, tasa_anual_pct: e.target.value }))} required />
        <input type="number" placeholder="Pago mínimo (COP)" className="border rounded px-3 py-2" value={form.pago_minimo}
          onChange={(e) => setForm((f) => ({ ...f, pago_minimo: e.target.value }))} required />
        <button className="bg-slate-900 text-white rounded py-2">Agregar</button>
      </form>

      <form onSubmit={comparar} className="flex flex-col gap-2 max-w-sm">
        <h2 className="font-medium">Comparar estrategias</h2>
        <input type="number" placeholder="Extra disponible al mes (COP)" className="border rounded px-3 py-2"
          value={extraMensual} onChange={(e) => setExtraMensual(e.target.value)} required />
        <button className="bg-slate-900 text-white rounded py-2">Comparar</button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {comparacion && (
        <div className="flex flex-col gap-3">
          <p className="text-sm">
            Recomendada: <b className="uppercase">{NOMBRES_ESTRATEGIA[comparacion.recomendada]}</b> —{" "}
            {comparacion.razon}
          </p>
          <table className="text-sm w-full border">
            <thead>
              <tr className="bg-slate-100">
                <th className="text-left p-2">Estrategia</th>
                <th className="text-right p-2">Interés total</th>
                <th className="text-right p-2">Meses hasta liberar todo</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(comparacion.resultados).map(([nombre, r]) => (
                <tr key={nombre} className="border-t">
                  <td className="p-2">{NOMBRES_ESTRATEGIA[nombre]}</td>
                  <td className="p-2 text-right">{r.interes_total.toLocaleString("es-CO")} COP</td>
                  <td className="p-2 text-right">{r.meses_totales}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
