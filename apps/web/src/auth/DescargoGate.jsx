import { useEffect, useState } from "react";
import { aceptarDescargo, getDescargoAceptado } from "../api/client";
import MarcaNovainvest from "../components/Marca";

const DESCARGO = `NOVAINVEST es una herramienta analítica y educativa. No es asesoría
financiera regulada. Las decisiones de inversión y su ejecución son
exclusivamente de cada usuario. Nada se ejecuta automáticamente contra
brokers.`;

/** Bloquea el resto de la app hasta que el usuario acepte el descargo —
 * cubre tanto el registro normal como el caso de confirmación de email
 * (donde la sesión llega después del signUp, no en el mismo instante). */
export default function DescargoGate({ children }) {
  const [aceptado, setAceptado] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDescargoAceptado()
      .then((r) => setAceptado(r.aceptado))
      .catch(() => setAceptado(false));
  }, []);

  if (aceptado === null) return null;
  if (aceptado) return children;

  async function aceptar() {
    setGuardando(true);
    setError(null);
    try {
      await aceptarDescargo();
      setAceptado(true);
    } catch (err) {
      setError(err.message || "No se pudo guardar. Intenta de nuevo.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md flex flex-col items-center gap-4 rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
        <MarcaNovainvest className="h-6 w-6 text-slate-300" />
        <h2 className="font-serif text-xl font-semibold text-brand-900">Antes de continuar</h2>
        <p className="text-sm leading-relaxed text-slate-600">{DESCARGO}</p>
        <button
          onClick={aceptar}
          disabled={guardando}
          className="w-full rounded-lg bg-brand-900 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50 cursor-pointer"
        >
          {guardando ? "Guardando…" : "Acepto y continúo"}
        </button>
        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600" role="alert">
            {error}. Si el servidor estaba dormido, puede tardar hasta 50s en despertar — intenta de nuevo.
          </p>
        )}
      </div>
    </div>
  );
}
