export type ApplicationStatus = "aplicado" | "entrevista" | "oferta" | "rechazado";

export interface ApplicationRecord {
  id: number | string;
  job_title: string;
  company: string;
  status?: string | null;
  applied_at?: string | null;
  url?: string | null;
  notes?: string | null;
}

export const APPLICATION_FLOW: ApplicationStatus[] = [
  "aplicado",
  "entrevista",
  "oferta",
  "rechazado",
];

export const APPLICATION_STATUS_META: Record<
  ApplicationStatus,
  {
    label: string;
    chip: string;
    column: string;
    dot: string;
  }
> = {
  aplicado: {
    label: "Aplicado",
    chip: "bg-sky-100 text-sky-700",
    column: "border-sky-200 bg-sky-50/70",
    dot: "bg-sky-500",
  },
  entrevista: {
    label: "Entrevista",
    chip: "bg-amber-100 text-amber-800",
    column: "border-amber-200 bg-amber-50/70",
    dot: "bg-amber-500",
  },
  oferta: {
    label: "Oferta",
    chip: "bg-emerald-100 text-emerald-700",
    column: "border-emerald-200 bg-emerald-50/70",
    dot: "bg-emerald-500",
  },
  rechazado: {
    label: "Rechazado",
    chip: "bg-rose-100 text-rose-700",
    column: "border-rose-200 bg-rose-50/70",
    dot: "bg-rose-500",
  },
};

export function normalizeApplicationStatus(status?: string | null): ApplicationStatus {
  if (!status) {
    return "aplicado";
  }

  return APPLICATION_FLOW.includes(status as ApplicationStatus)
    ? (status as ApplicationStatus)
    : "aplicado";
}

export function getApplicationStatusMeta(status?: string | null) {
  return APPLICATION_STATUS_META[normalizeApplicationStatus(status)];
}

export function groupApplications(applications: ApplicationRecord[]) {
  return APPLICATION_FLOW.map((status) => ({
    status,
    meta: APPLICATION_STATUS_META[status],
    items: applications.filter(
      (application) => normalizeApplicationStatus(application.status) === status,
    ),
  }));
}

export function formatApplicationDate(value?: string | null) {
  if (!value) {
    return "Sin fecha";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Sin fecha";
  }

  return parsed.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "short",
  });
}
