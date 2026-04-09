"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"

import PublicFooterLinks from "@/components/PublicFooterLinks"
import { apiRequest, setToken } from "@/lib/api"

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const code = useMemo(() => searchParams.get("code")?.trim().toUpperCase() || "", [searchParams])
  const nextPath = searchParams.get("next") || "/dashboard"

  useEffect(() => {
    if (!code) {
      return
    }

    const loginWithTelegramCode = async () => {
      try {
        setLoading(true)
        setMessage("Validando tu código de Telegram...")
        const data = await apiRequest<{ access_token: string }>("/auth/telegram/code", {
          method: "POST",
          body: JSON.stringify({ code }),
        })
        setToken(data.access_token)
        router.replace(nextPath)
      } catch (error) {
        const detail =
          error && typeof error === "object" && "message" in error
            ? String(error.message)
            : "No se pudo validar el código de Telegram."
        setMessage(detail)
      } finally {
        setLoading(false)
      }
    }

    void loginWithTelegramCode()
  }, [code, nextPath, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage("")
    
    try {
      const data = await apiRequest<{ access_token: string }>("/auth/token", {
        method: "POST",
        body: new URLSearchParams({
          username: email,
          password: password,
        }),
      })

      setToken(data.access_token)
      router.replace(nextPath)
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
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="rounded-[2rem] border border-white/10 bg-white/6 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-300">
            Login
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">
            Volvé a tu dashboard sin perder contexto
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-white/72">
            Seguí tu pipeline, retomá la CV Suite y revisá tus búsquedas guardadas desde el mismo
            lugar donde dejaste todo.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              "Pipeline con foco semanal y seguimiento real.",
              "CV Intelligence con ATS, job match y cover letters.",
              "Alertas, historial y entrevistas prácticas en un solo flujo.",
              "Billing y upgrades cuando realmente necesitás escalar.",
            ].map((item) => (
              <div key={item} className="rounded-[1.5rem] border border-white/10 bg-black/15 p-4 text-sm text-white/74">
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-white/6 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-300">
            Acceso
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight">Iniciá sesión</h2>
          <p className="mt-3 text-sm leading-7 text-white/68">
            También podés entrar desde Telegram si generaste un código de acceso en el bot.
          </p>

          {message ? (
            <div className="mt-6 rounded-2xl border border-white/10 bg-white/8 px-4 py-3 text-sm text-white/90">
              {message}
            </div>
          ) : null}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
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
              placeholder="Tu password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
              required
            />
            <button
              type="submit"
              disabled={loading || !!code}
              className="w-full rounded-2xl bg-gradient-to-r from-indigo-500 via-sky-500 to-amber-400 px-4 py-3 font-semibold text-slate-950 transition hover:opacity-95 disabled:opacity-60"
            >
              {loading ? "Ingresando..." : code ? "Validando código..." : "Entrar al dashboard"}
            </button>
          </form>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-white/62">
            <Link href="/forgot-password" className="font-medium text-indigo-300 hover:text-indigo-200">
              ¿Olvidaste tu password?
            </Link>
            <span>
              ¿No tenés cuenta?{" "}
              <Link href="/register" className="font-semibold text-amber-300 hover:text-amber-200">
                Crear cuenta
              </Link>
            </span>
          </div>

          <PublicFooterLinks />
        </section>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
          Cargando acceso...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  )
}
