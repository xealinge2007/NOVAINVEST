const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getSaludFuentes() {
  const resp = await fetch(`${API_URL}/salud/fuentes`);
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json();
}
