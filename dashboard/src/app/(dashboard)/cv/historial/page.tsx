"use client"

import { useEffect, useState } from "react"
import { FileText, Calendar, Crown, ArrowLeft, ExternalLink } from "lucide-react"
import Link from "next/link"

import { apiRequest } from "@/lib/api"

interface CVHistoryItem {
  id: number
  type: string
  has_job_match: boolean
  tokens_used: number
  created_at: string
}

interface CVHistoryResponse {
  history: CVHistoryItem[]
  count: number
  unlock_active: boolean
}

export default function CVHistoryPage() {
  const [history, setHistory] = useState<CVHistoryItem[]>([])
  const [unlockActive, setUnlockActive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiRequest<CVHistoryResponse>("/cv/history?limit=50", {}, true)
        setHistory(data.history || [])
        setUnlockActive(data.unlock_active)
      } catch (err) {
        const message =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo cargar el historial."
        setError(message)
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [])

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString("es-AR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Cargando historial...</div>
      </div>
    )
  }

  // Si no tiene unlock activo, mostrar CTA
  if (!unlockActive && !loading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-2 mb-6">
          <Link
            href="/dashboard/cv"
            className="flex items-center gap-1 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <ArrowLeft size={18} />
            <span>Volver a CV Suite</span>
          </Link>
        </div>

        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
          <div className="bg-purple-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Crown className="text-purple-600" size={40} />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mb-3">Historial de Análisis</h1>
          <p className="text-slate-600 mb-6 max-w-md mx-auto">
            Desbloqueá CV Suite para guardar y acceder a todos tus análisis de CV anteriores.
            Nunca pierdas una recomendación útil.
          </p>
          <Link
            href="/dashboard/creditos"
            className="inline-flex items-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-purple-700 transition-colors"
          >
            <Crown size={20} />
            Desbloquear CV Suite
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Link
          href="/dashboard/cv"
          className="flex items-center gap-1 text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Volver a CV Suite</span>
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-slate-900 mb-2">📜 Historial de Análisis</h1>
      <p className="text-slate-600 mb-6">
        Todos tus scans de CV guardados. Accedé a cualquier momento.
      </p>

      {error && (
        <div className="mb-6 rounded-lg bg-red-100 px-4 py-3 text-red-700">
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 border border-slate-200 text-center">
          <div className="bg-slate-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="text-slate-400" size={32} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Sin análisis aún</h3>
          <p className="text-slate-600 mb-4">
            Todavía no realizaste ningún análisis de CV. Empezá ahora.
          </p>
          <Link
            href="/dashboard/cv"
            className="inline-flex items-center gap-2 bg-purple-600 text-white px-5 py-2.5 rounded-lg font-semibold hover:bg-purple-700 transition-colors"
          >
            Analizar mi CV
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl p-5 border border-slate-200 hover:border-purple-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="text-purple-600" size={24} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">
                      Análisis de CV #{item.id}
                    </h3>
                    <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <Calendar size={14} />
                        {formatDate(item.created_at)}
                      </span>
                      {item.has_job_match && (
                        <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs">
                          Con job match
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <Link
                  href={`/dashboard/cv/historial/${item.id}`}
                  className="flex items-center gap-1 text-purple-600 hover:text-purple-700 font-medium text-sm"
                >
                  Ver detalle
                  <ExternalLink size={14} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
