import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const DESCARGO = `NOVAINVEST es una herramienta analítica y educativa. No es asesoría
financiera regulada. Las decisiones de inversión y su ejecución son
exclusivamente de cada usuario. Nada se ejecuta automáticamente contra
brokers.`;

export default function Login() {
  const { login, registrar } = useAuth();
  const navigate = useNavigate();
  const [modo, setModo] = useState("login"); // login | registro
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [aceptaDescargo, setAceptaDescargo] = useState(false);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    if (modo === "registro" && !aceptaDescargo) {
      setError("Debes aceptar el descargo para crear una cuenta.");
      return;
    }
    setCargando(true);
    try {
      if (modo === "registro") {
        await registrar(email, password);
      } else {
        await login(email, password);
      }
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm flex flex-col gap-4">
        <h1 className="text-2xl font-semibold text-center">NOVAINVEST</h1>

        <div className="flex gap-2 text-sm">
          <button
            type="button"
            className={`flex-1 py-1 rounded ${modo === "login" ? "bg-slate-900 text-white" : "bg-slate-100"}`}
            onClick={() => setModo("login")}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            className={`flex-1 py-1 rounded ${modo === "registro" ? "bg-slate-900 text-white" : "bg-slate-100"}`}
            onClick={() => setModo("registro")}
          >
            Crear cuenta
          </button>
        </div>

        <input
          type="email"
          required
          placeholder="correo@ejemplo.com"
          className="border rounded px-3 py-2"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          required
          minLength={6}
          placeholder="contraseña"
          className="border rounded px-3 py-2"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {modo === "registro" && (
          <div className="text-xs text-slate-600 border rounded p-3 flex flex-col gap-2">
            <p>{DESCARGO}</p>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={aceptaDescargo}
                onChange={(e) => setAceptaDescargo(e.target.checked)}
              />
              Acepto el descargo
            </label>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={cargando}
          className="bg-slate-900 text-white rounded py-2 disabled:opacity-50"
        >
          {cargando ? "..." : modo === "registro" ? "Crear cuenta" : "Entrar"}
        </button>
      </form>
    </div>
  );
}
