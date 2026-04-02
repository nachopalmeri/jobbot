"use client"

import { useEffect, useState } from "react"

import { apiRequest } from "@/lib/api"

export default function PostulacionesPage() {
  const [applications, setApplications] = useState<any[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    apiRequest<{ applications: any[] }>("/jobs/applications", {}, true)
      .then((data) => setApplications(data.applications || []))
      .catch((err) =>
        setError(
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudieron cargar tus postulaciones.",
        ),
      )
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Postulaciones</h1>
      <p className="text-slate-600 mb-6">Pipeline real de aplicaciones guardadas por tu cuenta.</p>
      {error ? <div className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-amber-800">{error}</div> : null}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Puesto</th>
              <th className="px-4 py-3 font-medium">Empresa</th>
              <th className="px-4 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 font-medium">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {applications.map((app) => (
              <tr key={app.id}>
                <td className="px-4 py-3 text-slate-900">{app.job_title}</td>
                <td className="px-4 py-3 text-slate-600">{app.company}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700">
                    {app.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">{app.applied_at || "-"}</td>
              </tr>
            ))}
            {applications.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  Todavía no registraste postulaciones.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  )
}
