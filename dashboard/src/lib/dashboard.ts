export type PipelineStatus = "aplicado" | "entrevista" | "rechazado" | "oferta";

export interface JobApplication {
  id: number;
  job_title: string;
  company: string;
  url?: string;
  notes?: string;
  status: PipelineStatus;
  applied_at?: string;
}

export const pipelineOrder: PipelineStatus[] = [
  "aplicado",
  "entrevista",
  "oferta",
  "rechazado",
];

export const pipelineLabels: Record<PipelineStatus, string> = {
  aplicado: "Aplicado",
  entrevista: "Entrevista",
  oferta: "Oferta",
  rechazado: "Descartado",
};

export const pipelineStyles: Record<PipelineStatus, string> = {
  aplicado: "border-sky-200 bg-sky-50 text-sky-700",
  entrevista: "border-amber-200 bg-amber-50 text-amber-700",
  oferta: "border-emerald-200 bg-emerald-50 text-emerald-700",
  rechazado: "border-rose-200 bg-rose-50 text-rose-700",
};

export const motivationalQuotes = [
  "Cada postulacion bien hecha acumula ventaja, aunque hoy no se note.",
  "No buscas mas volumen: buscas mejores oportunidades con mejor timing.",
  "Tu CV mejora mas rapido cuando aplicas con criterio que cuando aplicas al azar.",
  "La constancia gana cuando el mercado parece lento.",
  "Una semana ordenada de busqueda vale mas que diez impulsos desordenados.",
  "Aplicar mejor tambien es una skill. El dashboard existe para entrenarla.",
];

export function getDailyQuote(date = new Date()) {
  const daySeed = Number(
    `${date.getUTCFullYear()}${date.getUTCMonth() + 1}${date.getUTCDate()}`,
  );

  return motivationalQuotes[daySeed % motivationalQuotes.length];
}

export function formatApplicationDate(value?: string) {
  if (!value) {
    return "Sin fecha";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "short",
  });
}

export function buildGoalMessage(weeklyApplied: number, weeklyGoal: number) {
  if (weeklyGoal <= 0) {
    return "Defini una meta semanal para darle ritmo a tu pipeline.";
  }

  if (weeklyApplied >= weeklyGoal) {
    return "Meta cumplida. Es un buen momento para enfocarte en calidad y follow-ups.";
  }

  const remaining = weeklyGoal - weeklyApplied;
  return `Te faltan ${remaining} postulaciones para cumplir tu objetivo de esta semana.`;
}
