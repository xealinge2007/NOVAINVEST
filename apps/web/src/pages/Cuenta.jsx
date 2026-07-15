import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { borrarMiCuenta, exportarMisDatos } from "../api/client";
import { supabase } from "../lib/supabase";

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
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-8">
      <h1 className="text-2xl font-semibold">Mi cuenta</h1>
      <p className="text-sm text-slate-600">{usuario?.email}</p>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Verificación en dos pasos (opcional)</h2>
        {!qr ? (
          <button onClick={iniciarEnrolamiento2fa} className="bg-slate-900 text-white rounded py-2 max-w-xs">
            Activar 2FA
          </button>
        ) : (
          <form onSubmit={verificar2fa} className="flex flex-col gap-2 max-w-xs">
            <img src={qr} alt="QR 2FA" className="w-40 h-40" />
            <input
              placeholder="Código de 6 dígitos"
              className="border rounded px-3 py-2"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
            <button className="bg-slate-900 text-white rounded py-2">Verificar</button>
          </form>
        )}
        {mensaje2fa && <p className="text-sm">{mensaje2fa}</p>}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="font-medium">Mis datos</h2>
        <button onClick={exportar} className="border rounded py-2 max-w-xs">
          Exportar mis datos (JSON)
        </button>
        <button onClick={borrarCuenta} className="border border-red-600 text-red-600 rounded py-2 max-w-xs">
          Borrar mi cuenta
        </button>
        {mensaje && <p className="text-sm text-red-600">{mensaje}</p>}
      </section>
    </div>
  );
}
