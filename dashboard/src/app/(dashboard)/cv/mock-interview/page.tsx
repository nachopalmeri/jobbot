"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BrainCircuit, Sparkles } from "lucide-react";

import { apiRequest } from "@/lib/api";

export default function MockInterviewPage() {
  const [jobTitle, setJobTitle] = useState("");
  const [questions, setQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    apiRequest<{ remaining_interviews: number; interviews_limit: number }>(
      "/users/usage",
      {},
      true,
    )
      .then((data) => {
        setRemaining(data.interviews_limit === 0 ? null : data.remaining_interviews);
      })
      .catch(() => {
        setRemaining(null);
      });
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest<{ questions: string[] }>(
        `/cv/mock-interview?job_title=${encodeURIComponent(jobTitle)}`,
        { method: "POST" },
        true,
      );
      setQuestions(data.questions || []);
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo generar la simulacion.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#f8fafc,_#ecfeff_34%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
          <Link
            href="/dashboard/cv"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft size={16} />
            Volver a CV Suite
          </Link>

          <div className="mt-5 flex items-center gap-3">
            <div className="rounded-2xl bg-cyan-100 p-3 text-cyan-700">
              <BrainCircuit size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-600">
                Premium Tool
              </p>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                Mock Interview
              </h1>
            </div>
          </div>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
            Genera preguntas realistas para practicar antes de una entrevista. Úsalo como bridge
            entre el pipeline y la preparación concreta.
          </p>

          {remaining !== null ? (
            <div className="mt-5 rounded-2xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm text-cyan-800">
              Te quedan {remaining} mock interviews disponibles este periodo.
            </div>
          ) : null}

          {error ? (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}
        </section>

        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm"
          >
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Puesto objetivo</span>
              <input
                required
                value={jobTitle}
                onChange={(event) => setJobTitle(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
                placeholder="Backend Engineer"
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-2xl bg-cyan-600 px-5 py-3 font-medium text-white hover:bg-cyan-700 disabled:opacity-60"
            >
              <Sparkles size={18} />
              {loading ? "Generando..." : "Preparar simulacion"}
            </button>
          </form>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              Preguntas sugeridas
            </p>
            <div className="mt-5 space-y-3">
              {questions.map((question, index) => (
                <article
                  key={`${index}-${question}`}
                  className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4"
                >
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-600">
                    Pregunta {index + 1}
                  </div>
                  <p className="mt-2 text-sm leading-7 text-slate-700">{question}</p>
                </article>
              ))}

              {questions.length === 0 ? (
                <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 p-6 text-sm leading-7 text-slate-500">
                  Carga un puesto para generar una mini bateria de preguntas y practicar dentro del
                  mismo dashboard.
                </div>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
