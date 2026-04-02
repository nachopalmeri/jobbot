"use client"

import { useEffect, useState } from "react"
import { Sparkles, Zap, Crown, Check, CreditCard } from "lucide-react"

import { apiRequest } from "@/lib/api"

interface CreditPack {
  id: string
  name: string
  description: string
  credits: number
  price_usd: number
  is_unlock: boolean
  highlight?: boolean
  unit_price: number
}

interface CreditBalance {
  total_credits: number
  unlock_active: boolean
  active_packs: Array<{
    id: number
    pack_type: string
    credits_remaining: number
    purchase_price: number
  }>
}

export default function CreditosPage() {
  const [packs, setPacks] = useState<CreditPack[]>([])
  const [balance, setBalance] = useState<CreditBalance | null>(null)
  const [loading, setLoading] = useState(true)
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null)
  const [message, setMessage] = useState("")

  useEffect(() => {
    const load = async () => {
      const [packsResult, balanceResult] = await Promise.allSettled([
        apiRequest<{ packs: CreditPack[] }>("/credits/packs", {}, true),
        apiRequest<CreditBalance>("/credits/balance", {}, true),
      ])

      if (packsResult.status === "fulfilled") {
        setPacks(packsResult.value.packs || [])
      } else {
        const error = packsResult.reason
        setMessage(
          error && typeof error === "object" && "message" in error
            ? String(error.message)
            : "No se pudieron cargar los packs de creditos.",
        )
      }

      if (balanceResult.status === "fulfilled") {
        setBalance(balanceResult.value)
      } else {
        setBalance({
          total_credits: 0,
          unlock_active: false,
          active_packs: [],
        })
        setMessage((current) =>
          current || "No pudimos leer tu balance actual, pero igual podes ver los packs disponibles.",
        )
      }

      setLoading(false)
    }

    void load()
  }, [])

  const handlePurchase = async (packType: string) => {
    try {
      setCheckoutLoading(packType)
      setMessage("")
      
      const data = await apiRequest<{
        checkout_url?: string
        session_id?: string
        detail?: string
      }>("/credits/checkout", {
        method: "POST",
        body: JSON.stringify({
          pack_type: packType,
          success_url: `${window.location.origin}/dashboard/creditos?success=true`,
          cancel_url: `${window.location.origin}/dashboard/creditos`,
        }),
      }, true)

      if (data.checkout_url) {
        window.location.assign(data.checkout_url)
      } else {
        setMessage(data.detail || "No se pudo iniciar el checkout.")
      }
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "Error al procesar el pago.",
      )
    } finally {
      setCheckoutLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Cargando...</div>
      </div>
    )
  }

  const unlockPack = packs.find((p) => p.is_unlock)
  const creditPacks = packs.filter((p) => !p.is_unlock)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">⭐ Créditos & CV Suite</h1>
      <p className="text-slate-600 mb-6">
        Pagá una vez, usá para siempre. Los créditos nunca expiran.
      </p>

      {message && (
        <div className={`mb-6 rounded-lg px-4 py-3 ${message.includes("éxito") ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-700"}`}>
          {message}
        </div>
      )}

      {/* Balance actual */}
      {balance && (
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="text-yellow-300" size={24} />
            <span className="text-lg font-semibold">Tu Balance</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold">{balance.total_credits}</span>
            <span className="text-purple-100">créditos disponibles</span>
          </div>
          {balance.unlock_active && (
            <div className="mt-3 flex items-center gap-2 text-sm bg-white/20 rounded-lg px-3 py-2 w-fit">
              <Crown size={16} className="text-yellow-300" />
              <span>CV Suite Desbloqueado - Acceso ilimitado a herramientas</span>
            </div>
          )}
        </div>
      )}

      {/* Unlock CV Suite */}
      {unlockPack && !balance?.unlock_active && (
        <div className="mb-10">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">🔓 Desbloqueá CV Suite</h2>
          <div className="bg-white rounded-2xl p-8 border-2 border-purple-500 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-gradient-to-bl from-purple-100 to-transparent w-64 h-64 rounded-bl-full opacity-50" />
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <Crown className="text-purple-600" size={32} />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-900">{unlockPack.name}</h3>
                  <p className="text-slate-600">{unlockPack.description}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-4 mb-6">
                {[
                  "Lifetime access a herramientas CV",
                  "50 créditos IA incluidos",
                  "Historial ilimitado de scans",
                  "Sin anuncios",
                  "Sin suscripción mensual",
                ].map((feature) => (
                  <div key={feature} className="flex items-center gap-2 text-slate-700">
                    <Check className="text-green-500" size={18} />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-4xl font-bold text-purple-600">${unlockPack.price_usd}</span>
                <span className="text-slate-500">USD · pago único</span>
              </div>

              <button
                onClick={() => handlePurchase(unlockPack.id)}
                disabled={checkoutLoading === unlockPack.id}
                className="bg-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                <CreditCard size={20} />
                {checkoutLoading === unlockPack.id ? "Procesando..." : "Desbloquear Ahora"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Credit Packs */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-slate-900 mb-4">➕ Comprar Más Créditos</h2>
        <p className="text-slate-600 mb-6 text-sm">
          1 crédito = 1 análisis IA con feedback personalizado o 1 carta de presentación generada.
          Los créditos nunca expiran.
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {creditPacks.map((pack) => (
            <div
              key={pack.id}
              className={`bg-white rounded-2xl p-6 border-2 ${
                pack.highlight ? "border-pink-400 shadow-lg" : "border-slate-200"
              }`}
            >
              {pack.highlight && (
                <span className="inline-block bg-pink-100 text-pink-700 text-xs font-semibold px-3 py-1 rounded-full mb-3">
                  BEST VALUE
                </span>
              )}

              <div className="flex items-center gap-2 mb-3">
                <div className={`p-2 rounded-lg ${pack.highlight ? "bg-pink-100" : "bg-slate-100"}`}>
                  <Zap size={20} className={pack.highlight ? "text-pink-600" : "text-slate-600"} />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">{pack.name}</h3>
              </div>

              <p className="text-slate-600 text-sm mb-4">{pack.description}</p>

              <div className="mb-4">
                <span className="text-3xl font-bold text-slate-900">${pack.price_usd}</span>
                <span className="text-slate-500 text-sm ml-1">USD</span>
              </div>

              <div className="text-sm text-slate-500 mb-4">
                ${pack.unit_price} por crédito
              </div>

              <button
                onClick={() => handlePurchase(pack.id)}
                disabled={checkoutLoading === pack.id}
                className={`w-full py-3 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 ${
                  pack.highlight
                    ? "bg-pink-600 text-white hover:bg-pink-700"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                <CreditCard size={18} />
                {checkoutLoading === pack.id ? "Procesando..." : "Comprar"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Info */}
      <div className="bg-slate-50 rounded-xl p-6 mt-8">
        <h3 className="font-semibold text-slate-900 mb-3">💡 ¿Qué son los créditos?</h3>
        <ul className="space-y-2 text-sm text-slate-600">
          <li>• <strong>1 crédito</strong> = 1 análisis IA de tu CV vs una oferta laboral</li>
          <li>• <strong>1 crédito</strong> = 1 carta de presentación generada con IA</li>
          <li>• Los créditos <strong>nunca expiran</strong> - usalos cuando quieras</li>
          <li>• El <strong>CV Suite Unlock</strong> incluye 50 créditos + acceso lifetime</li>
          <li>• Los análisis básicos ATS son <strong>gratis siempre</strong></li>
        </ul>
      </div>
    </div>
  )
}
