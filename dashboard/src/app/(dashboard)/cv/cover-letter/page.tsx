"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Copy, FileText, Sparkles } from "lucide-react";

import { apiRequest } from "@/lib/api";

export default function CoverLetterPage() {
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [cvText, setCvText] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest<{ proposal: string }>(
        "/cv/proposal",
        {
          method: "POST",
          body: JSON.stringify({
            job_url: jobUrl || "manual-entry",
            job_title: jobTitle,
            company_name: companyName,
            user_cv: cvText,
          }),
        },
        true,
      );

      setResult(data.proposal || "");
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo generar la cover letter.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#f8fafc,_#faf5ff_34%,_#ffffff)] p-6 lg:p-8">
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
            <div className="rounded-2xl bg-violet-100 p-3 text-violet-700">
              <FileText size={22} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-600">
                Premium Tool
              </p>
              <h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">
                Cover Letter Generator
              </h1>
            </div>
          </div>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
            Genera una carta de presentacion enfocada en el puesto y la empresa. Para obtener un
            resultado fuerte, pega el texto de tu CV real y el contexto del rol.
          </p>

          {error ? (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </div>
          ) : null}
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm"
          >
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Puesto</span>
              <input
                required
                value={jobTitle}
                onChange={(event) => setJobTitle(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
                placeholder="Frontend Engineer"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Empresa</span>
              <input
                required
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
                placeholder="Acme Inc."
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">URL o referencia</span>
              <input
                value={jobUrl}
                onChange={(event) => setJobUrl(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
                placeholder="https://..."
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Texto de tu CV</span>
              <textarea
                required
                value={cvText}
                onChange={(event) => setCvText(event.target.value)}
                rows={12}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
                placeholder="Pega el texto de tu CV para que la carta use tu experiencia real..."
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-2xl bg-violet-600 px-5 py-3 font-medium text-white hover:bg-violet-700 disabled:opacity-60"
            >
              <Sparkles size={18} />
              {loading ? "Generando..." : "Generar cover letter"}
            </button>
          </form>

          <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                  Resultado
                </p>
                <h2 className="mt-1 text-xl font-semibold text-slate-950">Texto listo para adaptar</h2>
              </div>

              {result ? (
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(result)}
                  className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:border-slate-300 hover:text-slate-950"
                >
                  <Copy size={16} />
                  Copiar
                </button>
              ) : null}
            </div>

            <div className="mt-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
              {result ? (
                <div className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{result}</div>
              ) : (
                <p className="text-sm leading-7 text-slate-500">
                  Completa el formulario para generar una carta enfocada en ese rol. Si tu plan no
                  incluye esta feature, veras el mensaje de upgrade directamente desde la API.
                </p>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
