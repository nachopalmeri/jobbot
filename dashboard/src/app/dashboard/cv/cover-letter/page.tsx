"use client";

import { useState } from "react";
import Link from "next/link";
import { Copy, FileText, Loader2, Sparkles } from "lucide-react";

import { apiRequest } from "@/lib/api";

interface ProposalResponse {
  company: string;
  job_title: string;
  proposal: string;
  copied_text: string;
}

export default function CoverLetterPage() {
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [userCv, setUserCv] = useState("");
  const [jobUrlOrDescription, setJobUrlOrDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<ProposalResponse | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const data = await apiRequest<ProposalResponse>("/cv/proposal", {
        method: "POST",
        body: JSON.stringify({
          job_url: jobUrlOrDescription,
          job_description: jobUrlOrDescription,
          job_title: jobTitle,
          company_name: companyName,
          user_cv: userCv,
        }),
      }, true);

      setResult(data);
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No se pudo generar la carta.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,#f6f8fc_0%,#eef2f8_100%)] p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="rounded-[30px] border border-slate-200 bg-white p-7 shadow-sm">
          <Link href="/dashboard/cv" className="text-sm font-medium text-slate-500 hover:text-slate-900">
            Volver a CV Suite
          </Link>
          <div className="mt-4 flex items-center gap-3">
            <div className="rounded-2xl bg-slate-900 p-3 text-white">
              <FileText size={20} />
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
                Cover Letter Generator
              </h1>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                Herramienta premium para generar cartas personalizadas a partir de tu CV y la vacante.
              </p>
            </div>
          </div>
        </section>

        {message ? (
          <div className="rounded-[24px] border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
            {message}
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm"
          >
            <input
              value={jobTitle}
              onChange={(event) => setJobTitle(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
              placeholder="Puesto objetivo"
              required
            />
            <input
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
              placeholder="Empresa"
              required
            />
            <textarea
              value={jobUrlOrDescription}
              onChange={(event) => setJobUrlOrDescription(event.target.value)}
              rows={5}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
              placeholder="Pegá la URL o la descripción del puesto"
              required
            />
            <textarea
              value={userCv}
              onChange={(event) => setUserCv(event.target.value)}
              rows={10}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-400"
              placeholder="Pegá el contenido de tu CV"
              required
            />

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
              Generar carta
            </button>
          </form>

          <section className="rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-950">Resultado</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">
              Vas a obtener un borrador listo para adaptar y enviar.
            </p>

            {result ? (
              <div className="mt-5 space-y-4">
                <div className="rounded-[24px] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-700 whitespace-pre-wrap">
                  {result.proposal}
                </div>
                <button
                  type="button"
                  onClick={() => navigator.clipboard.writeText(result.copied_text)}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:border-slate-300 hover:text-slate-950"
                >
                  <Copy size={16} />
                  Copiar texto
                </button>
              </div>
            ) : (
              <div className="mt-5 rounded-[24px] border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center text-sm text-slate-500">
                Completá el formulario para generar tu primera cover letter.
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
