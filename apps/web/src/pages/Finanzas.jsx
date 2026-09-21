import { useEffect, useState } from "react";
import {
  getEstadoFondoEmergencia,
  getPatrimonio,
  getPresupuesto,
  guardarFondoEmergencia,
  guardarPresupuesto,
  registrarPatrimonio,
} from "../api/client";

const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";

export default function Finanzas() {
  return (
    <div className="flex flex-col gap-10">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Finanzas personales</h1>
      </div>
      <SeccionPresupuesto />
      <SeccionFondoEmergencia />
      <SeccionPatrimonio />
    </div>
  );
}

function SeccionPresupuesto() {
  const [form, setForm] = useState({ ingreso_mensual: "", pct_necesidades: 50, pct_deseos: 30, pct_ahorro: 20 });
  const [mensaje, setMensaje] = useState(null);

  useEffect(() => {
    getPresupuesto()
      .then((p) => setForm(p))
      .catch(() => {});
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setMensaje(null);
    try {
      await guardarPresupuesto({
        ingreso_mensual: Number(form.ingreso_mensual),
        pct_necesidades: Number(form.pct_necesidades),
        pct_deseos: Number(form.pct_deseos),
        pct_ahorro: Number(form.pct_ahorro),
      });
      setMensaje("Guardado.");
    } catch (err) {
      setMensaje(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-base font-medium text-slate-900">Presupuesto 50/30/20</h2>
      <form onSubmit={onSubmit} className="flex max-w-sm flex-col gap-2">
        <input
          type="number"
          placeholder="Ingreso mensual (COP)"
          className={INPUT}
          value={form.ingreso_mensual}
          onChange={(e) => setForm((f) => ({ ...f, ingreso_mensual: e.target.value }))}
          required
        />
        <div className="flex gap-2">
          <input type="number" className={`w-1/3 ${INPUT}`} value={form.pct_necesidades}
            onChange={(e) => setForm((f) => ({ ...f, pct_necesidades: e.target.value }))} />
          <input type="number" className={`w-1/3 ${INPUT}`} value={form.pct_deseos}
            onChange={(e) => setForm((f) => ({ ...f, pct_deseos: e.target.value }))} />
          <input type="number" className={`w-1/3 ${INPUT}`} value={form.pct_ahorro}
            onChange={(e) => setForm((f) => ({ ...f, pct_ahorro: e.target.value }))} />
        </div>
        <p className="text-xs text-slate-400">necesidades / deseos / ahorro (%, deben sumar 100)</p>
        <button className={BOTON}>Guardar</button>
        {mensaje && <p className="text-sm">{mensaje}</p>}
      </form>
    </section>
  );
}

function SeccionFondoEmergencia() {
  const [form, setForm] = useState({ gastos_mensuales_estimados: "", meses_objetivo: 6, monto_actual: "" });
  const [estado, setEstado] = useState(null);
  const [mensaje, setMensaje] = useState(null);

  async function cargarEstado() {
    const e = await getEstadoFondoEmergencia();
    setEstado(e);
  }

  useEffect(() => {
    cargarEstado();
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setMensaje(null);
    try {
      await guardarFondoEmergencia({
        gastos_mensuales_estimados: Number(form.gastos_mensuales_estimados),
        meses_objetivo: Number(form.meses_objetivo),
        monto_actual: Number(form.monto_actual),
      });
      await cargarEstado();
      setMensaje("Guardado.");
    } catch (err) {
      setMensaje(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-base font-medium text-slate-900">Fondo de emergencia</h2>
      {estado && (
        <div
          className={`rounded-lg border p-3 text-sm ${
            estado.bloqueado_inversion
              ? "border-amber-200 bg-amber-50 text-amber-800"
              : "border-emerald-200 bg-emerald-50 text-emerald-800"
          }`}
        >
          {estado.bloqueado_inversion
            ? `Módulo de inversión BLOQUEADO. ${estado.motivo}`
            : `Fondo de emergencia OK (${estado.meses_cubiertos} meses cubiertos) — inversión desbloqueada.`}
        </div>
      )}
      <form onSubmit={onSubmit} className="flex max-w-sm flex-col gap-2">
        <input type="number" placeholder="Gastos mensuales estimados (COP)" className={INPUT}
          value={form.gastos_mensuales_estimados}
          onChange={(e) => setForm((f) => ({ ...f, gastos_mensuales_estimados: e.target.value }))} required />
        <input type="number" min={3} max={6} placeholder="Meses objetivo (3-6)" className={INPUT}
          value={form.meses_objetivo}
          onChange={(e) => setForm((f) => ({ ...f, meses_objetivo: e.target.value }))} required />
        <input type="number" placeholder="Monto actual ahorrado (COP)" className={INPUT}
          value={form.monto_actual}
          onChange={(e) => setForm((f) => ({ ...f, monto_actual: e.target.value }))} required />
        <button className={BOTON}>Guardar</button>
        {mensaje && <p className="text-sm">{mensaje}</p>}
      </form>
    </section>
  );
}

function SeccionPatrimonio() {
  const [form, setForm] = useState({ fecha: new Date().toISOString().slice(0, 10), activos_total: "", pasivos_total: "" });
  const [snapshots, setSnapshots] = useState([]);
  const [mensaje, setMensaje] = useState(null);

  async function cargar() {
    setSnapshots(await getPatrimonio());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setMensaje(null);
    try {
      await registrarPatrimonio({
        fecha: form.fecha,
        activos_total: Number(form.activos_total),
        pasivos_total: Number(form.pasivos_total),
      });
      await cargar();
      setMensaje("Guardado.");
    } catch (err) {
      setMensaje(err.message);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-base font-medium text-slate-900">Patrimonio neto</h2>
      <form onSubmit={onSubmit} className="flex max-w-sm flex-col gap-2">
        <input type="date" className={INPUT} value={form.fecha}
          onChange={(e) => setForm((f) => ({ ...f, fecha: e.target.value }))} required />
        <input type="number" placeholder="Activos totales (COP)" className={INPUT}
          value={form.activos_total} onChange={(e) => setForm((f) => ({ ...f, activos_total: e.target.value }))} required />
        <input type="number" placeholder="Pasivos totales (COP)" className={INPUT}
          value={form.pasivos_total} onChange={(e) => setForm((f) => ({ ...f, pasivos_total: e.target.value }))} required />
        <button className={BOTON}>Guardar snapshot</button>
        {mensaje && <p className="text-sm">{mensaje}</p>}
      </form>
      <ul className="divide-y divide-slate-200 text-sm">
        {snapshots.map((s) => (
          <li key={s.fecha} className="flex justify-between py-1.5">
            <span>{s.fecha}</span>
            <span className="cifra">{s.patrimonio_neto.toLocaleString("es-CO")} COP</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
