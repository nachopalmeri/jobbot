"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { ExternalLink, Loader2, Search, Sparkles } from "lucide-react"

import { apiRequest } from "@/lib/api"

const modalityLabels: Record<string, string> = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
}

const scheduleLabels: Record<string, string> = {
  all: "Cualquiera",
  full_time: "Jornada completa",
  part_time: "Media jornada",
}

const suggestedSearches = [
  "python backend",
  "frontend react",
  "data analyst junior",
  "product designer",
]

interface SearchJob {
  id: string
  title: string
  company: string
  location: string
  modality: string
  match_score: number
  description: string
  source: string
  url?: string
}

interface PreferencesSnapshot {
  role_type: string
  technologies: string
  location: string
  job_modality: string
  job_schedule: string
}

export default function BuscarPage() {
  const [query, setQuery] = useState("")
  const [modality, setModality] = useState("all")
  const [schedule, setSchedule] = useState("all")
  const [jobs, setJobs] = useState<SearchJob[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [hasSearched, setHasSearched] = useState(false)
  const [lastQueryLabel, setLastQueryLabel] = useState("tu perfil")
  const [requestLabel, setRequestLabel] = useState("")
  const [preferences, setPreferences] = useState<PreferencesSnapshot | null>(null)

  useEffect(() => {
    apiRequest<PreferencesSnapshot>("/users/preferences", {}, true)
      .then((data) => {
        setPreferences(data)
        if (data.job_modality && data.job_modality !== "cualquiera") {
          const normalizedModality = data.job_modality.normalize("NFD").replace(/\p{Diacritic}/gu, "")
          const mappedModality =
            normalizedModality === "remoto"
              ? "remote"
              : normalizedModality === "hibrido"
                ? "hybrid"
                : normalizedModality === "presencial"
                  ? "onsite"
                  : "all"
          setModality(mappedModality)
        }
        if (data.job_schedule && data.job_schedule !== "cualquiera") {
          setSchedule(data.job_schedule)
        }
      })
      .catch(() => setPreferences(null))
  }, [])

  const runSearch = useCallback(async (customQuery: string, customModality: string, customSchedule: string) => {
    try {
      setLoading(true)
      setError("")
      setHasSearched(true)

      const params = new URLSearchParams()
      if (customQuery.trim()) {
        params.set("q", customQuery.trim())
      }
      if (customModality !== "all") {
        params.set("modality", customModality)
      }
      if (customSchedule !== "all") {
        params.set("schedule", customSchedule)
      }
      params.set("limit", "20")

      const label = customQuery.trim() || "tu perfil"
      setRequestLabel(label)

      const data = await apiRequest<{ jobs: SearchJob[]; total: number }>(
        `/jobs/search?${params.toString()}`,
        {},
        true,
      )

      setJobs(data.jobs || [])
      setTotal(data.total || 0)
      setLastQueryLabel(label)
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo ejecutar la búsqueda."
      setError(detail)
    } finally {
      setLoading(false)
    }
  }, [])

  const summary = useMemo(() => {
    if (!hasSearched) {
      return "Elegí una búsqueda o usá tu perfil para pedirle al motor del bot resultados reales."
    }
    if (loading) {
      return `Buscando oportunidades para ${requestLabel}...`
    }
    return `${total} resultados para ${lastQueryLabel}.`
  }, [hasSearched, lastQueryLabel, loading, requestLabel, total])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6 lg:p-8">
      <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
              Motor de búsqueda
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
              Buscar empleos con una intención clara
            </h1>
            <p className="mt-4 text-base leading-7 text-stone-600">
              Corrés la búsqueda cuando querés, con modalidad, jornada y una intención concreta.
              Si no escribís query, JobBot usa tu perfil guardado como punto de partida.
            </p>
          </div>

          <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-5 py-4 text-sm leading-6 text-stone-700 xl:max-w-sm">
            <p className="font-semibold text-stone-950">Cómo funciona</p>
            <p className="mt-2">
              Primero filtramos por perfil, modalidad y jornada. Después ordenamos por match para
              que no se mezclen ofertas demasiado genéricas.
            </p>
          </div>
        </div>
      </section>

      {preferences ? (
        <section className="grid gap-4 lg:grid-cols-4">
          <article className="rounded-[1.5rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Rol</p>
            <p className="mt-2 text-base font-semibold text-stone-950">
              {preferences.role_type || "Sin definir"}
            </p>
          </article>
          <article className="rounded-[1.5rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Stack</p>
            <p className="mt-2 text-base font-semibold text-stone-950">
              {preferences.technologies || "Sin definir"}
            </p>
          </article>
          <article className="rounded-[1.5rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Modalidad</p>
            <p className="mt-2 text-base font-semibold text-stone-950">
              {preferences.job_modality || "cualquiera"}
            </p>
          </article>
          <article className="rounded-[1.5rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Jornada</p>
            <p className="mt-2 text-base font-semibold text-stone-950">
              {scheduleLabels[preferences.job_schedule || "all"] || "Cualquiera"}
            </p>
          </article>
        </section>
      ) : null}

      <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-5 shadow-sm">
        <div className="flex flex-col gap-4">
          <div className="grid gap-3 xl:grid-cols-[1.2fr_0.32fr_0.32fr_auto_auto]">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" size={18} />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    void runSearch(query, modality, schedule)
                  }
                }}
                placeholder="Python backend, React, data analyst..."
                className="w-full rounded-2xl border border-stone-200 bg-white py-3 pl-11 pr-4 text-stone-950 outline-none focus:border-indigo-400"
              />
            </div>

            <select
              value={modality}
              onChange={(e) => setModality(e.target.value)}
              className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
              >
                <option value="all">Cualquier modalidad</option>
                <option value="remote">Remoto</option>
                <option value="hybrid">Híbrido</option>
                <option value="onsite">Presencial</option>
              </select>

            <select
              value={schedule}
              onChange={(e) => setSchedule(e.target.value)}
              className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-950 outline-none focus:border-indigo-400"
            >
              <option value="all">Cualquier jornada</option>
              <option value="full_time">Jornada completa</option>
              <option value="part_time">Media jornada</option>
            </select>

            <button
              onClick={() => void runSearch(query, modality, schedule)}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-stone-950 px-5 py-3 font-medium text-white hover:bg-stone-800 disabled:opacity-60"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
              {loading ? "Buscando..." : "Buscar ahora"}
            </button>

            <button
              onClick={() => void runSearch("", modality, schedule)}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-indigo-200 bg-indigo-50 px-5 py-3 font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-60"
            >
              <Sparkles size={18} />
              Usar mi perfil guardado
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {suggestedSearches.map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => {
                  setQuery(term)
                  void runSearch(term, modality, schedule)
                }}
                className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-sm font-medium text-stone-700 hover:border-indigo-300 hover:text-indigo-700"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-stone-200 bg-white/90 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-stone-600">{summary}</p>
            {hasSearched && !loading ? (
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
                  {total} resultados
                </span>
                <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
                  {modalityLabels[modality] || "Todas las modalidades"}
                </span>
                <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-700">
                  {scheduleLabels[schedule]}
                </span>
              </div>
            ) : null}
          </div>
      </section>

      {error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
          {error}
        </div>
      ) : null}

      {!hasSearched ? (
        <section className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-stone-950">1. Elegí una intención</p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Podés escribir una búsqueda concreta o dejarla vacía para usar tu perfil.
            </p>
          </div>
          <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-stone-950">2. Filtrá modalidad</p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Modalidad y jornada se aplican antes de mostrar resultados.
            </p>
          </div>
          <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-stone-950">3. Corré la búsqueda</p>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Una vez lanzada, el panel muestra resultados reales y deja de parecer “trabado”.
            </p>
          </div>
        </section>
      ) : null}

      {loading ? (
        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-10 text-center shadow-sm">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <Loader2 size={24} className="animate-spin" />
          </div>
          <p className="mt-4 text-lg font-semibold text-stone-950">Buscando oportunidades reales</p>
          <p className="mt-2 text-sm text-stone-600">
            Esto consulta el motor del bot con tu perfil y filtros actuales.
          </p>
        </section>
      ) : null}

      {!loading && hasSearched ? (
        <section className="space-y-4">
          {jobs.map((job) => (
            <article key={job.id} className="rounded-[1.75rem] border border-stone-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-stone-950">{job.title}</h2>
                    <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                      Match {job.match_score}%
                    </span>
                    <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-medium text-stone-700">
                      {modalityLabels[job.modality] || job.modality}
                    </span>
                  </div>
                  <p className="mt-1 text-stone-600">
                    {job.company} · {job.location} · {job.source}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-stone-600">{job.description}</p>
                </div>

                <a
                  href={job.url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-2xl bg-stone-950 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800"
                >
                  Ver oferta
                  <ExternalLink size={16} />
                </a>
              </div>
            </article>
          ))}

          {jobs.length === 0 ? (
            <div className="rounded-[2rem] border border-dashed border-stone-300 bg-white p-8 text-center text-stone-500">
              No encontramos resultados para esta búsqueda. Probá con otra query o usá “tu perfil”.
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}
