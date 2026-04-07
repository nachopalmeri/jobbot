"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Bell, Search, Sparkles, Target, Upload } from "lucide-react";

import ApplicationsPipeline from "@/components/ApplicationsPipeline";
import { apiRequest } from "@/lib/api";
import { buildGoalMessage, getDailyQuote, JobApplication } from "@/lib/dashboard";

interface DashboardPayload {
  plan: string;
  weekly_goal: number;
  weekly_applied: number;
  digest_mode: string;
  active_alerts: boolean;
  application_streak?: number;
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

  const weeklyGoal = dashboard?.weekly_goal ?? 0;
  const weeklyApplied = dashboard?.weekly_applied ?? 0;
  const weeklyRemaining = Math.max(weeklyGoal - weeklyApplied, 0);
  const streak = dashboard?.application_streak ?? weeklyApplied;
  const motivation = useMemo(() => getDailyQuote(), []);
  const searchesLabel =
    usage?.searches_limit === 0 ? "Ilimitadas" : String(usage?.remaining_searches ?? 0);

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.08),_transparent_30%),linear-gradient(180deg,_#fafaf9,_#f5f5f4_38%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="rounded-[2rem] border border-stone-200 bg-white/92 p-6 shadow-sm lg:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-600">
                Inicio
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
                Tu busqueda, clara y en movimiento.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600">
                Mira tu objetivo semanal, elige una accion y avanza. El dashboard ya no te vende
                nada: te ayuda a moverte.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/dashboard/buscar"
                className="inline-flex items-center gap-2 rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-white hover:bg-stone-800"
              >
                <Search size={16} />
                Buscar
              </Link>
              <Link
                href="/dashboard/cv"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-800 hover:border-stone-400"
              >
                <Upload size={16} />
                Subir CV
              </Link>
              <Link
                href="/dashboard/postulaciones"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-800 hover:border-stone-400"
              >
                <ArrowRight size={16} />
                Ver postulaciones
              </Link>
            </div>
          </div>

          {error ? (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-[1.7rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-stone-950">
              <Target size={16} className="text-indigo-600" />
              Meta semanal
            </div>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-stone-950">
              {weeklyApplied} / {weeklyGoal}
            </p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              {weeklyGoal > 0
                ? `${weeklyRemaining} restantes para cumplir el objetivo.`
                : "Define una meta para ordenar tu ritmo."}
            </p>
          </article>

          <article className="rounded-[1.7rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-stone-950">
              <Sparkles size={16} className="text-indigo-600" />
              Racha
            </div>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-stone-950">{streak}</p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              {buildGoalMessage(weeklyApplied, weeklyGoal)}
            </p>
          </article>

          <article className="rounded-[1.7rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-stone-950">
              <Bell size={16} className="text-amber-600" />
              Alertas
            </div>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-stone-950">
              {dashboard?.active_alerts ? "On" : "Off"}
            </p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Modo {dashboard?.digest_mode ?? "realtime"}.
            </p>
          </article>

          <article className="rounded-[1.7rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-stone-950">
              <Search size={16} className="text-indigo-600" />
              Busquedas
            </div>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-stone-950">
              {searchesLabel}
            </p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              {usage?.searches_limit === 0
                ? "Tu plan no tiene limite diario."
                : `${usage?.searches_used ?? 0} usadas hoy.`}
            </p>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                  Recomendadas
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                  Vacantes para mover hoy
                </h2>
              </div>
              <Link
                href="/dashboard/buscar"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 hover:border-stone-400 hover:text-stone-950"
              >
                Abrir buscador
                <ArrowRight size={16} />
              </Link>
            </div>

            <div className="mt-6 space-y-3">
              {recommendedJobs.slice(0, 3).map((job) => (
                <a
                  key={job.id}
                  href={job.url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-start justify-between gap-4 rounded-3xl border border-stone-200 bg-white p-5 shadow-sm transition-transform hover:-translate-y-0.5"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-stone-950">{job.title}</h3>
                    <p className="mt-1 text-sm text-stone-600">{job.company}</p>
                    <p className="mt-1 text-sm text-stone-500">
                      {job.location} · {job.modality}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                      {job.match_score}%
                    </span>
                    <p className="mt-3 text-xs uppercase tracking-[0.18em] text-stone-400">
                      {job.source}
                    </p>
                  </div>
                </a>
              ))}

              {recommendedJobs.length === 0 ? (
                <div className="rounded-3xl border border-dashed border-stone-300 bg-stone-50 px-6 py-10 text-center text-sm leading-6 text-stone-500">
                  Corre tu primera busqueda para poblar este bloque con vacantes reales.
                </div>
              ) : null}
            </div>
          </section>

          <div className="space-y-4">
            <article className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
                Motivacion diaria
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                Mantene el ritmo sin saturarte
              </h2>
              <p className="mt-4 text-base leading-7 text-stone-700">{motivation}</p>
            </article>

            <article className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-600">
                Tu plan
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                {(dashboard?.plan || "free").toUpperCase()}
              </h2>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                Algunas funciones avanzadas viven en Pro y Premium. El producto base sigue
                funcionando simple desde Free.
              </p>
              <Link
                href="/dashboard/suscripcion"
                className="mt-5 inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-medium text-amber-800 hover:bg-amber-100"
              >
                Ver planes
                <ArrowRight size={16} />
              </Link>
            </article>
          </div>
        </section>

        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                Pipeline
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                Tus postulaciones, sin ruido
              </h2>
            </div>
            <Link
              href="/dashboard/postulaciones"
              className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 hover:border-stone-400 hover:text-stone-950"
            >
              Ver completo
              <ArrowRight size={16} />
            </Link>
          </div>

          <ApplicationsPipeline
            applications={dashboard?.applications?.slice(0, 5) ?? []}
            compact
            subtitle="Vista resumida. El tablero completo vive en Postulaciones."
          />
        </section>
      </div>
    </div>
  );
}
