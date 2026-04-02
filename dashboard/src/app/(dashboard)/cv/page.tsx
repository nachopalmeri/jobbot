"use client"

import { useMemo, useState } from "react"
import { AlertTriangle, BarChart3, CheckCircle2, FileUp, Loader2, Sparkles } from "lucide-react"

import { apiRequest } from "@/lib/api"

type ScanResult = {
  ats_score: number
  match_score: number | null
  matching_keywords: string[]
  missing_keywords: string[]
  extra_keywords: string[]
  suggestions: string[]
  strengths: string[]
  sections: Record<string, boolean>
  metrics: {
    word_count: number
    keyword_count: number
    action_verb_hits: number
    metric_hits: number
  }
  quota: {
    used: number
    limit: number
    remaining: number
    ai_enabled: boolean
  }
  ai_feedback: string | null
  ai_feedback_included: boolean
  job_title: string
  company_name: string
}

function scoreTone(score: number | null) {
  if (score === null) {
    return "bg-slate-100 text-slate-700"
  }
  if (score >= 80) {
    return "bg-emerald-100 text-emerald-700"
  }
  if (score >= 60) {
    return "bg-amber-100 text-amber-700"
  }
  return "bg-rose-100 text-rose-700"
}

export default function CVPage() {
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState("")
  const [jobTitle, setJobTitle] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<ScanResult | null>(null)

  const canSubmit = useMemo(() => Boolean(cvFile || cvText.trim()), [cvFile, cvText])

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const form = new FormData()
      if (cvFile) {
        form.append("cv_file", cvFile)
      }
      if (cvText.trim()) {
        form.append("cv_text", cvText.trim())
      }
      if (jobTitle.trim()) {
        form.append("job_title", jobTitle.trim())
      }
      if (companyName.trim()) {
        form.append("company_name", companyName.trim())
      }
      if (jobDescription.trim()) {
        form.append("job_description", jobDescription.trim())
      }

      const data = await apiRequest<ScanResult>("/cv/scan", {
        method: "POST",
        body: form,
      }, true)
      setResult(data)
    } catch (err) {
      setError(
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo analizar tu CV.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 rounded-full bg-purple-50 px-3 py-1 text-sm font-medium text-purple-700">
          <Sparkles size={16} />
          CV Intelligence
        </div>
        <h1 className="mt-3 text-3xl font-bold text-slate-900">Rank my CV</h1>
        <p className="mt-2 max-w-3xl text-slate-600">
          Subí tu CV o pegalo acá, agregá una job description y obtené score ATS, gaps de keywords y feedback accionable para aplicar mejor.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={handleAnalyze} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 md:col-span-2">
              <span className="mb-2 flex items-center gap-2 font-medium text-slate-800">
                <FileUp size={16} />
                CV en PDF o TXT
              </span>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
                className="mt-2 block w-full text-sm text-slate-500"
              />
              <span className="mt-2 block text-xs text-slate-500">
                {cvFile ? `Archivo listo: ${cvFile.name}` : "También podés pegar el texto directamente abajo."}
              </span>
            </label>

            <div className="md:col-span-2">
              <label className="mb-2 block text-sm font-medium text-slate-700">Texto del CV</label>
              <textarea
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={10}
                placeholder="Pegá acá el contenido de tu CV si no querés subir un archivo."
                className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Puesto objetivo</label>
              <input
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Backend Engineer"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Empresa</label>
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Mercado Libre"
                className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-purple-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="mb-2 block text-sm font-medium text-slate-700">Job description</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={9}
                placeholder="Pegá la descripción del puesto para obtener un match score y keywords faltantes."
                className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-purple-500"
              />
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading || !canSubmit}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <BarChart3 size={18} />}
              {loading ? "Analizando..." : "Analizar CV"}
            </button>
            <p className="text-sm text-slate-500">
              Sin job description obtenés score ATS y mejoras generales. Con job description sumás match score.
            </p>
          </div>
        </form>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Qué vas a ver</h2>
            <div className="mt-4 grid gap-3">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="font-medium text-slate-900">ATS score</p>
                <p className="mt-1 text-sm text-slate-600">Qué tan bien está estructurado tu CV para pasar filtros automáticos.</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="font-medium text-slate-900">Match score</p>
                <p className="mt-1 text-sm text-slate-600">Qué tanto coincide tu CV con la vacante específica que querés atacar.</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="font-medium text-slate-900">Missing keywords</p>
                <p className="mt-1 text-sm text-slate-600">Las skills y términos que hoy te están faltando o no están bien visibles.</p>
              </div>
            </div>
          </div>

          {result ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">ATS score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-2xl font-bold ${scoreTone(result.ats_score)}`}>
                    {result.ats_score}/100
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">Match score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-2xl font-bold ${scoreTone(result.match_score)}`}>
                    {result.match_score ?? "--"}{result.match_score !== null ? "/100" : ""}
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Diagnóstico</h2>
                    <p className="text-sm text-slate-500">
                      {result.company_name || result.job_title
                        ? `Objetivo: ${[result.job_title, result.company_name].filter(Boolean).join(" · ")}`
                        : "Scan general de CV"}
                    </p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <div>{result.metrics.word_count} palabras</div>
                    <div>{result.metrics.keyword_count} keywords técnicas</div>
                  </div>
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800">
                      <CheckCircle2 size={16} className="text-emerald-600" />
                      Fortalezas
                    </p>
                    <ul className="space-y-2 text-sm text-slate-600">
                      {result.strengths.length ? result.strengths.map((item) => (
                        <li key={item} className="rounded-lg bg-emerald-50 px-3 py-2">{item}</li>
                      )) : <li className="rounded-lg bg-slate-50 px-3 py-2">Todavía no encontramos puntos claramente fuertes.</li>}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800">
                      <AlertTriangle size={16} className="text-amber-600" />
                      Quick wins
                    </p>
                    <ul className="space-y-2 text-sm text-slate-600">
                      {result.suggestions.map((item) => (
                        <li key={item} className="rounded-lg bg-amber-50 px-3 py-2">{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-900">Keywords que ya tenés</h3>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {result.matching_keywords.length ? result.matching_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-slate-500">Agregá una job description para comparar tu match.</span>}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-900">Keywords faltantes</h3>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {result.missing_keywords.length ? result.missing_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-rose-100 px-3 py-1 text-sm font-medium text-rose-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-slate-500">No detectamos gaps claros, o faltó la job description.</span>}
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-base font-semibold text-slate-900">Feedback IA</h3>
                  <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                    {result.quota.ai_enabled
                      ? `${result.quota.remaining} análisis IA restantes`
                      : "Upgrade para feedback IA"}
                  </div>
                </div>
                <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm leading-7 text-slate-700 whitespace-pre-wrap">
                  {result.ai_feedback || "Este scan te dio score y quick wins heurísticos. Para sumar feedback IA completo, necesitás cuota de análisis en tu plan."}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
