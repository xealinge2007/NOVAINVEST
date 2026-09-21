import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import MarcaNovainvest from "../components/Marca";

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
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <MarcaNovainvest className="h-7 w-7 text-slate-300" />
          <h1 className="text-center font-serif text-2xl font-semibold tracking-tight text-brand-900">
            NOVAINVEST
          </h1>
        </div>

        <form
          onSubmit={onSubmit}
          className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
            <button
              type="button"
              className={`flex-1 rounded-md py-1.5 font-medium transition-colors cursor-pointer ${
                modo === "login" ? "bg-white text-brand-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
              onClick={() => setModo("login")}
            >
              Iniciar sesión
            </button>
            <button
              type="button"
              className={`flex-1 rounded-md py-1.5 font-medium transition-colors cursor-pointer ${
                modo === "registro" ? "bg-white text-brand-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
              onClick={() => setModo("registro")}
            >
              Crear cuenta
            </button>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-sm font-medium text-slate-700">
              Correo
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              placeholder="correo@ejemplo.com"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              autoComplete={modo === "registro" ? "new-password" : "current-password"}
              placeholder="mínimo 6 caracteres"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {modo === "registro" && (
            <div className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
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

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={cargando}
            className="rounded-lg bg-brand-900 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50 cursor-pointer"
          >
            {cargando ? "..." : modo === "registro" ? "Crear cuenta" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
