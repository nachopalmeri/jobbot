"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Bell,
  Briefcase,
  Crown,
  Search,
  Sparkles,
  Target,
} from "lucide-react";

import ApplicationsPipeline from "@/components/ApplicationsPipeline";
import ProductivityPanel from "@/components/ProductivityPanel";
import { apiRequest } from "@/lib/api";
import { JobApplication } from "@/lib/dashboard";

interface DashboardPayload {
  plan: string;
  weekly_goal: number;
  weekly_applied: number;
  digest_mode: string;
  active_alerts: boolean;
  funnel?: {
    applied?: number;
    interview?: number;
    offer?: number;
    rejected?: number;
  };
  applications: JobApplication[];
}

interface UsagePayload {
  remaining_searches: number;
  searches_limit: number;
  searches_used: number;
  remaining_interviews: number;
  interviews_limit: number;
}

interface JobRecommendation {
  id: string;
  title: string;
  company: string;
  location: string;
  modality: string;
  match_score: number;
  source: string;
  url?: string;
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [usage, setUsage] = useState<UsagePayload | null>(null);
  const [recommendedJobs, setRecommendedJobs] = useState<JobRecommendation[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [dashboardData, usageData, jobsData] = await Promise.all([
          apiRequest<DashboardPayload>("/users/dashboard", {}, true),
          apiRequest<UsagePayload>("/users/usage", {}, true),
          apiRequest<{ jobs: JobRecommendation[] }>("/jobs/recommended", {}, true),
        ]);

        setDashboard(dashboardData);
        setUsage(usageData);
        setRecommendedJobs(jobsData.jobs ?? []);
      } catch (err) {
        const detail =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo cargar el dashboard.";
        setError(detail);
      }
    };

    void load();
  }, []);

  const stats = useMemo(
    () => [
      {
        label: "Pipeline activo",
        value: dashboard?.applications?.length ?? 0,
        detail: `${dashboard?.funnel?.interview ?? 0} entrevistas abiertas`,
      },
      {
        label: "Busquedas disponibles",
        value:
          usage?.searches_limit === 0
            ? "Ilimitadas"
            : String(usage?.remaining_searches ?? 0),
        detail:
          usage?.searches_limit === 0
            ? "Tu plan ya no tiene tope diario"
            : `${usage?.searches_used ?? 0} usadas hoy`,
      },
      {
        label: "Alertas",
        value: dashboard?.active_alerts ? "Encendidas" : "Pausadas",
        detail: `Modo ${dashboard?.digest_mode ?? "realtime"}`,
      },
      {
        label: "Entrevistas IA",
        value:
          usage?.interviews_limit === 0
            ? "No incluidas"
            : `${usage?.remaining_interviews ?? 0}`,
        detail:
          usage?.interviews_limit === 0
            ? "Disponibles desde Premium"
            : `${usage?.interviews_limit ?? 0} incluidas este mes`,
      },
    ],
    [dashboard, usage],
  );

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.08),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(217,119,6,0.08),_transparent_28%),linear-gradient(180deg,_#fafaf9,_#f5f5f4_42%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-10">
        <section className="overflow-hidden rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-600">
                Dashboard Operativo
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
                Tu búsqueda laboral merece un tablero que empuje, no que drene energía.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600 lg:text-lg">
                Seguí tu pipeline, sostené tu objetivo semanal, enfocá bloques de trabajo
                con pomodoro y dejá a mano la suite de CV para aplicar con más precisión.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/dashboard/buscar"
                  className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white hover:bg-slate-800"
                >
                  Buscar empleos
                  <ArrowRight size={18} />
                </Link>
                <Link
                  href="/dashboard/cv"
                  className="inline-flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-5 py-3 font-medium text-stone-700 hover:border-indigo-200 hover:text-indigo-700"
                >
                  CV Intelligence
                  <Sparkles size={18} />
                </Link>
              </div>
            </div>

            <div className="rounded-[1.75rem] border border-indigo-200 bg-[linear-gradient(135deg,_rgba(79,70,229,0.08),_rgba(245,158,11,0.08))] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-700">
                Momentum del día
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="rounded-2xl border border-white/70 bg-white/80 p-4">
                  <p className="text-sm font-medium text-stone-500">Meta</p>
                  <p className="mt-2 text-lg font-semibold text-stone-950">
                    1 búsqueda buena + 1 postulación cuidada
                  </p>
                </div>
                <div className="rounded-2xl border border-white/70 bg-white/80 p-4">
                  <p className="text-sm font-medium text-stone-500">Mindset</p>
                  <p className="mt-2 text-lg font-semibold text-stone-950">
                    Consistencia mata ansiedad.
                  </p>
                </div>
                <div className="rounded-2xl border border-white/70 bg-white/80 p-4">
                  <p className="text-sm font-medium text-stone-500">Palanca</p>
                  <p className="mt-2 text-lg font-semibold text-stone-950">
                    CV Suite + pipeline = mejores decisiones.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {error ? (
            <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="grid gap-4 sm:grid-cols-2">
            {stats.map((stat) => (
              <article key={stat.label} className="rounded-3xl border border-stone-200 bg-white/90 p-5 shadow-sm">
                <p className="text-sm font-medium text-stone-500">{stat.label}</p>
                <div className="mt-3 text-3xl font-semibold tracking-tight text-stone-950">
                  {stat.value}
                </div>
                <p className="mt-2 text-sm leading-6 text-stone-600">{stat.detail}</p>
              </article>
            ))}
          </div>

          <ProductivityPanel
            weeklyApplied={dashboard?.weekly_applied ?? 0}
            weeklyGoal={dashboard?.weekly_goal ?? 0}
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                  Pipeline
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                  Vista tipo Notion para tus postulaciones
                </h2>
              </div>
              <Link
                href="/dashboard/postulaciones"
                className="inline-flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 hover:border-stone-300 hover:text-stone-950"
              >
                Abrir pipeline
                <ArrowRight size={16} />
              </Link>
            </div>

            <ApplicationsPipeline
              applications={dashboard?.applications ?? []}
              compact
              subtitle="Segui tu pipeline en tablero o tabla sin salir del dashboard."
            />
          </div>

          <div className="space-y-4">
            <article className="rounded-3xl border border-stone-200 bg-white/90 p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-indigo-100 p-3 text-indigo-700">
                  <Sparkles size={20} />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
                    CV Analysis
                  </p>
                  <h3 className="mt-1 text-xl font-semibold text-stone-950">
                    Resume Score + ATS + Job Match
                  </h3>
                </div>
              </div>
              <p className="mt-4 text-sm leading-6 text-stone-600">
                Tu suite de CV ya vive dentro del dashboard: score ATS, keywords faltantes,
                feedback IA, cover letters y mock interviews desde un mismo flujo.
              </p>
              <Link
                href="/dashboard/cv"
                className="mt-5 inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2.5 font-medium text-white hover:bg-indigo-700"
              >
                Ir a CV Suite
                <ArrowRight size={16} />
              </Link>
            </article>

            <article className="rounded-3xl border border-stone-200 bg-white/90 p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-amber-100 p-3 text-amber-700">
                  <Crown size={20} />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-600">
                    Plan Actual
                  </p>
                  <h3 className="mt-1 text-xl font-semibold text-stone-950">
                    {(dashboard?.plan || "free").toUpperCase()}
                  </h3>
                </div>
              </div>
              <p className="mt-4 text-sm leading-6 text-stone-600">
                Si queres destrabar mock interviews, cover letters y CV Intelligence full,
                tene todo centralizado desde la suscripcion.
              </p>
              <Link
                href="/dashboard/suscripcion"
                className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-2.5 font-medium text-amber-800 hover:bg-amber-100"
              >
                Ver planes premium
                <ArrowRight size={16} />
              </Link>
            </article>
          </div>
        </section>

        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                Recomendadas
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                Oportunidades para atacar hoy
              </h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/dashboard/buscar"
                className="inline-flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 hover:border-stone-300 hover:text-stone-950"
              >
                <Search size={16} />
                Abrir buscador
              </Link>
              <Link
                href="/dashboard/configuracion"
                className="inline-flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 hover:border-stone-300 hover:text-stone-950"
              >
                <Bell size={16} />
                Ajustar alertas
              </Link>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            {recommendedJobs.slice(0, 3).map((job) => (
              <a
                key={job.id}
                href={job.url || "#"}
                target="_blank"
                rel="noreferrer"
                className="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm transition-transform hover:-translate-y-0.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                    Match {job.match_score}%
                  </span>
                    <span className="text-xs uppercase tracking-[0.18em] text-stone-400">
                      {job.source}
                    </span>
                  </div>
                <h3 className="mt-4 text-lg font-semibold text-stone-950">{job.title}</h3>
                <p className="mt-2 text-sm text-stone-600">{job.company}</p>
                <p className="mt-1 text-sm text-stone-500">
                  {job.location} · {job.modality}
                </p>
              </a>
            ))}

            {recommendedJobs.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-stone-300 bg-stone-50 px-6 py-10 text-center text-sm leading-6 text-stone-500 lg:col-span-3">
                Completa tu configuracion y ejecuta una primera busqueda para poblar las recomendaciones.
              </div>
            ) : null}
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Link
              href="/dashboard/postulaciones"
              className="flex items-center gap-3 rounded-3xl border border-stone-200 bg-stone-50 px-5 py-4 text-stone-700 hover:bg-stone-100"
            >
              <div className="rounded-2xl bg-stone-950 p-3 text-white">
                <Briefcase size={20} />
              </div>
              <div>
                <p className="font-semibold text-stone-950">Tabla y tablero de seguimiento</p>
                <p className="text-sm text-stone-500">
                  Cambia estados, agrega notas y ordena tu pipeline.
                </p>
              </div>
            </Link>

            <Link
              href="/dashboard/cv"
              className="flex items-center gap-3 rounded-3xl border border-indigo-200 bg-indigo-50 px-5 py-4 text-indigo-800 hover:bg-indigo-100"
            >
              <div className="rounded-2xl bg-indigo-600 p-3 text-white">
                <Target size={20} />
              </div>
              <div>
                <p className="font-semibold text-stone-950">CV analysis estilo RankMyCV</p>
                <p className="text-sm text-stone-600">
                  Score, ATS, Job Match y feedback para cada vacante.
                </p>
              </div>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
