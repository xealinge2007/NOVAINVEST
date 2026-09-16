import { supabase } from "../lib/supabase";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// El backend en Render (plan free) se duerme tras ~15 min sin trafico y
// tarda 30-50s en despertar en la primera peticion. Sin este aviso, esa
// espera se ve como pantalla en blanco (DescargoGate devuelve null mientras
// carga) -- parece que la app no carga, cuando en realidad esta despertando.
const EVENTO_SERVIDOR_LENTO = "novainvest:servidor-lento";
const UMBRAL_AVISO_MS = 2500;

let peticionesActivas = 0;
let avisoTimeout = null;

function marcarInicioPeticion() {
  peticionesActivas++;
  if (!avisoTimeout) {
    avisoTimeout = setTimeout(() => {
      window.dispatchEvent(new CustomEvent(EVENTO_SERVIDOR_LENTO, { detail: true }));
    }, UMBRAL_AVISO_MS);
  }
}

function marcarFinPeticion() {
  peticionesActivas = Math.max(0, peticionesActivas - 1);
  if (peticionesActivas === 0) {
    if (avisoTimeout) {
      clearTimeout(avisoTimeout);
      avisoTimeout = null;
    }
    window.dispatchEvent(new CustomEvent(EVENTO_SERVIDOR_LENTO, { detail: false }));
  }
}

async function authHeader() {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("No hay sesión activa");
  return { Authorization: `Bearer ${token}` };
}

async function peticion(metodo, ruta, cuerpo) {
  const headers = await authHeader();
  marcarInicioPeticion();
  try {
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
  } finally {
    marcarFinPeticion();
  }
}

export async function getSaludFuentes() {
  marcarInicioPeticion();
  try {
    const resp = await fetch(`${API_URL}/salud/fuentes`);
    if (!resp.ok) throw new Error(`API ${resp.status}`);
    return resp.json();
  } finally {
    marcarFinPeticion();
  }
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
  marcarInicioPeticion();
  try {
    const resp = await fetch(`${API_URL}${ruta}`, { method: "POST", headers, body: form });
    if (!resp.ok) {
      const detalle = await resp.json().catch(() => ({}));
      throw new Error(detalle.detail || `API ${resp.status}`);
    }
    return resp.json();
  } finally {
    marcarFinPeticion();
  }
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
export const getSupuestosMacro = () => peticion("GET", "/fundamentales/macro/supuestos");
export const getEvolucionFundamental = (slug) => peticion("GET", `/fundamentales/${slug}/evolucion`);

// señales
export const getSenales = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return peticion("GET", `/senales${qs ? `?${qs}` : ""}`);
};
export const getBitacoraBacktests = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return peticion("GET", `/senales/bitacora/backtests${qs ? `?${qs}` : ""}`);
};
