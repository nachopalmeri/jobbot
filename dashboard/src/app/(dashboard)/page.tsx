"use client"

import { Search, FileText, TrendingUp, Bell } from "lucide-react"

const stats = [
  { title: "Empleos encontrados", value: "24", change: "+5 esta semana", icon: Search, trend: "up" },
  { title: "Postulaciones", value: "12", change: "3 en proceso", icon: FileText, trend: "up" },
  { title: "Tasa de respuesta", value: "18%", change: "+2% vs mes anterior", icon: TrendingUp, trend: "up" },
  { title: "Alertas activas", value: "3", change: "Próxima en 2h", icon: Bell, trend: "neutral" },
]

export default function DashboardPage() {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">¡Bienvenido de nuevo!</h1>
        <p className="text-slate-600">Estas son las estadísticas de tu búsqueda de empleo</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
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
                <stat.icon className="text-purple-600" size={24} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl p-6 border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Últimos empleos recomendados</h2>
        <div className="space-y-4">
          {[
            { title: "Python Developer", company: "TechCorp", location: "Remote", modality: "remote" },
            { title: "Backend Engineer", company: "StartupXYZ", location: "Buenos Aires", modality: "hybrid" },
            { title: "Junior Developer", company: "DevStudio", location: "CABA", modality: "onsite" },
          ].map((job, i) => (
            <div key={i} className="flex justify-between items-center p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer">
              <div>
                <h3 className="font-medium text-slate-900">{job.title}</h3>
                <p className="text-sm text-slate-600">{job.company} • {job.location}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                job.modality === "remote" ? "bg-green-100 text-green-700" :
                job.modality === "hybrid" ? "bg-amber-100 text-amber-700" :
                "bg-slate-100 text-slate-700"
              }`}>
                {job.modality}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
