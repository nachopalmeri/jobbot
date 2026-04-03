"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

import PublicFooterLinks from "@/components/PublicFooterLinks"
import { apiRequest, setToken } from "@/lib/api"

interface RegisterResponse {
  access_token: string
  is_temp_account?: boolean
}

export default function RegisterPage() {
  const router = useRouter()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [telegramId, setTelegramId] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")
    
    try {
      const trimmedTelegramId = telegramId.trim()
      const data = await apiRequest<RegisterResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          telegram_id: trimmedTelegramId ? parseInt(trimmedTelegramId, 10) : null,
          name: name || "Usuario",
        }),
      })

      setToken(data.access_token)
      router.replace(
        data.is_temp_account ?? !trimmedTelegramId
          ? "/dashboard/configuracion?linkTelegram=1"
          : "/dashboard",
      )
    } catch (error) {
      const detail =
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "Error de conexión"
      setMessage(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.22),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(251,191,36,0.18),_transparent_26%),linear-gradient(180deg,_#18181b,_#0f172a_42%,_#111827)] px-4 py-12 text-white">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1fr_1fr]">
        <section className="rounded-[2rem] border border-white/10 bg-white/6 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-300">
            Alta inicial
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">
            Entrá rápido y vinculá Telegram cuando quieras
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-white/72">
            Podés empezar solo con email y password o sumar tu ID de Telegram desde el primer día
            para recibir alertas, códigos de acceso y automatizaciones.
          </p>

          <div className="mt-8 space-y-4">
            {[
              "Cuenta web lista para usar en menos de un minuto.",
              "Pipeline, CV Suite y búsquedas guiadas desde el dashboard.",
              "Telegram opcional para alertas, login asistido y comandos del bot.",
            ].map((item) => (
              <div key={item} className="rounded-[1.5rem] border border-white/10 bg-black/15 p-4 text-sm text-white/74">
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-white/6 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-300">
            Crear cuenta
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight">Abrí tu espacio en JobBot</h2>
          <p className="mt-3 text-sm leading-7 text-white/68">
            Después podés completar preferencias, objetivo semanal, Pomodoro y pipeline.
          </p>

          {message ? (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/8 px-4 py-3 text-sm text-white/90">
              {message}
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <input
              type="text"
              placeholder="Tu nombre"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
            />
            <input
              type="text"
              placeholder="ID de Telegram opcional"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
            />
            <p className="px-1 text-xs leading-6 text-white/58">
              Si lo completás ahora, la cuenta queda lista para alertas y automatizaciones del bot.
            </p>
            <input
              type="email"
              placeholder="tu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
              required
            />
            <input
              type="password"
              placeholder="Elegí una password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-gradient-to-r from-indigo-500 via-sky-500 to-amber-400 px-4 py-3 font-semibold text-slate-950 transition hover:opacity-95 disabled:opacity-60"
            >
              {loading ? "Creando cuenta..." : "Crear cuenta"}
            </button>
          </form>

          <p className="mt-5 text-sm text-white/62">
            ¿Ya tenés cuenta?
            <Link href="/login" className="ml-2 font-semibold text-amber-300 hover:text-amber-200">
              Entrar
            </Link>
          </p>

          <PublicFooterLinks />
        </section>
      </div>
    </div>
  )
}
