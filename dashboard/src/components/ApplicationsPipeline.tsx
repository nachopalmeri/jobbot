"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink, KanbanSquare, Loader2, Plus, Table2 } from "lucide-react";

import {
  formatApplicationDate,
  JobApplication,
  pipelineLabels,
  pipelineOrder,
  pipelineStyles,
  PipelineStatus,
} from "@/lib/dashboard";

interface NewApplicationPayload {
  company: string;
  job_title: string;
  url?: string;
  notes?: string;
}

interface ApplicationsPipelineProps {
  applications: JobApplication[];
  title?: string;
  subtitle?: string;
  compact?: boolean;
  allowCreate?: boolean;
  onAddApplication?: (payload: NewApplicationPayload) => Promise<void>;
  onStatusChange?: (appId: number, status: PipelineStatus) => Promise<void>;
}

const emptyForm = {
  company: "",
  job_title: "",
  url: "",
  notes: "",
};

export default function ApplicationsPipeline({
  applications,
  title = "Pipeline de postulaciones",
  subtitle = "Seguimiento estilo Notion en tabla y tablero.",
  compact = false,
  allowCreate = false,
  onAddApplication,
  onStatusChange,
}: ApplicationsPipelineProps) {
  const [view, setView] = useState<"board" | "table">("board");
  const [form, setForm] = useState(emptyForm);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");

  const grouped = useMemo(() => {
    return pipelineOrder.map((status) => ({
      status,
      label: pipelineLabels[status],
      items: applications.filter((application) => application.status === status),
    }));
  }, [applications]);

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!onAddApplication) {
      return;
    }

    try {
      setCreating(true);
      setMessage("");
      await onAddApplication(form);
      setForm(emptyForm);
      setMessage("Postulación agregada al pipeline.");
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No se pudo guardar la postulación.",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (appId: number, status: PipelineStatus) => {
    if (!onStatusChange) {
      return;
    }

    try {
      setSavingId(appId);
      setMessage("");
      await onStatusChange(appId, status);
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No se pudo actualizar el estado.",
      );
    } finally {
      setSavingId(null);
    }
  };

  return (
    <section className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-stone-950">{title}</h2>
          <p className="mt-1 text-sm text-stone-500">{subtitle}</p>
        </div>

        <div className="inline-flex rounded-full border border-stone-200 bg-stone-50 p-1">
          <button
            type="button"
            onClick={() => setView("board")}
            className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm ${
              view === "board" ? "bg-white text-stone-950 shadow-sm" : "text-stone-500"
            }`}
          >
            <KanbanSquare size={16} />
            Tablero
          </button>
          <button
            type="button"
            onClick={() => setView("table")}
            className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm ${
              view === "table" ? "bg-white text-stone-950 shadow-sm" : "text-stone-500"
            }`}
          >
            <Table2 size={16} />
            Tabla
          </button>
        </div>
      </div>

      {allowCreate ? (
        <form
          onSubmit={handleCreate}
          className="mb-6 grid gap-3 rounded-3xl border border-stone-200 bg-stone-50 p-4 md:grid-cols-2"
        >
          <input
            value={form.company}
            onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))}
            className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
            placeholder="Empresa"
            required
          />
          <input
            value={form.job_title}
            onChange={(event) => setForm((current) => ({ ...current, job_title: event.target.value }))}
            className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
            placeholder="Puesto"
            required
          />
          <input
            value={form.url}
            onChange={(event) => setForm((current) => ({ ...current, url: event.target.value }))}
            className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
            placeholder="URL de la oferta (opcional)"
          />
          <input
            value={form.notes}
            onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
            className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
            placeholder="Notas"
          />
          <div className="md:col-span-2 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={creating}
              className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {creating ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
              Agregar al pipeline
            </button>
            <span className="text-sm text-stone-500">
              Guardá manualmente postulaciones desde el dashboard o desde `/track` en Telegram.
            </span>
          </div>
        </form>
      ) : null}

      {message ? (
        <div className="mb-4 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-700">
          {message}
        </div>
      ) : null}

      {applications.length === 0 ? (
        <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center text-slate-500">
          Todavía no registraste postulaciones. Empezá desde una búsqueda o cargalas manualmente.
        </div>
      ) : view === "board" ? (
        <div className={`grid gap-4 ${compact ? "xl:grid-cols-2" : "xl:grid-cols-4"}`}>
          {grouped.map((column) => (
            <div key={column.status} className="rounded-[24px] border border-stone-200 bg-stone-50 p-4">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-stone-500">{column.label}</p>
                  <p className="text-2xl font-semibold text-stone-950">{column.items.length}</p>
                </div>
                <span
                  className={`rounded-full border px-3 py-1 text-xs font-semibold ${pipelineStyles[column.status]}`}
                >
                  {column.label}
                </span>
              </div>

              <div className="space-y-3">
                {column.items.slice(0, compact ? 3 : column.items.length).map((application) => (
                  <article
                    key={application.id}
                    className="rounded-[22px] border border-white bg-white p-4 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-base font-semibold text-stone-950">
                          {application.job_title}
                        </p>
                        <p className="truncate text-sm text-stone-500">{application.company}</p>
                      </div>
                      <span className="text-xs text-stone-400">
                        {formatApplicationDate(application.applied_at)}
                      </span>
                    </div>

                    {application.notes ? (
                      <p className="mt-3 text-sm leading-6 text-stone-600">{application.notes}</p>
                    ) : null}

                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      {onStatusChange ? (
                        <select
                          value={application.status}
                          disabled={savingId === application.id}
                          onChange={(event) =>
                            void handleStatusChange(
                              application.id,
                              event.target.value as PipelineStatus,
                            )
                          }
                          className="rounded-full border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 outline-none"
                        >
                          {pipelineOrder.map((status) => (
                            <option key={status} value={status}>
                              {pipelineLabels[status]}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <span
                          className={`rounded-full border px-3 py-2 text-xs font-semibold ${pipelineStyles[application.status]}`}
                        >
                          {pipelineLabels[application.status]}
                        </span>
                      )}

                      {application.url ? (
                        <Link
                          href={application.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 rounded-full border border-stone-200 px-3 py-2 text-xs font-medium text-stone-700 hover:border-stone-300 hover:text-stone-950"
                        >
                          Ver aviso
                          <ExternalLink size={14} />
                        </Link>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="overflow-hidden rounded-[24px] border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-stone-50 text-stone-500">
              <tr>
                <th className="px-4 py-3 font-medium">Empresa</th>
                <th className="px-4 py-3 font-medium">Puesto</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Notas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {applications.map((application) => (
                <tr key={application.id}>
                  <td className="px-4 py-3 font-medium text-stone-950">{application.company}</td>
                  <td className="px-4 py-3 text-stone-600">
                    <div className="flex items-center gap-2">
                      <span>{application.job_title}</span>
                      {application.url ? (
                        <Link
                          href={application.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-stone-400 hover:text-stone-700"
                        >
                          <ExternalLink size={14} />
                        </Link>
                      ) : null}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {onStatusChange ? (
                      <select
                        value={application.status}
                        disabled={savingId === application.id}
                        onChange={(event) =>
                          void handleStatusChange(
                            application.id,
                            event.target.value as PipelineStatus,
                          )
                        }
                        className="rounded-full border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 outline-none"
                      >
                        {pipelineOrder.map((status) => (
                          <option key={status} value={status}>
                            {pipelineLabels[status]}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span
                        className={`rounded-full border px-3 py-2 text-xs font-semibold ${pipelineStyles[application.status]}`}
                      >
                        {pipelineLabels[application.status]}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-stone-500">
                    {formatApplicationDate(application.applied_at)}
                  </td>
                  <td className="px-4 py-3 text-stone-500">{application.notes || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
