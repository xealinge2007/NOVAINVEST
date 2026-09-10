import { supabase } from "../lib/supabase";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function authHeader() {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("No hay sesión activa");
  return { Authorization: `Bearer ${token}` };
}

async function peticion(metodo, ruta, cuerpo) {
  const headers = await authHeader();
  const resp = await fetch(`${API_URL}${ruta}`, {
    method: metodo,
    headers: cuerpo ? { ...headers, "Content-Type": "application/json" } : headers,
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  if (!resp.ok) {
    const detalle = await resp.json().catch(() => ({}));
    throw new Error(detalle.detail || `API ${resp.status}`);
  }
  return resp.json();
}

export async function getSaludFuentes() {
  const resp = await fetch(`${API_URL}/salud/fuentes`);
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json();
}

// perfil
export const responderCuestionario = (body) => peticion("POST", "/perfil/cuestionario", body);
export const getMiPerfil = () => peticion("GET", "/perfil/mio");

// finanzas
export const guardarPresupuesto = (body) => peticion("PUT", "/finanzas/presupuesto", body);
export const getPresupuesto = () => peticion("GET", "/finanzas/presupuesto");
export const registrarPatrimonio = (body) => peticion("POST", "/finanzas/patrimonio", body);
export const getPatrimonio = () => peticion("GET", "/finanzas/patrimonio");
export const guardarFondoEmergencia = (body) => peticion("PUT", "/finanzas/fondo-emergencia", body);
export const getEstadoFondoEmergencia = () => peticion("GET", "/finanzas/fondo-emergencia/estado");

// deudas
export const crearDeuda = (body) => peticion("POST", "/deudas", body);
export const getMisDeudas = () => peticion("GET", "/deudas");
export const eliminarDeuda = (id) => peticion("DELETE", `/deudas/${id}`);
export const compararEstrategias = (body) => peticion("POST", "/deudas/comparar", body);

// gastos
export const registrarGastoManual = (body) => peticion("POST", "/gastos/manual", body);
export const getMisGastos = () => peticion("GET", "/gastos");

async function subirArchivo(ruta, archivo) {
  const headers = await authHeader();
  const form = new FormData();
  form.append("archivo", archivo);
  const resp = await fetch(`${API_URL}${ruta}`, { method: "POST", headers, body: form });
  if (!resp.ok) {
    const detalle = await resp.json().catch(() => ({}));
    throw new Error(detalle.detail || `API ${resp.status}`);
  }
  return resp.json();
}

export const importarExtracto = (archivo) => subirArchivo("/gastos/importar-extracto", archivo);

// cuenta
export const aceptarDescargo = () => peticion("POST", "/cuenta/aceptar-descargo");
export const getDescargoAceptado = () => peticion("GET", "/cuenta/descargo-aceptado");
export const exportarMisDatos = () => peticion("GET", "/cuenta/exportar");
export const borrarMiCuenta = () => peticion("DELETE", "/cuenta/mi-cuenta");

// objetivos
export const crearObjetivo = (body) => peticion("POST", "/objetivos", body);
export const getMisObjetivos = () => peticion("GET", "/objetivos");
export const actualizarAvanceObjetivo = (id, body) => peticion("PUT", `/objetivos/${id}/avance`, body);
export const eliminarObjetivo = (id) => peticion("DELETE", `/objetivos/${id}`);
export const getMonteCarloObjetivo = (id) => peticion("GET", `/objetivos/${id}/monte-carlo`);

// portafolio
export const crearPosicion = (body) => peticion("POST", "/portafolio/posiciones", body);
export const getMisPosiciones = () => peticion("GET", "/portafolio/posiciones");
export const eliminarPosicion = (id) => peticion("DELETE", `/portafolio/posiciones/${id}`);
export const getMetricasPortafolio = () => peticion("GET", "/portafolio/metricas");
export const calcularOptimizador = (body) => peticion("POST", "/portafolio/optimizador", body);
export const importarExtractoBroker = (archivo) => subirArchivo("/portafolio/importar-broker", archivo);

// rebalanceo
export const calcularRebalanceo = (body) => peticion("POST", "/rebalanceo", body);

// etf
export const getFichaEtf = (ticker) => peticion("GET", `/etf/${ticker}`);
export const getSolapamientoEtf = (a, b) => peticion("GET", `/etf/solapamiento/${a}/${b}`);

// fundamentales
export const getFundamentales = () => peticion("GET", "/fundamentales");
export const getFundamentalDetalle = (slug) => peticion("GET", `/fundamentales/${slug}`);

// señales
export const getSenales = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return peticion("GET", `/senales${qs ? `?${qs}` : ""}`);
};
export const getBitacoraBacktests = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return peticion("GET", `/senales/bitacora/backtests${qs ? `?${qs}` : ""}`);
};
