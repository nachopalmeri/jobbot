"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { LayoutGrid, Plus, Rows3, Search } from "lucide-react";

import { ApplicationsKanban } from "@/components/ApplicationsKanban";
import {
  APPLICATION_FLOW,
  ApplicationRecord,
  formatApplicationDate,
  getApplicationStatusMeta,
  normalizeApplicationStatus,
} from "@/lib/applications";
import { apiRequest } from "@/lib/api";

type ViewMode = "table" | "board";

const statusOptions = [
  { value: "", label: "Todos los estados" },
  ...APPLICATION_FLOW.map((status) => ({
    value: status,
    label: getApplicationStatusMeta(status).label,
  })),
];

export default function PostulacionesPage() {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<ViewMode>("table");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | string | null>(null);
  const [form, setForm] = useState({
    job_title: "",
    company: "",
    url: "",
    notes: "",
  });

  const loadApplications = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<{ applications: ApplicationRecord[] }>(
        "/jobs/applications",
        {},
        true,
      );
      setApplications(data.applications || []);
      setError("");
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudieron cargar tus postulaciones.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadApplications();
  }, []);

  const filteredApplications = useMemo(() => {
    return applications.filter((application) => {
      const matchesStatus =
        !statusFilter || normalizeApplicationStatus(application.status) === statusFilter;
      const haystack = `${application.job_title} ${application.company}`.toLowerCase();
      const matchesSearch = haystack.includes(search.toLowerCase().trim());
      return matchesStatus && matchesSearch;
    });
  }, [applications, search, statusFilter]);

  const handleStatusChange = async (appId: number | string, status: string) => {
    const normalized = normalizeApplicationStatus(status);
    try {
      setUpdatingId(appId);
      await apiRequest(
        `/jobs/applications/${appId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ status: normalized }),
        },
        true,
      );

      setApplications((current) =>
        current.map((application) =>
          String(application.id) === String(appId)
            ? { ...application, status: normalized }
            : application,
        ),
      );
      setError("");
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo actualizar el estado.";
      setError(detail);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCreateApplication = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      setSubmitting(true);
      const created = await apiRequest<ApplicationRecord>(
        "/jobs/track",
        {
          method: "POST",
          body: JSON.stringify(form),
        },
        true,
      );

      setApplications((current) => [created, ...current]);
      setForm({
        job_title: "",
        company: "",
        url: "",
        notes: "",
      });
      setIsModalOpen(false);
      setError("");
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo crear la postulacion.";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#fafaf9,_#f5f5f4_35%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Seguimiento
              </p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
                Pipeline de postulaciones
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
                Controla tu embudo como una mezcla entre tabla operativa y board tipo Notion.
                Carga aplicaciones, mueve estados y revisa el historial desde un solo lugar.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white hover:bg-slate-800"
            >
              <Plus size={18} />
              Nueva postulacion
            </button>
          </div>

          {error ? (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}

          <div className="mt-6 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-1 flex-col gap-3 md:flex-row">
              <label className="relative flex-1">
                <Search size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por puesto o empresa..."
                  className="w-full rounded-2xl border border-stone-200 bg-white py-3 pl-11 pr-4 text-stone-950 outline-none focus:border-indigo-400"
                />
              </label>

              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="inline-flex rounded-2xl border border-stone-200 bg-stone-50 p-1">
              <button
                type="button"
                onClick={() => setView("table")}
                className={`inline-flex items-center gap-2 rounded-[1rem] px-4 py-2 text-sm font-medium transition-colors ${
                  view === "table" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500"
                }`}
              >
                <Rows3 size={16} />
                Tabla
              </button>
              <button
                type="button"
                onClick={() => setView("board")}
                className={`inline-flex items-center gap-2 rounded-[1rem] px-4 py-2 text-sm font-medium transition-colors ${
                  view === "board" ? "bg-white text-slate-950 shadow-sm" : "text-slate-500"
                }`}
              >
                <LayoutGrid size={16} />
                Board
              </button>
            </div>
          </div>
        </section>

        {loading ? (
          <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-10 text-center text-slate-500 shadow-sm">
            Cargando tu pipeline...
          </div>
        ) : view === "board" ? (
          <ApplicationsKanban applications={filteredApplications} />
        ) : (
          <section className="overflow-hidden rounded-[2rem] border border-stone-200 bg-white/90 shadow-sm">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-slate-500">
                  <tr>
                    <th className="px-5 py-4 font-medium">Puesto</th>
                    <th className="px-5 py-4 font-medium">Empresa</th>
                    <th className="px-5 py-4 font-medium">Fecha</th>
                    <th className="px-5 py-4 font-medium">Estado</th>
                    <th className="px-5 py-4 font-medium">Oferta</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredApplications.map((application) => {
                    const meta = getApplicationStatusMeta(application.status);

                    return (
                      <tr key={application.id} className="align-top">
                        <td className="px-5 py-4">
                          <div className="font-medium text-slate-950">
                            {application.job_title}
                          </div>
                          {application.notes ? (
                            <p className="mt-1 max-w-md text-xs leading-5 text-slate-500">
                              {application.notes}
                            </p>
                          ) : null}
                        </td>
                        <td className="px-5 py-4 text-slate-700">{application.company}</td>
                        <td className="px-5 py-4 text-slate-500">
                          {formatApplicationDate(application.applied_at)}
                        </td>
                        <td className="px-5 py-4">
                          <select
                            value={normalizeApplicationStatus(application.status)}
                            onChange={(event) =>
                              void handleStatusChange(application.id, event.target.value)
                            }
                            disabled={updatingId === application.id}
                            className="rounded-full border border-stone-300 bg-white px-3 py-2 text-xs font-semibold text-stone-900 outline-none focus:border-indigo-400"
                          >
                            {APPLICATION_FLOW.map((status) => (
                              <option key={status} value={status}>
                                {getApplicationStatusMeta(status).label}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-5 py-4">
                          {application.url ? (
                            <a
                              href={application.url}
                              target="_blank"
                              rel="noreferrer"
                              className="font-medium text-slate-700 hover:text-slate-950"
                            >
                              Abrir
                            </a>
                          ) : (
                            <span className="text-slate-400">Sin URL</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {filteredApplications.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-12 text-center">
                        <p className="text-slate-500">
                          No hay postulaciones para este filtro todavia.
                        </p>
                        <button
                          type="button"
                          onClick={() => setIsModalOpen(true)}
                          className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 font-medium text-slate-700 hover:border-slate-300 hover:text-slate-950"
                        >
                          <Plus size={16} />
                          Cargar primera postulacion
                        </button>
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-950">
                Convierte este pipeline en entrevistas reales
              </p>
              <p className="mt-1 text-sm text-slate-500">
                Usa CV Suite para adaptar tu perfil a cada vacante antes de aplicar.
              </p>
            </div>
            <Link
              href="/dashboard/cv"
              className="inline-flex items-center gap-2 rounded-2xl bg-violet-600 px-4 py-2.5 font-medium text-white hover:bg-violet-700"
            >
              Abrir CV Suite
            </Link>
          </div>
        </section>

        {isModalOpen ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm">
            <div className="w-full max-w-xl rounded-[2rem] border border-stone-200 bg-white p-6 shadow-xl">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                    Nueva postulacion
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                    Carga una oportunidad a tu pipeline
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    Guardá la vacante con datos mínimos y movela después entre aplicado,
                    entrevista, oferta o descartado.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-full border border-stone-200 px-3 py-1.5 text-sm text-stone-600 hover:border-stone-300 hover:text-stone-900"
                >
                  Cerrar
                </button>
              </div>

              <form onSubmit={handleCreateApplication} className="mt-6 space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-900">Puesto</span>
                  <input
                    required
                    value={form.job_title}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, job_title: event.target.value }))
                    }
                    className="w-full rounded-2xl border border-stone-200 px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
                    placeholder="Backend Developer"
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-900">Empresa</span>
                  <input
                    required
                    value={form.company}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, company: event.target.value }))
                    }
                    className="w-full rounded-2xl border border-stone-200 px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
                    placeholder="Mercado Libre"
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-900">URL</span>
                  <input
                    value={form.url}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, url: event.target.value }))
                    }
                    className="w-full rounded-2xl border border-stone-200 px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
                    placeholder="https://..."
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-900">Notas</span>
                  <textarea
                    value={form.notes}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, notes: event.target.value }))
                    }
                    rows={4}
                    className="w-full rounded-2xl border border-stone-200 px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
                    placeholder="Recruiter, salary range, proximo paso..."
                  />
                </label>

                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white hover:bg-slate-800 disabled:opacity-60"
                  >
                    <Plus size={18} />
                    {submitting ? "Guardando..." : "Guardar en pipeline"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="rounded-2xl border border-slate-200 px-5 py-3 font-medium text-slate-700 hover:border-slate-300 hover:text-slate-950"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
