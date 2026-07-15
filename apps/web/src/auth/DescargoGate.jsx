import { useEffect, useState } from "react";
import { aceptarDescargo, getDescargoAceptado } from "../api/client";

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

  useEffect(() => {
    getDescargoAceptado()
      .then((r) => setAceptado(r.aceptado))
      .catch(() => setAceptado(false));
  }, []);

  if (aceptado === null) return null;
  if (aceptado) return children;

  async function aceptar() {
    setGuardando(true);
    await aceptarDescargo();
    setAceptado(true);
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md flex flex-col gap-4 text-center">
        <h2 className="text-xl font-semibold">Antes de continuar</h2>
        <p className="text-sm text-slate-600">{DESCARGO}</p>
        <button
          onClick={aceptar}
          disabled={guardando}
          className="bg-slate-900 text-white rounded py-2 disabled:opacity-50"
        >
          Acepto y continúo
        </button>
      </div>
    </div>
  );
}
