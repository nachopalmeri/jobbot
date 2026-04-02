import Link from "next/link";
import { ArrowRight, Briefcase } from "lucide-react";

import {
  ApplicationRecord,
  formatApplicationDate,
  getApplicationStatusMeta,
  groupApplications,
} from "@/lib/applications";

interface ApplicationsKanbanProps {
  applications: ApplicationRecord[];
  maxPerColumn?: number;
  compact?: boolean;
  showEmptyMessage?: boolean;
}

export function ApplicationsKanban({
  applications,
  maxPerColumn,
  compact = false,
  showEmptyMessage = true,
}: ApplicationsKanbanProps) {
  const columns = groupApplications(applications);
  const hasApplications = applications.length > 0;

  if (!hasApplications && showEmptyMessage) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/80 p-10 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
          <Briefcase size={24} />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-slate-900">Tu pipeline todavia esta vacio</h3>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          Agrega tus primeras postulaciones para empezar a medir avance, follow-ups y conversion.
        </p>
        <Link
          href="/dashboard/postulaciones"
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 font-medium text-white hover:bg-slate-800"
        >
          Cargar pipeline
          <ArrowRight size={18} />
        </Link>
      </div>
    );
  }

  return (
    <div className={`grid gap-4 ${compact ? "xl:grid-cols-4" : "xl:grid-cols-4"}`}>
      {columns.map((column) => (
        <section
          key={column.status}
          className={`rounded-3xl border p-4 shadow-sm ${column.meta.column}`}
        >
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${column.meta.dot}`} />
              <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-700">
                {column.meta.label}
              </h3>
            </div>
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${column.meta.chip}`}>
              {column.items.length}
            </span>
          </div>

          <div className="space-y-3">
            {(maxPerColumn ? column.items.slice(0, maxPerColumn) : column.items).map((application) => {
              const meta = getApplicationStatusMeta(application.status);
              return (
                <article
                  key={application.id}
                  className="rounded-2xl border border-white/80 bg-white/90 p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900">
                        {application.job_title}
                      </h4>
                      <p className="mt-1 text-sm text-slate-600">{application.company}</p>
                    </div>
                    <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${meta.chip}`}>
                      {meta.label}
                    </span>
                  </div>

                  <div className="mt-4 flex items-center justify-between gap-3 text-xs text-slate-500">
                    <span>{formatApplicationDate(application.applied_at)}</span>
                    {application.url ? (
                      <a
                        href={application.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-slate-700 hover:text-slate-950"
                      >
                        Ver oferta
                      </a>
                    ) : null}
                  </div>
                </article>
              );
            })}

            {column.items.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/80 bg-white/60 px-4 py-6 text-center text-sm text-slate-500">
                Sin movimientos todavia.
              </div>
            ) : null}
          </div>
        </section>
      ))}
    </div>
  );
}
