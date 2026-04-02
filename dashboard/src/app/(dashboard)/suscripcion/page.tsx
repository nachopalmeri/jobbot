"use client"

import { useEffect, useMemo, useState } from "react"
import { Bitcoin, Check, CreditCard, Wallet } from "lucide-react"

import { apiRequest } from "@/lib/api"

const providers = [
  { name: "Stripe", icon: CreditCard, color: "bg-purple-600" },
  { name: "MercadoPago", icon: Wallet, color: "bg-blue-600" },
  { name: "Crypto", icon: Bitcoin, color: "bg-orange-500" },
]

export default function SuscripcionPage() {
  const [plans, setPlans] = useState<any[]>([])
  const [currentPlan, setCurrentPlan] = useState("free")
  const [selectedPlan, setSelectedPlan] = useState("pro")
  const [message, setMessage] = useState("")

  useEffect(() => {
    const load = async () => {
      try {
        const [plansData, statusData] = await Promise.all([
          apiRequest<{ plans: any[] }>("/subscriptions/plans", {}, true),
          apiRequest<{ plan: string }>("/subscriptions/status", {}, true),
        ])
        setPlans(plansData.plans || [])
        setCurrentPlan(statusData.plan || "free")
      } catch (err) {
        setMessage(
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudieron cargar los planes.",
        )
      }
    }

    void load()
  }, [])

  const paidPlans = useMemo(() => plans.filter((plan) => plan.id !== "free"), [plans])

  const handleUpgrade = async (provider: string) => {
    try {
      setMessage("")
      const data = await apiRequest<{ url?: string; detail?: string }>("/subscriptions/create-checkout", {
        method: "POST",
        body: JSON.stringify({ provider, plan: selectedPlan }),
      }, true)

      if (data.url) {
        window.location.href = data.url
      } else {
        setMessage(data.detail || "No se pudo iniciar el checkout.")
      }
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "Error al procesar el pago.",
      )
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Tu Suscripción</h1>
      <p className="text-slate-600 mb-8">Planes y límites alineados con el backend y el bot.</p>
      {message ? <div className="mb-6 rounded-lg bg-slate-100 px-4 py-3 text-slate-700">{message}</div> : null}
      
      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        {plans.map((plan) => (
          <div key={plan.name} className={`bg-white rounded-2xl p-8 border-2 ${
            plan.id === selectedPlan ? "border-purple-500 relative" : "border-slate-200"
          }`}>
            {plan.id === "pro" && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-sm px-3 py-1 rounded-full">
                Más popular
              </span>
            )}
            <h3 className="text-xl font-bold text-slate-900">{plan.name}</h3>
            <div className="mt-4">
              <span className="text-4xl font-bold">${plan.price}</span>
              <span className="text-slate-500">/mes</span>
            </div>
            <ul className="mt-6 space-y-3">
              {plan.features.map((feature: string) => (
                <li key={feature} className="flex items-center gap-2 text-slate-700">
                  <Check className="text-green-500" size={18} />
                  {feature}
                </li>
              ))}
            </ul>
            <button
              onClick={() => setSelectedPlan(plan.id)}
              className={`w-full mt-8 py-3 rounded-lg font-semibold ${
                plan.id === currentPlan
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-purple-600 text-white hover:bg-purple-700"
              }`}
              disabled={plan.id === currentPlan || plan.id === "free"}
            >
              {plan.id === currentPlan ? "Plan actual" : plan.id === "free" ? "Incluido" : "Seleccionar"}
            </button>
          </div>
        ))}
      </div>
      
      <div className="bg-white rounded-xl p-6 border border-slate-200">
        <h3 className="text-lg font-semibold mb-4">Métodos de pago disponibles</h3>
        <p className="mb-4 text-sm text-slate-500">
          Estás por activar el plan <strong>{selectedPlan.toUpperCase()}</strong>.
        </p>
        <div className="flex flex-wrap gap-4">
          {providers.map((p) => (
            <button 
              key={p.name}
              onClick={() => handleUpgrade(p.name.toLowerCase())}
              disabled={!paidPlans.some((plan) => plan.id === selectedPlan)}
              className={`${p.color} text-white px-6 py-3 rounded-lg flex items-center gap-2 hover:opacity-90 transition-opacity`}
            >
              <p.icon size={20} />
              {p.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
