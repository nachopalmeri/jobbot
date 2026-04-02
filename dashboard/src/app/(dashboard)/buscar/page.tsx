"use client"

import { useEffect, useState } from "react"
import { ExternalLink, Search } from "lucide-react"

import { apiRequest } from "@/lib/api"

const modalityLabels: Record<string, string> = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
}

export default function BuscarPage() {
  const [query, setQuery] = useState("")
  const [modality, setModality] = useState("all")
  const [jobs, setJobs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const runSearch = async (customQuery = query, customModality = modality) => {
    try {
      setLoading(true)
      setError("")
      const params = new URLSearchParams()
      if (customQuery.trim()) {
        params.set("q", customQuery.trim())
      }
      if (customModality !== "all") {
        params.set("modality", customModality)
      }
      params.set("limit", "20")

      const data = await apiRequest<{ jobs: any[]; total: number }>(
        `/jobs/search?${params.toString()}`,
        {},
        true,
      )
      setJobs(data.jobs || [])
      setTotal(data.total || 0)
    } catch (err) {
      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo ejecutar la búsqueda."
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void runSearch("")
  }, [])

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Buscar empleos</h1>
        <p className="text-slate-600">Resultados reales desde el motor del bot y la API.</p>
      </div>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  void runSearch()
                }
              }}
              placeholder="Python, React, backend, data..."
              className="w-full rounded-lg border border-slate-200 py-3 pl-10 pr-4 outline-none focus:border-purple-500"
            />
          </div>
          <select
            value={modality}
            onChange={(e) => setModality(e.target.value)}
            className="rounded-lg border border-slate-200 px-4 py-3 outline-none focus:border-purple-500"
          >
            <option value="all">Cualquier modalidad</option>
            <option value="remote">Remoto</option>
            <option value="hybrid">Híbrido</option>
            <option value="onsite">Presencial</option>
          </select>
          <button
            onClick={() => void runSearch()}
            disabled={loading}
            className="rounded-lg bg-purple-600 px-5 py-3 font-medium text-white hover:bg-purple-700 disabled:opacity-60"
          >
            {loading ? "Buscando..." : "Buscar"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">
          {error}
        </div>
      ) : null}

      <div className="mb-4 text-sm text-slate-500">
        {total} resultados encontrados
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <div key={job.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-semibold text-slate-900">{job.title}</h2>
                  <span className="rounded-full bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700">
                    Match {job.match_score}%
                  </span>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                    {modalityLabels[job.modality] || job.modality}
                  </span>
                </div>
                <p className="mt-1 text-slate-600">
                  {job.company} • {job.location} • {job.source}
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-600">{job.description}</p>
              </div>
              <a
                href={job.url || "#"}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              >
                Ver oferta
                <ExternalLink size={16} />
              </a>
            </div>
          </div>
        ))}
        {!loading && jobs.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
            No hay resultados para esta búsqueda todavía.
          </div>
        ) : null}
      </div>
    </div>
  )
}
