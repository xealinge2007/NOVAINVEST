// Debe coincidir exactamente con los ids q1..q14 que espera
// app/services/perfil_scoring.py (bloques capacidad/tolerancia/experiencia/liquidez).
export const PREGUNTAS_PERFIL = [
  {
    bloque: "Capacidad (40%)",
    id: "q1",
    texto: "¿Cuánto tiempo antes de necesitar este dinero?",
    opciones: [
      { valor: 1, texto: "Menos de 1 año" },
      { valor: 2, texto: "1 a 3 años" },
      { valor: 3, texto: "3 a 7 años" },
      { valor: 4, texto: "Más de 7 años" },
    ],
  },
  {
    bloque: "Capacidad (40%)",
    id: "q2",
    texto: "¿Qué tan estable es tu ingreso principal?",
    opciones: [
      { valor: 1, texto: "Muy inestable" },
      { valor: 2, texto: "Variable" },
      { valor: 3, texto: "Estable" },
      { valor: 4, texto: "Muy estable (empleo formal, negocio consolidado)" },
    ],
  },
  {
    bloque: "Capacidad (40%)",
    id: "q3",
    texto: "¿Cuántos dependientes económicos tienes?",
    opciones: [
      { valor: 1, texto: "4 o más" },
      { valor: 2, texto: "2 a 3" },
      { valor: 3, texto: "1" },
      { valor: 4, texto: "Ninguno" },
    ],
  },
  {
    bloque: "Capacidad (40%)",
    id: "q4",
    texto: "¿Cuántos meses de gastos cubre tu fondo de emergencia actual?",
    opciones: [
      { valor: 1, texto: "0 meses" },
      { valor: 2, texto: "1 a 2 meses" },
      { valor: 3, texto: "3 a 5 meses" },
      { valor: 4, texto: "6 meses o más" },
    ],
  },
  {
    bloque: "Tolerancia (30%)",
    id: "q5",
    texto: "Si tu portafolio cae 20% en un mes, ¿qué harías?",
    opciones: [
      { valor: 1, texto: "Vendo todo" },
      { valor: 2, texto: "Vendo una parte" },
      { valor: 3, texto: "No hago nada" },
      { valor: 4, texto: "Compro más" },
    ],
  },
  {
    bloque: "Tolerancia (30%)",
    id: "q6",
    texto: "¿Qué caída máxima en un año tolerarías sin perder el sueño?",
    opciones: [
      { valor: 1, texto: "Menos de 5%" },
      { valor: 2, texto: "5% a 15%" },
      { valor: 3, texto: "15% a 30%" },
      { valor: 4, texto: "Más de 30%" },
    ],
  },
  {
    bloque: "Tolerancia (30%)",
    id: "q7",
    texto: "¿Qué prioridad tienes entre seguridad y crecimiento?",
    opciones: [
      { valor: 1, texto: "Solo seguridad" },
      { valor: 2, texto: "Más seguridad que crecimiento" },
      { valor: 3, texto: "Más crecimiento que seguridad" },
      { valor: 4, texto: "Solo crecimiento" },
    ],
  },
  {
    bloque: "Tolerancia (30%)",
    id: "q8",
    texto: "¿Cómo reaccionas a la volatilidad diaria del mercado?",
    opciones: [
      { valor: 1, texto: "Me estresa mucho" },
      { valor: 2, texto: "Me incomoda" },
      { valor: 3, texto: "La entiendo como normal" },
      { valor: 4, texto: "No me afecta" },
    ],
  },
  {
    bloque: "Experiencia (20%)",
    id: "q9",
    texto: "¿Cuál es tu experiencia previa invirtiendo?",
    opciones: [
      { valor: 1, texto: "Ninguna" },
      { valor: 2, texto: "Solo CDT/ahorro" },
      { valor: 3, texto: "Acciones/ETFs básico" },
      { valor: 4, texto: "Acciones + derivados/cripto" },
    ],
  },
  {
    bloque: "Experiencia (20%)",
    id: "q10",
    texto: "¿Qué tanto conoces conceptos como diversificación, volatilidad y drawdown?",
    opciones: [
      { valor: 1, texto: "Nada" },
      { valor: 2, texto: "Básico" },
      { valor: 3, texto: "Intermedio" },
      { valor: 4, texto: "Avanzado" },
    ],
  },
  {
    bloque: "Experiencia (20%)",
    id: "q11",
    texto: "¿Cuántos años llevas activo en los mercados?",
    opciones: [
      { valor: 1, texto: "0" },
      { valor: 2, texto: "Menos de 1" },
      { valor: 3, texto: "1 a 5" },
      { valor: 4, texto: "Más de 5" },
    ],
  },
  {
    bloque: "Liquidez (10%)",
    id: "q12",
    texto: "¿Qué porcentaje de tu patrimonio necesitas líquido en los próximos 12 meses?",
    opciones: [
      { valor: 1, texto: "Más de 50%" },
      { valor: 2, texto: "25% a 50%" },
      { valor: 3, texto: "10% a 25%" },
      { valor: 4, texto: "Menos de 10%" },
    ],
  },
  {
    bloque: "Liquidez (10%)",
    id: "q13",
    texto: "¿Tienes otras fuentes de liquidez disponibles (línea de crédito, familia)?",
    opciones: [
      { valor: 1, texto: "Ninguna" },
      { valor: 2, texto: "Limitada" },
      { valor: 3, texto: "Moderada" },
      { valor: 4, texto: "Amplia" },
    ],
  },
  {
    bloque: "Liquidez (10%)",
    id: "q14",
    texto: "¿Con qué frecuencia podrías necesitar retirar dinero de forma imprevista?",
    opciones: [
      { valor: 1, texto: "Frecuente" },
      { valor: 2, texto: "Ocasional" },
      { valor: 3, texto: "Rara vez" },
      { valor: 4, texto: "Nunca" },
    ],
  },
];

export const DISPARADORES_SUGERIDOS = [
  "Estrés/mal día",
  "Salidas sociales",
  "Compras impulsivas online",
  "Antojos de comida a domicilio",
  "Ofertas y descuentos",
  "Aburrimiento",
];
