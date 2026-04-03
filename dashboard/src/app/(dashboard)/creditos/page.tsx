"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Sparkles, Zap, Crown, Check, CreditCard, ArrowRight } from "lucide-react"

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
      <div className="flex min-h-[400px] items-center justify-center p-6">
        <div className="text-stone-500">Cargando...</div>
      </div>
    )
  }

  const unlockPack = packs.find((p) => p.is_unlock)
  const creditPacks = packs.filter((p) => !p.is_unlock)

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
          Créditos & CV Suite
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
          Pagá por uso cuando no necesitás otra suscripción mensual.
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600">
          Si querés usar la capa de CV con más flexibilidad, podés desbloquear la suite y comprar
          créditos solo para las partes avanzadas con IA. Los créditos no expiran.
        </p>
      </section>

      {message && (
        <div className={`rounded-2xl px-4 py-3 ${message.includes("éxito") ? "bg-emerald-100 text-emerald-700" : "bg-stone-100 text-stone-700"}`}>
          {message}
        </div>
      )}

      {balance && (
        <section className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(135deg,_rgba(79,70,229,0.9),_rgba(67,56,202,0.95))] p-6 text-white shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="text-amber-200" size={24} />
            <span className="text-lg font-semibold">Tu Balance</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-bold">{balance.total_credits}</span>
            <span className="text-indigo-100">créditos disponibles</span>
          </div>
          {balance.unlock_active && (
            <div className="mt-3 flex w-fit items-center gap-2 rounded-lg bg-white/15 px-3 py-2 text-sm">
              <Crown size={16} className="text-amber-200" />
              <span>CV Suite desbloqueada. Historial y capa base activos; IA avanzada según cuota o créditos.</span>
            </div>
          )}
        </section>
      )}

      {unlockPack && !balance?.unlock_active && (
        <section className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
              Unlock one-time
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-950">Desbloqueá CV Suite</h2>
          </div>
          <div className="relative overflow-hidden rounded-[2rem] border border-indigo-200 bg-white p-8 shadow-sm">
            <div className="absolute right-0 top-0 h-64 w-64 rounded-bl-full bg-gradient-to-bl from-indigo-100 to-transparent opacity-60" />
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4">
                <div className="rounded-xl bg-indigo-100 p-3">
                  <Crown className="text-indigo-600" size={32} />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-stone-900">{unlockPack.name}</h3>
                  <p className="text-stone-600">{unlockPack.description}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-4 mb-6">
                {[
                  "Acceso permanente a la capa base de CV Suite",
                  "50 créditos IA incluidos",
                  "Historial y análisis guardados",
                  "Sin anuncios",
                  "Sin suscripción mensual",
                ].map((feature) => (
                  <div key={feature} className="flex items-center gap-2 text-stone-700">
                    <Check className="text-green-500" size={18} />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="flex items-baseline gap-2 mb-6">
                <span className="text-4xl font-bold text-indigo-600">${unlockPack.price_usd}</span>
                <span className="text-stone-500">USD · pago único</span>
              </div>

              <p className="mb-6 max-w-2xl text-sm leading-6 text-stone-600">
                Ideal si querés usar Resume Score, ATS Checker, Job Match e historial sin subir de
                plan todavía. Después podés sumar créditos extra solo cuando lo necesites.
              </p>

              <button
                onClick={() => handlePurchase(unlockPack.id)}
                disabled={checkoutLoading === unlockPack.id}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-4 font-semibold text-white transition-colors hover:bg-indigo-700"
              >
                <CreditCard size={20} />
                {checkoutLoading === unlockPack.id ? "Procesando..." : "Desbloquear ahora"}
              </button>
            </div>
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-4 text-2xl font-semibold text-stone-900">Comprar más créditos</h2>
        <p className="mb-6 text-sm text-stone-600">
          1 crédito = 1 análisis IA con feedback personalizado o 1 carta de presentación generada.
          Los créditos nunca expiran.
        </p>

        <div className="grid md:grid-cols-3 gap-6">
          {creditPacks.map((pack) => (
            <div
              key={pack.id}
              className={`rounded-[1.75rem] bg-white p-6 border ${
                pack.highlight ? "border-amber-300 shadow-lg" : "border-stone-200"
              }`}
            >
              {pack.highlight && (
                <span className="mb-3 inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                  Mejor valor
                </span>
              )}

              <div className="flex items-center gap-2 mb-3">
                <div className={`rounded-lg p-2 ${pack.highlight ? "bg-amber-100" : "bg-stone-100"}`}>
                  <Zap size={20} className={pack.highlight ? "text-amber-600" : "text-stone-600"} />
                </div>
                <h3 className="text-lg font-semibold text-stone-900">{pack.name}</h3>
              </div>

              <p className="mb-4 text-sm text-stone-600">{pack.description}</p>

              <div className="mb-4">
                <span className="text-3xl font-bold text-stone-900">${pack.price_usd}</span>
                <span className="ml-1 text-sm text-stone-500">USD</span>
              </div>

              <div className="mb-4 text-sm text-stone-500">
                ${pack.unit_price} por crédito
              </div>

              <button
                onClick={() => handlePurchase(pack.id)}
                disabled={checkoutLoading === pack.id}
                className={`flex w-full items-center justify-center gap-2 rounded-xl py-3 font-semibold transition-colors ${
                  pack.highlight
                    ? "bg-stone-950 text-white hover:bg-stone-800"
                    : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              >
                <CreditCard size={18} />
                {checkoutLoading === pack.id ? "Procesando..." : "Comprar"}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-stone-200 bg-stone-50 p-6">
        <h3 className="mb-3 font-semibold text-stone-900">Cómo encaja esto con los planes</h3>
        <ul className="space-y-2 text-sm text-stone-600">
          <li>• <strong>1 crédito</strong> = 1 análisis IA de tu CV vs una oferta laboral</li>
          <li>• <strong>1 crédito</strong> = 1 carta de presentación generada con IA</li>
          <li>• Los créditos <strong>nunca expiran</strong> - usalos cuando quieras</li>
          <li>• El <strong>CV Suite Unlock</strong> incluye 50 créditos + acceso permanente a la suite base</li>
          <li>• Los análisis básicos ATS son <strong>gratis siempre</strong></li>
        </ul>
        <p className="mt-4 text-sm text-stone-600">
          Si querés búsquedas, tracker y alertas todos los días, te conviene una suscripción.
          Si lo tuyo es CV Suite y uso puntual de IA, los créditos son la vía más flexible.
        </p>
        <Link
          href="/dashboard/suscripcion"
          className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700"
        >
          Comparar contra los planes
          <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  )
}
