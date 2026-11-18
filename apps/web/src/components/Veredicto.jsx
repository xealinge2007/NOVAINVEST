// Veredicto por consenso de 3 lentes (V2 del plan v4): intrínseco, propia historia y pares.
export const VEREDICTO = {
  infravalorada: { texto: "Infravalorada", clase: "bg-emerald-100 text-emerald-800" },
  en_precio: { texto: "En su precio", clase: "bg-slate-100 text-slate-700" },
  sobrevalorada: { texto: "Sobrevalorada", clase: "bg-red-100 text-red-800" },
  senales_mixtas: { texto: "Señales mixtas", clase: "bg-amber-100 text-amber-800" },
  no_determinable: { texto: "No determinable", clase: "bg-slate-50 text-slate-400" },
};
export const LENTE = { intrinseco: "Valor intrínseco", historia: "Su propia historia", pares: "Sus pares" };
export const INCERTIDUMBRE = { baja: "baja", media: "media", alta: "alta" };

export function VeredictoChip({ consenso }) {
  const v = VEREDICTO[consenso?.veredicto] || VEREDICTO.no_determinable;
  const ayuda = consenso?.votos
    ? Object.entries(consenso.votos).map(([k, x]) => `${LENTE[k]}: ${(VEREDICTO[x] || VEREDICTO.no_determinable).texto}`).join(" · ")
    : "";
  return (
    <span title={ayuda} className={`whitespace-nowrap rounded px-1.5 py-0.5 text-xs font-medium ${v.clase}`}>
      {v.texto}
      {consenso?.incertidumbre ? <span className="font-normal opacity-70"> · incert. {consenso.incertidumbre}</span> : null}
    </span>
  );
}
