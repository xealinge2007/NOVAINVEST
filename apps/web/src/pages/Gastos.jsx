import { useEffect, useRef, useState } from "react";
import { getMisGastos, importarExtracto, registrarGastoManual } from "../api/client";

const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";

export default function Gastos() {
  const [gastos, setGastos] = useState([]);
  const [form, setForm] = useState({
    fecha: new Date().toISOString().slice(0, 10),
    monto: "",
    categoria: "",
    descripcion: "",
  });
  const [mensajeImport, setMensajeImport] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  async function cargar() {
    setGastos(await getMisGastos());
  }

  useEffect(() => {
    cargar();
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await registrarGastoManual({
        fecha: form.fecha,
        monto: Number(form.monto),
        categoria: form.categoria,
        descripcion: form.descripcion || null,
      });
      setForm((f) => ({ ...f, monto: "", descripcion: "" }));
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onImportar(e) {
    e.preventDefault();
    setMensajeImport(null);
    setError(null);
    const archivo = fileRef.current.files[0];
    if (!archivo) return;
    try {
      const res = await importarExtracto(archivo);
      setMensajeImport(
        `${res.fusionados} gasto(s) conciliado(s) sin duplicar, ${res.nuevos} nuevo(s) importado(s) de ${res.total_filas_procesadas} fila(s).`
      );
      await cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Gastos</h1>
      </div>

      <form onSubmit={onSubmit} className="flex max-w-sm flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Registrar gasto manual</h2>
        <input type="date" className={INPUT} value={form.fecha}
          onChange={(e) => setForm((f) => ({ ...f, fecha: e.target.value }))} required />
        <input type="number" placeholder="Monto (COP)" className={INPUT} value={form.monto}
          onChange={(e) => setForm((f) => ({ ...f, monto: e.target.value }))} required />
        <input placeholder="Categoría (ej. comida)" className={INPUT} value={form.categoria}
          onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))} required />
        <input placeholder="Descripción (opcional)" className={INPUT} value={form.descripcion}
          onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))} />
        <button className={BOTON}>Registrar</button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>

      <form onSubmit={onImportar} className="flex max-w-sm flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">
          Importar extracto (CSV: fecha,monto,descripcion)
        </h2>
        <input type="file" accept=".csv" ref={fileRef} className="text-sm" />
        <button className={BOTON}>Importar</button>
        {mensajeImport && <p className="text-sm text-emerald-700">{mensajeImport}</p>}
      </form>

      <ul className="divide-y divide-slate-200 text-sm">
        {gastos.map((g) => (
          <li key={g.id} className="flex justify-between py-2.5">
            <span>
              {g.fecha} · {g.categoria} · {g.descripcion || "—"}{" "}
              <span className="text-xs text-slate-400">({g.origen})</span>
            </span>
            <span className="cifra">{g.monto.toLocaleString("es-CO")} COP</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
