"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { 
  AlertTriangle, 
  BarChart3, 
  CheckCircle2, 
  FileUp, 
  Loader2, 
  Sparkles, 
  Crown,
  Zap,
  History,
  FileText,
  Target,
  ArrowRight,
  Coins
} from "lucide-react"

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
  credits?: {
    total: number
    unlock_active: boolean
  } | null
  ai_feedback: string | null
  ai_feedback_included: boolean
  job_title: string
  company_name: string
  mode: string
  used_credits: boolean
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

interface ToolCardProps {
  icon: React.ReactNode
  title: string
  description: string
  href: string
  highlight?: boolean
  locked?: boolean
}

function ToolCard({ icon, title, description, href, highlight, locked }: ToolCardProps) {
  return (
    <Link
      href={href}
      className={`group rounded-xl p-5 border-2 transition-all ${
        highlight 
          ? "border-purple-200 bg-purple-50/50 hover:border-purple-400" 
          : locked
            ? "border-slate-200 bg-slate-50 opacity-75"
            : "border-slate-200 bg-white hover:border-purple-300"
      }`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${highlight ? "bg-purple-100" : "bg-slate-100"}`}>
          {icon}
        </div>
        <div className="flex-1">
          <h3 className={`font-semibold ${highlight ? "text-purple-900" : "text-slate-900"}`}>
            {title}
          </h3>
          <p className="text-sm text-slate-600 mt-1">{description}</p>
          <div className="flex items-center gap-1 mt-3 text-sm font-medium text-purple-600 group-hover:text-purple-700">
            <span>Usar herramienta</span>
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </div>
    </Link>
  )
}

export default function CVPage() {
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState("")
  const [jobTitle, setJobTitle] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [mode, setMode] = useState<"basic" | "pro">("basic")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<ScanResult | null>(null)
  const [credits, setCredits] = useState(0)
  const [unlockActive, setUnlockActive] = useState(false)

  useEffect(() => {
    // Cargar créditos disponibles
    apiRequest<{ total_credits: number; unlock_active: boolean }>("/credits/balance", {}, true)
      .then((data) => {
        setCredits(data.total_credits || 0)
        setUnlockActive(data.unlock_active)
      })
      .catch(() => {
        setCredits(0)
        setUnlockActive(false)
      })
  }, [result]) // Recargar después de un scan

  const canSubmit = useMemo(() => Boolean(cvFile || cvText.trim()), [cvFile, cvText])
  const needsCredits = mode === "pro" && credits === 0 && !unlockActive

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
      form.append("mode", mode)

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
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-2 rounded-lg">
            <Sparkles className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-bold text-slate-900">CV Suite</h1>
        </div>
        <p className="text-slate-600 max-w-2xl">
          Herramientas profesionales para optimizar tu CV y aumentar tus chances de conseguir entrevistas. 
          Análisis ATS, match con ofertas, y feedback con IA.
        </p>
      </div>

      {/* Tools Grid */}
      {!result && (
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <ToolCard
            icon={<BarChart3 className="text-purple-600" size={24} />}
            title="Resume Score"
            description="Score general de tu CV basado en estructura, contenido y formato."
            href="#analyzer"
            highlight
          />
          <ToolCard
            icon={<Target className="text-purple-600" size={24} />}
            title="Job Matcher"
            description="Compará tu CV contra una oferta específica y descubrí qué te falta."
            href="#analyzer"
            highlight
          />
          <ToolCard
            icon={<History className="text-slate-600" size={24} />}
            title="Historial"
            description="Accedé a todos tus análisis previos y compará versiones."
            href="/dashboard/cv/historial"
            locked={!unlockActive}
          />
          <ToolCard
            icon={<FileText className="text-slate-600" size={24} />}
            title="Cover Letter"
            description="Generá cartas de presentación personalizadas con IA."
            href="/dashboard/cv/cover-letter"
            locked={credits === 0}
          />
        </div>
      )}

      {/* Credit Status Bar */}
      <div className="bg-white rounded-xl p-4 border border-slate-200 mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-purple-100 p-2 rounded-lg">
            <Coins className="text-purple-600" size={20} />
          </div>
          <div>
            <span className="font-semibold text-slate-900">{credits} créditos disponibles</span>
            <p className="text-sm text-slate-500">
              {unlockActive ? "CV Suite desbloqueado" : "Comprá créditos para análisis IA"}
            </p>
          </div>
        </div>
        <Link
          href="/dashboard/creditos"
          className="text-purple-600 hover:text-purple-700 font-medium text-sm flex items-center gap-1"
        >
          {credits === 0 ? "Conseguir créditos" : "Comprar más"}
          <ArrowRight size={16} />
        </Link>
      </div>

      {/* Main Analyzer */}
      <div id="analyzer" className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={handleAnalyze} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {/* Mode Selector */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-3">Modo de análisis</label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setMode("basic")}
                className={`flex-1 py-3 px-4 rounded-xl border-2 text-left transition-colors ${
                  mode === "basic"
                    ? "border-purple-500 bg-purple-50"
                    : "border-slate-200 hover:border-purple-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <BarChart3 size={18} className={mode === "basic" ? "text-purple-600" : "text-slate-400"} />
                  <span className={`font-semibold ${mode === "basic" ? "text-purple-900" : "text-slate-700"}`}>
                    Básico (Gratis)
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 ml-6">
                  Score ATS, estructura, keywords
                </p>
              </button>
              
              <button
                type="button"
                onClick={() => setMode("pro")}
                disabled={needsCredits}
                className={`flex-1 py-3 px-4 rounded-xl border-2 text-left transition-colors ${
                  mode === "pro"
                    ? "border-purple-500 bg-purple-50"
                    : needsCredits
                      ? "border-slate-200 opacity-50 cursor-not-allowed"
                      : "border-slate-200 hover:border-purple-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Zap size={18} className={mode === "pro" ? "text-purple-600" : "text-slate-400"} />
                  <span className={`font-semibold ${mode === "pro" ? "text-purple-900" : "text-slate-700"}`}>
                    Pro (IA)
                  </span>
                  {credits > 0 && (
                    <span className="ml-auto bg-purple-100 text-purple-700 text-xs font-bold px-2 py-0.5 rounded-full">
                      1⭐
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1 ml-6">
                  + Feedback personalizado con IA
                </p>
              </button>
            </div>
            
            {needsCredits && (
              <div className="mt-3 p-3 bg-amber-50 rounded-lg text-sm text-amber-800 flex items-center gap-2">
                <Crown size={16} />
                <span>Necesitás créditos para análisis Pro.</span>
                <Link href="/dashboard/creditos" className="underline font-medium">
                  Conseguir ahora →
                </Link>
              </div>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 md:col-span-2">
              <span className="mb-2 flex items-center gap-2 font-medium text-slate-800">
                <FileUp size={16} />
                Tu CV (PDF o TXT)
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
              <label className="mb-2 block text-sm font-medium text-slate-700">O pegá el texto de tu CV</label>
              <textarea
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={8}
                placeholder="Copiá y pegá el contenido de tu CV aquí..."
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
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Descripción del puesto (opcional)
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                placeholder="Pegá la descripción del puesto para obtener match score y keywords faltantes. Podés usar una URL de LinkedIn o pegar el texto directamente."
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
              disabled={loading || !canSubmit || (mode === "pro" && needsCredits)}
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-6 py-3 font-semibold text-white hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
              {loading 
                ? "Analizando..." 
                : mode === "pro" 
                  ? `Analizar con IA ${credits > 0 ? "(1⭐)" : ""}`
                  : "Analizar CV"
              }
            </button>
            <p className="text-sm text-slate-500">
              {mode === "basic" 
                ? "Análisis ATS gratuito. No consume créditos."
                : credits > 0 
                  ? "Consumirá 1 crédito de tu balance."
                  : "Necesitás créditos para usar el modo Pro."
              }
            </p>
          </div>
        </form>

        {/* Results Panel */}
        <div className="space-y-6">
          {/* What you'll get */}
          {!result && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Qué vas a obtener</h2>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                  <BarChart3 size={20} className="text-purple-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-900">ATS Score</p>
                    <p className="text-sm text-slate-600">Qué tan bien está estructurado para filtros automáticos.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                  <Target size={20} className="text-purple-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-900">Match Score</p>
                    <p className="text-sm text-slate-600">Qué tanto coincide con la vacante específica.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                  <AlertTriangle size={20} className="text-purple-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-900">Keywords faltantes</p>
                    <p className="text-sm text-slate-600">Skills y términos que deberías agregar.</p>
                  </div>
                </div>
                {mode === "pro" && (
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-purple-50 border border-purple-100">
                    <Sparkles size={20} className="text-purple-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-purple-900">Feedback IA</p>
                      <p className="text-sm text-purple-700">Recomendaciones personalizadas por IA.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Results */}
          {result ? (
            <div className="space-y-6">
              {/* Score Cards */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">ATS Score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-3xl font-bold ${scoreTone(result.ats_score)}`}>
                    {result.ats_score}/100
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {result.ats_score >= 80 ? "Excelente" : result.ats_score >= 60 ? "Bueno" : "Necesita mejora"}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">Match Score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-3xl font-bold ${scoreTone(result.match_score)}`}>
                    {result.match_score ?? "--"}{result.match_score !== null ? "/100" : ""}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {result.match_score === null 
                      ? "Agregá una job description" 
                      : result.match_score >= 80 
                        ? "Muy buen match" 
                        : "Hay espacio para mejorar"
                    }
                  </p>
                </div>
              </div>

              {/* Main Analysis */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
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
                    <div>{result.metrics.keyword_count} keywords</div>
                    <div>{result.metrics.action_verb_hits} verbos de acción</div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
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

              {/* Keywords */}
              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">✅ Keywords que tenés</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.matching_keywords.length ? result.matching_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-slate-500">Agregá una job description para comparar.</span>}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">⚠️ Keywords faltantes</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.missing_keywords.length ? result.missing_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-rose-100 px-3 py-1 text-sm font-medium text-rose-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-slate-500">No detectamos gaps claros. ¡Buen trabajo!</span>}
                  </div>
                </div>
              </div>

              {/* AI Feedback */}
              {result.ai_feedback_included && result.ai_feedback && (
                <div className="rounded-2xl border border-purple-200 bg-purple-50 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="text-purple-600" size={20} />
                    <h3 className="font-semibold text-purple-900">Feedback IA</h3>
                    {result.used_credits && (
                      <span className="ml-auto bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded-full">
                        Usó 1⭐
                      </span>
                    )}
                  </div>
                  <div className="text-sm leading-7 text-purple-800 whitespace-pre-wrap">
                    {result.ai_feedback}
                  </div>
                </div>
              )}

              {/* Next Steps */}
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                <h3 className="font-semibold text-slate-900 mb-3">Próximos pasos</h3>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/dashboard/cv/historial"
                    className="inline-flex items-center gap-2 bg-white border border-slate-200 px-4 py-2 rounded-lg font-medium text-slate-700 hover:border-purple-300 hover:text-purple-700 transition-colors"
                  >
                    <History size={18} />
                    Ver en historial
                  </Link>
                  <button
                    onClick={() => {
                      setResult(null)
                      window.scrollTo({ top: 0, behavior: "smooth" })
                    }}
                    className="inline-flex items-center gap-2 bg-purple-600 px-4 py-2 rounded-lg font-medium text-white hover:bg-purple-700 transition-colors"
                  >
                    <Sparkles size={18} />
                    Analizar otro CV
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
