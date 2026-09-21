import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { borrarMiCuenta, exportarMisDatos } from "../api/client";
import { supabase } from "../lib/supabase";

const INPUT = "rounded-md border border-slate-300 px-3 py-2 focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20";
const BOTON = "max-w-xs rounded-md bg-brand-900 py-2 text-white hover:opacity-90 cursor-pointer";
const BOTON_SECUNDARIO = "max-w-xs rounded-md border border-slate-300 py-2 hover:border-brand-700 cursor-pointer";

export default function Cuenta() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();
  const [qr, setQr] = useState(null);
  const [factorId, setFactorId] = useState(null);
  const [codigo, setCodigo] = useState("");
  const [mensaje2fa, setMensaje2fa] = useState(null);
  const [mensaje, setMensaje] = useState(null);

  async function iniciarEnrolamiento2fa() {
    const { data, error } = await supabase.auth.mfa.enroll({ factorType: "totp" });
    if (error) {
      setMensaje2fa(error.message);
      return;
    }
    setFactorId(data.id);
    setQr(data.totp.qr_code);
  }

  async function verificar2fa(e) {
    e.preventDefault();
    const { data: challenge, error: errChallenge } = await supabase.auth.mfa.challenge({ factorId });
    if (errChallenge) {
      setMensaje2fa(errChallenge.message);
      return;
    }
    const { error } = await supabase.auth.mfa.verify({ factorId, challengeId: challenge.id, code: codigo });
    if (error) {
      setMensaje2fa(error.message);
      return;
    }
    setMensaje2fa("2FA activado.");
    setQr(null);
  }

  async function exportar() {
    const datos = await exportarMisDatos();
    const blob = new Blob([JSON.stringify(datos, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mis-datos-novainvest.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function borrarCuenta() {
    if (!confirm("Esto borra tu cuenta y todos tus datos de forma permanente. ¿Continuar?")) return;
    setMensaje(null);
    try {
      await borrarMiCuenta();
      await logout();
      navigate("/login");
    } catch (err) {
      setMensaje(err.message);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="border-b border-slate-200 pb-4">
        <h1 className="font-serif text-2xl font-semibold text-slate-900">Mi cuenta</h1>
        <p className="mt-1 text-sm text-slate-600">{usuario?.email}</p>
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Verificación en dos pasos (opcional)</h2>
        {!qr ? (
          <button onClick={iniciarEnrolamiento2fa} className={BOTON}>
            Activar 2FA
          </button>
        ) : (
          <form onSubmit={verificar2fa} className="flex max-w-xs flex-col gap-2">
            <img src={qr} alt="QR 2FA" className="h-40 w-40 rounded-md border border-slate-200" />
            <input
              placeholder="Código de 6 dígitos"
              className={INPUT}
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
            <button className={BOTON}>Verificar</button>
          </form>
        )}
        {mensaje2fa && <p className="text-sm">{mensaje2fa}</p>}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-serif text-base font-medium text-slate-900">Mis datos</h2>
        <button onClick={exportar} className={BOTON_SECUNDARIO}>
          Exportar mis datos (JSON)
        </button>
        <button onClick={borrarCuenta} className="max-w-xs cursor-pointer rounded-md border border-red-300 py-2 text-red-600 hover:bg-red-50">
          Borrar mi cuenta
        </button>
        {mensaje && <p className="text-sm text-red-600">{mensaje}</p>}
      </section>
    </div>
  );
}
