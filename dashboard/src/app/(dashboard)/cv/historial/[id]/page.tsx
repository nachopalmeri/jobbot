"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CalendarDays, Cpu, FileText } from "lucide-react";

import { apiRequest } from "@/lib/api";

interface AnalysisDetail {
  id: number;
  type: string;
  has_job_match: boolean;
  prompt_tokens: number;
  response_tokens: number;
  total_tokens: number;
  created_at: string;
}

export default function CVHistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiRequest<AnalysisDetail>(`/cv/history/${params.id}`, {}, true);
        setDetail(data);
      } catch (err) {
        const message =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo cargar el detalle.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [params.id]);

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#f8fafc,_#f5f3ff_30%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
          <Link
            href="/dashboard/cv/historial"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft size={16} />
            Volver al historial
          </Link>

          <div className="mt-5 flex items-center gap-3">
            <div className="rounded-2xl bg-violet-100 p-3 text-violet-700">
              <FileText size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-600">
                Analisis guardado
              </p>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                Detalle del scan #{params.id}
              </h1>
            </div>
          </div>
        </section>

        {loading ? (
          <div className="rounded-[2rem] border border-slate-200 bg-white/90 p-8 text-center text-slate-500 shadow-sm">
            Cargando detalle...
          </div>
        ) : error ? (
          <div className="rounded-[2rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 shadow-sm">
            {error}
          </div>
        ) : detail ? (
          <section className="grid gap-4 md:grid-cols-3">
            <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Fecha
              </p>
              <div className="mt-3 flex items-center gap-2 text-slate-950">
                <CalendarDays size={18} />
                <span className="font-medium">
                  {new Date(detail.created_at).toLocaleDateString("es-AR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </span>
              </div>
            </article>

            <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Match
              </p>
              <p className="mt-3 text-lg font-medium text-slate-950">
                {detail.has_job_match ? "Con job match" : "Scan general"}
              </p>
            </article>

            <article className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Tokens
              </p>
              <div className="mt-3 flex items-center gap-2 text-slate-950">
                <Cpu size={18} />
                <span className="font-medium">{detail.total_tokens || 0}</span>
              </div>
              <p className="mt-2 text-sm text-slate-500">
                Prompt: {detail.prompt_tokens || 0} · Respuesta: {detail.response_tokens || 0}
              </p>
            </article>
          </section>
        ) : null}
      </div>
    </div>
  );
}
