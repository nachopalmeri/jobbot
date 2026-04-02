"use client"

import { useEffect, useState } from "react"

import { apiRequest } from "@/lib/api"

const defaultPreferences = {
  experience_level: "junior",
  role_type: "",
  technologies: "",
  job_modality: "cualquiera",
  weekly_goal: 10,
  digest_mode: "realtime",
  active_alerts: false,
}

export default function ConfiguracionPage() {
  const [form, setForm] = useState(defaultPreferences)
  const [message, setMessage] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    apiRequest<any>("/users/preferences", {}, true)
      .then((data) => setForm((prev) => ({ ...prev, ...data })))
      .catch(() => setMessage("No se pudieron cargar tus preferencias actuales."))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")
    try {
      await apiRequest("/users/preferences", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          alert_channel: "telegram",
          check_interval_hours: 6,
          alert_start_hour: 8,
          alert_end_hour: 22,
          timezone: "America/Buenos_Aires",
          blocked_companies: "",
          preferred_companies: "",
          max_job_age_days: 30,
          match_threshold: 70,
        }),
      }, true)
      setMessage("Preferencias guardadas.")
    } catch (err) {
      setMessage(
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudieron guardar los cambios.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Configuración</h1>
      <p className="text-slate-600 mb-6">Ajustá tu perfil para mejorar búsquedas y alertas.</p>
      {message ? <div className="mb-4 rounded-lg bg-slate-100 px-4 py-3 text-slate-700">{message}</div> : null}
      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">Nivel</label>
          <select
            value={form.experience_level}
            onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
            className="w-full rounded-lg border border-slate-200 px-4 py-3"
          >
            <option value="sin_experiencia">Sin experiencia</option>
            <option value="junior">Junior</option>
            <option value="semi_senior">Semi senior</option>
            <option value="senior">Senior</option>
          </select>
        </div>
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">Rol buscado</label>
          <input
            value={form.role_type}
            onChange={(e) => setForm({ ...form, role_type: e.target.value })}
            className="w-full rounded-lg border border-slate-200 px-4 py-3"
            placeholder="backend, data, frontend..."
          />
        </div>
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">Tecnologías</label>
          <input
            value={form.technologies}
            onChange={(e) => setForm({ ...form, technologies: e.target.value })}
            className="w-full rounded-lg border border-slate-200 px-4 py-3"
            placeholder="Python, SQL, React..."
          />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
          <div>
            <p className="font-medium text-slate-900">Alertas activas</p>
            <p className="text-sm text-slate-500">Controla si el bot monitorea oportunidades automáticamente.</p>
          </div>
          <input
            type="checkbox"
            checked={form.active_alerts}
            onChange={(e) => setForm({ ...form, active_alerts: e.target.checked })}
            className="h-5 w-5"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-purple-600 px-5 py-3 font-medium text-white hover:bg-purple-700 disabled:opacity-60"
        >
          {loading ? "Guardando..." : "Guardar cambios"}
        </button>
      </form>
    </div>
  )
}
