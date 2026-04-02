"use client"

import { useEffect, useState } from "react"
import { Bell, FileText, Search, TrendingUp } from "lucide-react"

import { apiRequest } from "@/lib/api"

const statIcons = [Search, FileText, TrendingUp, Bell]

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<any | null>(null)
  const [usage, setUsage] = useState<any | null>(null)
  const [recommendedJobs, setRecommendedJobs] = useState<any[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    const load = async () => {
      try {
        const [dashboardData, usageData, jobsData] = await Promise.all([
          apiRequest<any>("/users/dashboard", {}, true),
          apiRequest<any>("/users/usage", {}, true),
          apiRequest<any>("/jobs/recommended", {}, true),
        ])
        setDashboard(dashboardData)
        setUsage(usageData)
        setRecommendedJobs(jobsData.jobs ?? [])
      } catch (err) {
        const detail =
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudo cargar el dashboard."
        setError(detail)
      }
    }

    void load()
  }, [])

  const stats = [
    {
      title: "Empleos trackeados",
      value: String(dashboard?.applications?.length ?? 0),
      change: `${dashboard?.funnel?.interview ?? 0} entrevistas activas`,
      trend: "up",
    },
    {
      title: "Objetivo semanal",
      value: `${dashboard?.weekly_applied ?? 0}/${dashboard?.weekly_goal ?? 0}`,
      change: "Aplicaciones esta semana",
      trend: "up",
    },
    {
      title: "Búsquedas disponibles",
      value: usage?.searches_limit === 0 ? "Ilimitadas" : String(usage?.remaining_searches ?? 0),
      change: usage?.searches_limit === 0 ? "Tu plan no tiene cap" : `${usage?.searches_used ?? 0} usadas hoy`,
      trend: "neutral",
    },
    {
      title: "Alertas",
      value: dashboard?.active_alerts ? "Activas" : "Pausadas",
      change: `Modo ${dashboard?.digest_mode ?? "realtime"}`,
      trend: dashboard?.active_alerts ? "up" : "neutral",
    },
  ]

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">¡Bienvenido de nuevo!</h1>
        <p className="text-slate-600">Estas son las estadísticas reales de tu búsqueda de empleo</p>
      </div>

      {error ? (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = statIcons[index]
          return (
          <div key={stat.title} className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 font-medium">{stat.title}</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{stat.value}</p>
                <p className={`text-sm mt-2 ${
                  stat.trend === "up" ? "text-green-600" : 
                  stat.trend === "down" ? "text-red-600" : "text-slate-500"
                }`}>
                  {stat.change}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
                <Icon className="text-purple-600" size={24} />
              </div>
            </div>
          </div>
        )})}
      </div>

      <div className="bg-white rounded-xl p-6 border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Últimos empleos recomendados</h2>
        <div className="space-y-4">
          {recommendedJobs.length === 0 ? (
            <div className="rounded-lg bg-slate-50 p-4 text-slate-600">
              Configurá mejor tu perfil o hacé una búsqueda manual para empezar a recibir recomendaciones.
            </div>
          ) : recommendedJobs.slice(0, 5).map((job) => (
            <a
              key={job.id}
              href={job.url || "#"}
              target="_blank"
              rel="noreferrer"
              className="flex justify-between items-center p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <div>
                <h3 className="font-medium text-slate-900">{job.title}</h3>
                <p className="text-sm text-slate-600">{job.company} • {job.location}</p>
                <p className="text-xs text-slate-500 mt-1">
                  Match {job.match_score}% • {job.source}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                job.modality === "remote" ? "bg-green-100 text-green-700" :
                job.modality === "hybrid" ? "bg-amber-100 text-amber-700" :
                "bg-slate-100 text-slate-700"
              }`}>
                {job.modality}
              </span>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
