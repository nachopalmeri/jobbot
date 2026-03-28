"use client"

import { Check, CreditCard, Wallet, Bitcoin } from "lucide-react"

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "para siempre",
    features: [
      "3 alertas por semana",
      "5 búsquedas diarias",
      "2 análisis de CV/mes",
      "Dashboard básico",
    ],
    notFeatures: [
      "Match con ofertas",
      "Job Tracker",
      "Export PDF",
    ],
    cta: "Plan actual",
    current: true,
  },
  {
    name: "Premium",
    price: "$5",
    period: "por mes",
    features: [
      "Alertas ilimitadas",
      "Búsquedas ilimitadas",
      "Análisis de CV ilimitados",
      "Match con ofertas",
      "Job Tracker",
      "Export PDF",
      "Soporte prioritario",
    ],
    notFeatures: [],
    cta: "Actualizar",
    popular: true,
  },
]

const providers = [
  { name: "Stripe", icon: CreditCard, color: "bg-purple-600" },
  { name: "MercadoPago", icon: Wallet, color: "bg-blue-600" },
  { name: "Crypto", icon: Bitcoin, color: "bg-orange-500" },
]

export default function SuscripcionPage() {
  const handleUpgrade = async (provider: string) => {
    try {
      const token = localStorage.getItem("token")
      const res = await fetch("http://localhost:8000/subscriptions/create-checkout-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ provider }),
      })
      
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      }
    } catch (error) {
      alert("Error al procesar pago")
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Tu Suscripción</h1>
      <p className="text-slate-600 mb-8">Elige el plan que mejor se adapte a tus necesidades</p>
      
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {plans.map((plan) => (
          <div key={plan.name} className={`bg-white rounded-2xl p-8 border-2 ${
            plan.popular ? "border-purple-500 relative" : "border-slate-200"
          }`}>
            {plan.popular && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-white text-sm px-3 py-1 rounded-full">
                Más popular
              </span>
            )}
            <h3 className="text-xl font-bold text-slate-900">{plan.name}</h3>
            <div className="mt-4">
              <span className="text-4xl font-bold">{plan.price}</span>
              <span className="text-slate-500">/{plan.period}</span>
            </div>
            <ul className="mt-6 space-y-3">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center gap-2 text-slate-700">
                  <Check className="text-green-500" size={18} />
                  {feature}
                </li>
              ))}
              {plan.notFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-2 text-slate-400">
                  <span className="w-[18px]" />
                  {feature}
                </li>
              ))}
            </ul>
            <button className={`w-full mt-8 py-3 rounded-lg font-semibold ${
              plan.current 
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-purple-600 text-white hover:bg-purple-700"
            }`}>
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
      
      <div className="bg-white rounded-xl p-6 border border-slate-200">
        <h3 className="text-lg font-semibold mb-4">Métodos de pago disponibles</h3>
        <div className="flex flex-wrap gap-4">
          {providers.map((p) => (
            <button 
              key={p.name}
              onClick={() => handleUpgrade(p.name.toLowerCase())}
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
