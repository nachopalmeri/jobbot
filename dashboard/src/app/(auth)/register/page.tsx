"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">JobBot</h1>
        <p className="text-white/60 text-center mb-6">Creá tu cuenta y empezá desde web</p>
        {message ? (
          <div className="mb-4 rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm text-white">
            {message}
          </div>
        ) : null}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <input
            type="text"
            placeholder="Tu ID de Telegram (opcional)"
            value={telegramId}
            onChange={(e) => setTelegramId(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <p className="px-1 text-xs text-white/60">
            Si querés alertas y login desde el bot, completalo ahora. Si no, podés arrancar igual con cuenta web.
          </p>
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
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg font-semibold text-white hover:opacity-90 transition-all disabled:opacity-50"
          >
            {loading ? "Creando cuenta..." : "Crear Cuenta"}
          </button>
        </form>
        
        <p className="text-white/60 text-center mt-6">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-purple-400 hover:underline">
            Iniciá sesión
          </Link>
        </p>
      </div>
    </div>
  )
}
