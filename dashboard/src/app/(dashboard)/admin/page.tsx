"use client"

import { useEffect, useState } from "react"
import { 
  Users, 
  DollarSign, 
  CreditCard, 
  TrendingUp, 
  Crown,
  AlertCircle,
  Loader2,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react"
import { apiRequest } from "@/lib/api"
import Link from "next/link"

interface AdminMetrics {
  users: {
    telegram_total: number
    web_total: number
    active_today: number
    new_this_week: number
  }
  revenue: {
    total_usd: number
    monthly_usd: number
  }
  plans: Array<{
    plan: string
    count: number
  }>
  credits: {
    total_sold: number
    remaining: number
    consumed: number
  }
  recent_payments: Array<{
    id: number
    email: string
    amount: number
    currency: string
    provider: string
    status: string
    created_at: string
  }>
}

export default function AdminPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [isAdmin, setIsAdmin] = useState(false)
  const [userEmail, setUserEmail] = useState("")

  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const user = await apiRequest<{ email: string; is_admin: boolean }>("/auth/me", {}, true)
        setUserEmail(user.email)
        
        if (!user.is_admin) {
          setIsAdmin(false)
          setLoading(false)
          return
        }
        
        setIsAdmin(true)
        
        // Cargar métricas
        const data = await apiRequest<AdminMetrics>("/admin/metrics", {}, true)
        setMetrics(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error cargando datos")
      } finally {
        setLoading(false)
      }
    }

    checkAdmin()
  }, [])

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (!isAdmin) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center p-6">
        <div className="rounded-full bg-red-100 p-4">
          <AlertCircle className="h-8 w-8 text-red-600" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-stone-900">Acceso Restringido</h1>
        <p className="mt-2 text-center text-stone-600">
          Solo los administradores pueden acceder a esta sección.
        </p>
        <p className="mt-1 text-sm text-stone-500">
          Tu email: {userEmail}
        </p>
        <Link
          href="/dashboard"
          className="mt-6 rounded-2xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Volver al Dashboard
        </Link>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center p-6">
        <div className="rounded-full bg-amber-100 p-4">
          <AlertCircle className="h-8 w-8 text-amber-600" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-stone-900">Error cargando datos</h1>
        <p className="mt-2 text-stone-600">{error}</p>
      </div>
    )
  }

  if (!metrics) return null

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-indigo-100 p-3">
            <Crown className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-stone-900">Panel de Administración</h1>
            <p className="text-sm text-stone-600">Métricas de billing y usuarios</p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {/* Revenue Total */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-stone-600">Revenue Total</p>
              <p className="mt-2 text-3xl font-bold text-stone-900">
                ${metrics.revenue.total_usd.toFixed(2)}
              </p>
            </div>
            <div className="rounded-full bg-green-100 p-3">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        {/* Revenue Mensual */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-stone-600">Revenue 30 días</p>
              <p className="mt-2 text-3xl font-bold text-stone-900">
                ${metrics.revenue.monthly_usd.toFixed(2)}
              </p>
            </div>
            <div className="rounded-full bg-indigo-100 p-3">
              <TrendingUp className="h-6 w-6 text-indigo-600" />
            </div>
          </div>
        </div>

        {/* Usuarios Web */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-stone-600">Usuarios Web</p>
              <p className="mt-2 text-3xl font-bold text-stone-900">
                {metrics.users.web_total}
              </p>
              <p className="text-xs text-stone-500">
                +{metrics.users.new_this_week} esta semana
              </p>
            </div>
            <div className="rounded-full bg-blue-100 p-3">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        {/* Créditos Vendidos */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-stone-600">Créditos Vendidos</p>
              <p className="mt-2 text-3xl font-bold text-stone-900">
                {metrics.credits.total_sold}
              </p>
              <p className="text-xs text-stone-500">
                {metrics.credits.remaining} sin usar
              </p>
            </div>
            <div className="rounded-full bg-amber-100 p-3">
              <CreditCard className="h-6 w-6 text-amber-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Distribución de Planes */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-stone-900 mb-4">Distribución de Planes</h2>
          <div className="space-y-3">
            {metrics.plans.map((plan) => (
              <div key={plan.plan} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-3 w-3 rounded-full ${
                    plan.plan === "free" ? "bg-stone-400" :
                    plan.plan === "starter" ? "bg-blue-500" :
                    plan.plan === "pro" ? "bg-indigo-500" :
                    plan.plan === "premium" ? "bg-amber-500" :
                    "bg-stone-400"
                  }`} />
                  <span className="text-sm font-medium text-stone-700 capitalize">
                    {plan.plan}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="h-2 w-32 rounded-full bg-stone-100 overflow-hidden">
                    <div 
                      className="h-full rounded-full bg-indigo-500"
                      style={{ 
                        width: `${(plan.count / metrics.users.web_total) * 100}%`,
                        backgroundColor: plan.plan === "free" ? "#78716c" :
                                        plan.plan === "starter" ? "#3b82f6" :
                                        plan.plan === "pro" ? "#6366f1" :
                                        plan.plan === "premium" ? "#f59e0b" : "#78716c"
                      }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-stone-900 w-8">
                    {plan.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Usuarios Activos */}
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-stone-900 mb-4">Actividad Reciente</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-stone-50 p-4 text-center">
              <p className="text-3xl font-bold text-stone-900">{metrics.users.active_today}</p>
              <p className="text-sm text-stone-600">Activos hoy</p>
            </div>
            <div className="rounded-xl bg-stone-50 p-4 text-center">
              <p className="text-3xl font-bold text-stone-900">{metrics.users.telegram_total}</p>
              <p className="text-sm text-stone-600">Usuarios Telegram</p>
            </div>
            <div className="rounded-xl bg-stone-50 p-4 text-center">
              <p className="text-3xl font-bold text-stone-900">{metrics.credits.consumed}</p>
              <p className="text-sm text-stone-600">Créditos Usados</p>
            </div>
            <div className="rounded-xl bg-stone-50 p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{Math.round((metrics.credits.consumed / (metrics.credits.total_sold || 1)) * 100)}%</p>
              <p className="text-sm text-stone-600">Tasa de Uso</p>
            </div>
          </div>
        </div>
      </div>

      {/* Últimos Pagos */}
      <div className="mt-8 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-stone-900 mb-4">Últimos Pagos</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-stone-200">
                <th className="pb-3 text-left text-sm font-semibold text-stone-600">Email</th>
                <th className="pb-3 text-left text-sm font-semibold text-stone-600">Monto</th>
                <th className="pb-3 text-left text-sm font-semibold text-stone-600">Provider</th>
                <th className="pb-3 text-left text-sm font-semibold text-stone-600">Estado</th>
                <th className="pb-3 text-left text-sm font-semibold text-stone-600">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {metrics.recent_payments.map((payment) => (
                <tr key={payment.id}>
                  <td className="py-3 text-sm text-stone-900">{payment.email}</td>
                  <td className="py-3 text-sm font-semibold text-stone-900">
                    ${payment.amount.toFixed(2)} {payment.currency}
                  </td>
                  <td className="py-3 text-sm text-stone-600 capitalize">{payment.provider}</td>
                  <td className="py-3">
                    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                      payment.status === "completed" 
                        ? "bg-green-100 text-green-700" 
                        : payment.status === "pending"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {payment.status}
                    </span>
                  </td>
                  <td className="py-3 text-sm text-stone-500">
                    {new Date(payment.created_at).toLocaleDateString("es-AR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
