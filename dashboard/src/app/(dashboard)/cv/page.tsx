"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Coins,
  Crown,
  FileText,
  FileUp,
  History,
  Loader2,
  MessageSquareQuote,
  Sparkles,
  Target,
  Zap,
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

interface ToolCardProps {
  icon: React.ReactNode
  title: string
  description: string
  href: string
  highlight?: boolean
  locked?: boolean
}

const primaryTools: ToolCardProps[] = [
  {
    icon: <BarChart3 className="text-indigo-600" size={24} />,
    title: "Resume Score",
    description: "Score general de estructura, claridad y señales fuertes del CV.",
    href: "#analyzer",
    highlight: true,
  },
  {
    icon: <Sparkles className="text-indigo-600" size={24} />,
    title: "ATS Checker",
    description: "Detectá gaps, secciones flojas y mejoras rápidas antes de aplicar.",
    href: "#analyzer",
    highlight: true,
  },
  {
    icon: <Target className="text-indigo-600" size={24} />,
    title: "Job Matcher",
    description: "Compará tu CV contra una vacante real y encontrá qué te está faltando.",
    href: "#analyzer",
    highlight: true,
  },
]

function scoreTone(score: number | null) {
  if (score === null) {
    return "bg-stone-100 text-stone-700"
  }
  if (score >= 80) {
    return "bg-emerald-100 text-emerald-700"
  }
  if (score >= 60) {
    return "bg-amber-100 text-amber-800"
  }
  return "bg-rose-100 text-rose-700"
}

function ToolCard({ icon, title, description, href, highlight, locked }: ToolCardProps) {
  return (
    <Link
      href={href}
      className={`group rounded-[1.6rem] border p-5 transition-all ${
        highlight
          ? "border-indigo-200 bg-indigo-50 hover:border-indigo-400"
          : locked
            ? "border-stone-200 bg-stone-50 opacity-80"
            : "border-stone-200 bg-white hover:border-indigo-300"
      }`}
    >
      <div className="flex items-start gap-4">
        <div className={`rounded-2xl p-3 ${highlight ? "bg-indigo-100" : "bg-stone-100"}`}>
          {icon}
        </div>
        <div className="flex-1">
          <h3 className={`font-semibold ${highlight ? "text-indigo-950" : "text-stone-950"}`}>
            {title}
          </h3>
          <p className="mt-1 text-sm leading-6 text-stone-600">{description}</p>
          <div className="mt-3 flex items-center gap-1 text-sm font-medium text-indigo-600 group-hover:text-indigo-700">
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
  const [remainingAnalyses, setRemainingAnalyses] = useState(0)
  const [currentPlan, setCurrentPlan] = useState("free")

  useEffect(() => {
    Promise.all([
      apiRequest<{ total_credits: number; unlock_active: boolean }>("/credits/balance", {}, true),
      apiRequest<{ remaining_analyses: number }>("/users/usage", {}, true),
      apiRequest<{ plan: string }>("/subscriptions/status", {}, true),
    ])
      .then(([balanceData, usageData, subscriptionData]) => {
        setCredits(balanceData.total_credits || 0)
        setUnlockActive(balanceData.unlock_active)
        setRemainingAnalyses(usageData.remaining_analyses || 0)
        setCurrentPlan(subscriptionData.plan || "free")
      })
      .catch(() => {
        setCredits(0)
        setUnlockActive(false)
        setRemainingAnalyses(0)
        setCurrentPlan("free")
      })
  }, [result])

  const canSubmit = useMemo(() => Boolean(cvFile || cvText.trim()), [cvFile, cvText])
  const hasPlanQuota = remainingAnalyses > 0
  const canUseProMode = credits > 0 || hasPlanQuota
  const needsProUnlock = mode === "pro" && !canUseProMode
  const canCreateCoverLetter = currentPlan === "premium"
  const canRunMockInterview = currentPlan === "premium"

  const secondaryTools: ToolCardProps[] = [
    {
      icon: <FileText className="text-stone-600" size={24} />,
      title: "Cover Letter",
      description: "Cartas personalizadas para cada aplicación.",
      href: "/dashboard/cv/cover-letter",
      locked: !canCreateCoverLetter,
    },
    {
      icon: <MessageSquareQuote className="text-stone-600" size={24} />,
      title: "Mock Interview",
      description: "Practicá respuestas reales antes de la entrevista.",
      href: "/dashboard/cv/mock-interview",
      locked: !canRunMockInterview,
    },
    {
      icon: <History className="text-stone-600" size={24} />,
      title: "Historial",
      description: "Guardá análisis y compará versiones del CV.",
      href: "/dashboard/cv/historial",
      locked: !unlockActive,
    },
  ]

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

      const data = await apiRequest<ScanResult>(
        "/cv/scan",
        {
          method: "POST",
          body: form,
        },
        true,
      )
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
    <div className="mx-auto max-w-7xl space-y-8 p-6 lg:p-8">
      <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
              CV Intelligence
            </p>
            <div className="mt-3 flex items-center gap-3">
              <div className="rounded-2xl bg-indigo-600 p-3 text-white">
                <Sparkles size={24} />
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
                CV Suite
              </h1>
            </div>
            <p className="mt-4 text-base leading-7 text-stone-600 lg:text-lg">
              La suite está ordenada para un flujo real: primero validás ATS y claridad, después
              comparás contra una vacante y recién ahí entrás a herramientas premium como cover
              letters o mock interviews.
            </p>

            <div className="mt-6 grid gap-3 md:grid-cols-3">
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                  Paso 1
                </p>
                <p className="mt-2 text-sm font-semibold text-stone-950">
                  Escaneá tu CV con modo básico.
                </p>
              </div>
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                  Paso 2
                </p>
                <p className="mt-2 text-sm font-semibold text-stone-950">
                  Sumá una vacante y mirá el match real.
                </p>
              </div>
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                  Paso 3
                </p>
                <p className="mt-2 text-sm font-semibold text-stone-950">
                  Si vale la pena, usá IA para ajustar y aplicar mejor.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[420px]">
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                Básico
              </p>
              <p className="mt-2 text-sm leading-6 text-stone-700">
                ATS Score, estructura y quick wins sin consumir créditos.
              </p>
            </div>
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                Match
              </p>
              <p className="mt-2 text-sm leading-6 text-stone-700">
                Compará contra una vacante y detectá keywords faltantes.
              </p>
            </div>
            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                Premium
              </p>
              <p className="mt-2 text-sm leading-6 text-stone-700">
                Cover letters, mock interviews e historial guardado.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
            Núcleo de análisis
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-stone-950">
            Empezá por estas tres herramientas
          </h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
        {primaryTools.map((tool) => (
          <ToolCard key={tool.title} {...tool} />
        ))}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
            Flujo extendido
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-stone-950">
            Desbloqueá solo cuando de verdad lo necesites
          </h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
        {secondaryTools.map((tool) => (
          <ToolCard key={tool.title} {...tool} />
        ))}
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-[1.75rem] border border-stone-200 bg-[linear-gradient(135deg,_rgba(79,70,229,0.06),_rgba(245,158,11,0.08))] p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-indigo-100 p-3">
            <Coins className="text-indigo-600" size={20} />
          </div>
          <div>
            <span className="font-semibold text-stone-950">{credits} créditos disponibles</span>
            <p className="text-sm text-stone-600">
              {hasPlanQuota
                ? `Tu plan ${currentPlan.toUpperCase()} incluye ${remainingAnalyses} análisis IA restantes este mes.`
                : unlockActive
                  ? "Tenés la suite desbloqueada. La IA avanzada sigue usando créditos o cuota del plan."
                  : "Comprá créditos o subí de plan para análisis IA avanzados."}
            </p>
          </div>
        </div>
        <Link
          href="/dashboard/creditos"
          className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
        >
          {credits === 0 ? "Conseguir créditos" : "Comprar más"}
          <ArrowRight size={16} />
        </Link>
      </section>

      <section id="analyzer" className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <form
          onSubmit={handleAnalyze}
          className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-7"
        >
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
              Analizador principal
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-950">Escaneá tu CV</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
              Subí tu archivo o pegá el contenido. Si además cargás una vacante, te devolvemos
              el match y las keywords faltantes.
            </p>
          </div>

          <div className="mb-6">
            <label className="mb-3 block text-sm font-medium text-stone-800">Modo de análisis</label>
            <div className="grid gap-3 md:grid-cols-2">
              <button
                type="button"
                onClick={() => setMode("basic")}
                className={`rounded-[1.4rem] border px-4 py-4 text-left ${
                  mode === "basic"
                    ? "border-indigo-500 bg-indigo-50"
                    : "border-stone-200 hover:border-indigo-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <BarChart3
                    size={18}
                    className={mode === "basic" ? "text-indigo-600" : "text-stone-400"}
                  />
                  <span
                    className={`font-semibold ${
                      mode === "basic" ? "text-indigo-950" : "text-stone-800"
                    }`}
                  >
                    Básico (Gratis)
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-stone-600">
                  Score ATS, estructura, keywords y quick wins para iterar rápido.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode("pro")}
                disabled={needsProUnlock}
                className={`rounded-[1.4rem] border px-4 py-4 text-left ${
                  mode === "pro"
                    ? "border-indigo-500 bg-indigo-50"
                    : needsProUnlock
                      ? "cursor-not-allowed border-stone-200 opacity-60"
                      : "border-stone-200 hover:border-indigo-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Zap
                    size={18}
                    className={mode === "pro" ? "text-indigo-600" : "text-stone-400"}
                  />
                  <span
                    className={`font-semibold ${
                      mode === "pro" ? "text-indigo-950" : "text-stone-800"
                    }`}
                  >
                    Pro (IA)
                  </span>
                  {credits > 0 || hasPlanQuota ? (
                    <span className="ml-auto rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-700">
                      {credits > 0 ? "1⭐" : "Plan"}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-xs leading-5 text-stone-600">
                  Feedback recruiter, lectura más fina y recomendaciones personalizadas.
                </p>
              </button>
            </div>

            {needsProUnlock ? (
              <div className="mt-3 flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <Crown size={16} />
                <span>Necesitás créditos o un plan con cuota IA para usar el análisis Pro.</span>
                <Link href="/dashboard/suscripcion" className="font-medium underline">
                  Ver planes
                </Link>
              </div>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="rounded-[1.4rem] border border-dashed border-stone-300 bg-stone-50 p-4 text-sm text-stone-700 md:col-span-2">
              <span className="mb-2 flex items-center gap-2 font-medium text-stone-900">
                <FileUp size={16} />
                Tu CV (PDF o TXT)
              </span>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
                className="mt-2 block w-full text-sm text-stone-700"
              />
              <span className="mt-2 block text-xs text-stone-500">
                {cvFile ? `Archivo listo: ${cvFile.name}` : "También podés pegar el texto directamente abajo."}
              </span>
            </label>

            <div className="md:col-span-2">
              <label className="mb-2 block text-sm font-medium text-stone-800">O pegá el texto de tu CV</label>
              <textarea
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                rows={8}
                placeholder="Copiá y pegá el contenido de tu CV aquí..."
                className="w-full rounded-[1.4rem] border border-stone-200 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-800">Puesto objetivo</label>
              <input
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Backend Engineer"
                className="w-full rounded-[1.4rem] border border-stone-200 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-stone-800">Empresa</label>
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Mercado Libre"
                className="w-full rounded-[1.4rem] border border-stone-200 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>

            <div className="md:col-span-2">
              <label className="mb-2 block text-sm font-medium text-stone-800">
                Descripción del puesto (opcional)
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={6}
                placeholder="Pegá la descripción del puesto para obtener match score y keywords faltantes."
                className="w-full rounded-[1.4rem] border border-stone-200 px-4 py-3 outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={loading || !canSubmit || (mode === "pro" && needsProUnlock)}
              className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
              {loading
                ? "Analizando..."
                : mode === "pro"
                  ? `Analizar con IA ${credits > 0 ? "(1⭐)" : hasPlanQuota ? "(Plan)" : ""}`
                  : "Analizar CV"}
            </button>
            <p className="text-sm text-stone-600">
              {mode === "basic"
                ? "Análisis ATS gratuito. No consume créditos."
                : credits > 0
                  ? "Consumirá 1 crédito de tu balance."
                  : hasPlanQuota
                    ? `Consumirá 1 uso de tu plan ${currentPlan.toUpperCase()}.`
                    : "Necesitás créditos o una suscripción con cuota IA."}
            </p>
          </div>
        </form>

        <div className="space-y-6">
          {!result ? (
            <div className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
                Qué devuelve el análisis
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-stone-950">Lectura útil, no ruido</h2>
              <p className="mt-2 text-sm leading-6 text-stone-600">
                La suite te muestra solo lo que ayuda a decidir rápido cómo mejorar tu siguiente aplicación.
              </p>
              <div className="mt-5 space-y-3">
                <div className="flex items-start gap-3 rounded-2xl bg-stone-50 p-4">
                  <BarChart3 size={20} className="mt-0.5 text-indigo-600" />
                  <div>
                    <p className="font-medium text-stone-950">ATS Score</p>
                    <p className="text-sm text-stone-600">Qué tan bien está estructurado para filtros automáticos.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-2xl bg-stone-50 p-4">
                  <Target size={20} className="mt-0.5 text-indigo-600" />
                  <div>
                    <p className="font-medium text-stone-950">Match Score</p>
                    <p className="text-sm text-stone-600">Qué tanto coincide con la vacante que querés atacar.</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-2xl bg-stone-50 p-4">
                  <AlertTriangle size={20} className="mt-0.5 text-indigo-600" />
                  <div>
                    <p className="font-medium text-stone-950">Keywords faltantes</p>
                    <p className="text-sm text-stone-600">Qué skills o términos conviene sumar o visibilizar mejor.</p>
                  </div>
                </div>
                {mode === "pro" ? (
                  <div className="flex items-start gap-3 rounded-2xl border border-indigo-100 bg-indigo-50 p-4">
                    <Sparkles size={20} className="mt-0.5 text-indigo-600" />
                    <div>
                      <p className="font-medium text-indigo-950">Feedback IA</p>
                      <p className="text-sm text-indigo-700">Diagnóstico corto con foco en impacto y claridad.</p>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-stone-500">ATS Score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-3xl font-bold ${scoreTone(result.ats_score)}`}>
                    {result.ats_score}/100
                  </div>
                  <p className="mt-2 text-xs text-stone-500">
                    {result.ats_score >= 80 ? "Excelente" : result.ats_score >= 60 ? "Bueno" : "Necesita mejora"}
                  </p>
                </div>
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <p className="text-sm font-medium text-stone-500">Match Score</p>
                  <div className={`mt-3 inline-flex rounded-full px-4 py-2 text-3xl font-bold ${scoreTone(result.match_score)}`}>
                    {result.match_score ?? "--"}{result.match_score !== null ? "/100" : ""}
                  </div>
                  <p className="mt-2 text-xs text-stone-500">
                    {result.match_score === null
                      ? "Agregá una job description"
                      : result.match_score >= 80
                        ? "Muy buen match"
                        : "Hay espacio para mejorar"}
                  </p>
                </div>
              </div>

              <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-stone-950">Diagnóstico</h2>
                    <p className="text-sm text-stone-500">
                      {result.company_name || result.job_title
                        ? `Objetivo: ${[result.job_title, result.company_name].filter(Boolean).join(" · ")}`
                        : "Scan general de CV"}
                    </p>
                  </div>
                  <div className="text-right text-xs text-stone-500">
                    <div>{result.metrics.word_count} palabras</div>
                    <div>{result.metrics.keyword_count} keywords</div>
                    <div>{result.metrics.action_verb_hits} verbos de acción</div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-stone-900">
                      <CheckCircle2 size={16} className="text-emerald-600" />
                      Fortalezas
                    </p>
                    <ul className="space-y-2 text-sm text-stone-600">
                      {result.strengths.length ? result.strengths.map((item) => (
                        <li key={item} className="rounded-xl bg-emerald-50 px-3 py-2">{item}</li>
                      )) : <li className="rounded-xl bg-stone-50 px-3 py-2">Todavía no encontramos puntos claramente fuertes.</li>}
                    </ul>
                  </div>
                  <div>
                    <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-stone-900">
                      <AlertTriangle size={16} className="text-amber-600" />
                      Quick wins
                    </p>
                    <ul className="space-y-2 text-sm text-stone-600">
                      {result.suggestions.map((item) => (
                        <li key={item} className="rounded-xl bg-amber-50 px-3 py-2">{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-stone-950">Keywords que ya están</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.matching_keywords.length ? result.matching_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-stone-500">Agregá una job description para comparar.</span>}
                  </div>
                </div>

                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-stone-950">Keywords faltantes</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.missing_keywords.length ? result.missing_keywords.map((item) => (
                      <span key={item} className="rounded-full bg-rose-100 px-3 py-1 text-sm font-medium text-rose-700">
                        {item}
                      </span>
                    )) : <span className="text-sm text-stone-500">No detectamos gaps claros. Buen trabajo.</span>}
                  </div>
                </div>
              </div>

              {result.ai_feedback_included && result.ai_feedback ? (
                <div className="rounded-[1.75rem] border border-indigo-200 bg-indigo-50 p-6">
                  <div className="mb-4 flex items-center gap-2">
                    <Sparkles className="text-indigo-600" size={20} />
                    <h3 className="font-semibold text-indigo-950">Feedback IA</h3>
                    {result.used_credits ? (
                      <span className="ml-auto rounded-full bg-indigo-100 px-2 py-1 text-xs font-bold text-indigo-700">
                        Usó 1⭐
                      </span>
                    ) : null}
                  </div>
                  <div className="whitespace-pre-wrap text-sm leading-7 text-indigo-900">
                    {result.ai_feedback}
                  </div>
                </div>
              ) : null}

              <div className="rounded-[1.75rem] border border-stone-200 bg-stone-50 p-6">
                <h3 className="mb-3 font-semibold text-stone-950">Próximos pasos</h3>
                <div className="flex flex-wrap gap-3">
                  <Link
                    href="/dashboard/cv/historial"
                    className="inline-flex items-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 py-2 font-medium text-stone-700 hover:border-indigo-300 hover:text-indigo-700"
                  >
                    <History size={18} />
                    Ver en historial
                  </Link>
                  <button
                    onClick={() => {
                      setResult(null)
                      window.scrollTo({ top: 0, behavior: "smooth" })
                    }}
                    className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700"
                  >
                    <Sparkles size={18} />
                    Analizar otro CV
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
