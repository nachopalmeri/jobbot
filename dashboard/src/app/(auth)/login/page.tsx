"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">JobBot</h1>
        <p className="text-white/60 text-center mb-6">Iniciá sesión en tu cuenta</p>
        {message ? (
          <div className="mb-4 rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm text-white">
            {message}
          </div>
        ) : null}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            required
          />
          <button 
            type="submit" 
            disabled={loading || !!code}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-semibold text-white hover:opacity-90 transition-all disabled:opacity-50"
          >
            {loading ? "Ingresando..." : code ? "Validando código..." : "Iniciar Sesión"}
          </button>
        </form>
        
        <p className="text-white/60 text-center mt-6">
          ¿No tienes cuenta?{" "}
          <Link href="/register" className="text-purple-400 hover:underline">
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
          Cargando acceso...
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  )
}
