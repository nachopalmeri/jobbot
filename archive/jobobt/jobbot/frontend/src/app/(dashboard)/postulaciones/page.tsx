"use client"

import { useState } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { 
  Search, Filter, Plus, MoreHorizontal, Calendar, 
  MessageSquare, CheckCircle, XCircle, Clock, Trash2, Edit, Eye
} from "lucide-react"

const applications = [
  {
    id: 1,
    title: "Frontend Developer",
    company: "TechFlow Argentina",
    appliedDate: "2026-03-27",
    status: "interview",
    salary: "$2.200",
    notes: "Tech lead muy copado, la práctica fue bien",
    nextAction: "Entrevista",
    nextActionDate: "2026-03-28"
  },
  {
    id: 2,
    title: "Full Stack Engineer",
    company: "DataViz Labs",
    appliedDate: "2026-03-26",
    status: "applied",
    salary: "$2.500",
    notes: "",
    nextAction: "Seguimiento",
    nextActionDate: "2026-03-29"
  },
  {
    id: 3,
    title: "Backend Developer",
    company: "CloudNet SA",
    appliedDate: "2026-03-24",
    status: "rejected",
    salary: "$2.800",
    notes: "Buscaban más seniority",
    nextAction: null,
    nextActionDate: null
  },
  {
    id: 4,
    title: "Product Manager",
    company: "Innovate Corp",
    appliedDate: "2026-03-20",
    status: "offer",
    salary: "$2.200",
    notes: "¡Oferta aceptada!",
    nextAction: "Responder",
    nextActionDate: "2026-03-25"
  },
  {
    id: 5,
    title: "UI/UX Designer",
    company: "Creative Studio BA",
    appliedDate: "2026-03-22",
    status: "interview",
    salary: "$1.800",
    notes: "Portfolio visto, buen feeling",
    nextAction: "Entrevista",
    nextActionDate: "2026-03-30"
  },
]

const statusConfig = {
  applied: { label: "Aplicado", color: "bg-blue-100 text-blue-700", icon: Clock },
  interview: { label: "Entrevista", color: "bg-amber-100 text-amber-700", icon: MessageSquare },
  offer: { label: "Oferta", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle },
  rejected: { label: "No avanzado", color: "bg-zinc-100 text-zinc-500", icon: XCircle },
}

const stats = [
  { label: "Total aplicadas", value: "12", color: "bg-blue-500" },
  { label: "En entrevista", value: "3", color: "bg-amber-500" },
  { label: "Ofertas recibidas", value: "1", color: "bg-emerald-500" },
  { label: "Tasa de éxito", value: "25%", color: "bg-purple-500" },
]

export default function PostulacionesPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  const filteredApps = applications.filter(app => {
    const matchesSearch = app.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         app.company.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === "all" || app.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-zinc-900">Mis Postulaciones</h1>
          <p className="text-zinc-500">Seguimiento de tu pipeline de empleo</p>
        </div>
        <Button>
          <Plus size={18} className="mr-2" />
          Nueva postulación
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, i) => (
          <Card key={i} className="border-zinc-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${stat.color} flex items-center justify-center`}>
                  <span className="text-white font-semibold">{stat.value[0]}</span>
                </div>
                <div>
                  <p className="text-sm text-zinc-500">{stat.label}</p>
                  <p className="text-xl font-semibold text-zinc-900">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
          <Input 
            placeholder="Buscar postulaciones..." 
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <select 
          className="px-4 py-2 border border-zinc-200 rounded-lg text-sm bg-white"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">Todos los estados</option>
          <option value="applied">Aplicados</option>
          <option value="interview">En entrevista</option>
          <option value="offer">Con oferta</option>
          <option value="rejected">No avanzado</option>
        </select>
      </div>

      {/* Kanban View (Simple) */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {Object.entries(statusConfig).map(([status, config]) => {
          const apps = applications.filter(a => a.status === status)
          return (
            <div key={status} className="bg-zinc-50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <config.icon size={16} className={config.color.replace("bg-", "text-").split(" ")[1]} />
                  <span className="font-medium text-sm">{config.label}</span>
                </div>
                <Badge variant="secondary" className="bg-white">{apps.length}</Badge>
              </div>
              <div className="space-y-2">
                {apps.slice(0, 3).map(app => (
                  <div key={app.id} className="bg-white rounded-lg p-3 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                    <p className="font-medium text-sm text-zinc-900">{app.title}</p>
                    <p className="text-xs text-zinc-500">{app.company}</p>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Table View */}
      <Card className="border-zinc-100">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-zinc-50 border-b border-zinc-100">
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Empresa</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Puesto</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Fecha</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Estado</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Salario</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Notas</th>
                <th className="text-left p-4 text-sm font-medium text-zinc-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredApps.map(app => {
                const status = statusConfig[app.status as keyof typeof statusConfig]
                return (
                  <tr key={app.id} className="border-b border-zinc-50 hover:bg-zinc-50">
                    <td className="p-4">
                      <p className="font-medium text-zinc-900">{app.company}</p>
                    </td>
                    <td className="p-4">
                      <p className="text-zinc-600">{app.title}</p>
                    </td>
                    <td className="p-4">
                      <p className="text-sm text-zinc-500">{new Date(app.appliedDate).toLocaleDateString("es-AR")}</p>
                    </td>
                    <td className="p-4">
                      <Badge className={status.color}>
                        <status.icon size={12} className="mr-1" />
                        {status.label}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <p className="text-sm text-zinc-600">{app.salary}</p>
                    </td>
                    <td className="p-4">
                      <p className="text-sm text-zinc-500 max-w-[150px] truncate">
                        {app.notes || "-"}
                      </p>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Eye size={16} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Edit size={16} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500">
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Empty State */}
      {filteredApps.length === 0 && (
        <div className="text-center py-12">
          <p className="text-zinc-500 mb-4">No hay postulaciones que coincidan con tu búsqueda</p>
          <Button>
            <Plus size={18} className="mr-2" />
            Agregar postulación
          </Button>
        </div>
      )}
    </div>
  )
}
