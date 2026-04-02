"use client"

import { useState } from "react"
import Link from "next/link"

export default function RegisterPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [telegramId, setTelegramId] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const res = await fetch("http://localhost:8000/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          telegram_id: parseInt(telegramId),
          name: "Usuario"
        }),
      })
      
      if (res.ok) {
        alert("Cuenta creada. Iniciá sesión.")
        window.location.href = "/login"
      } else {
        const data = await res.json()
        alert(data.detail || "Error al registrar")
      }
    } catch (error) {
      alert("Error de conexión")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">JobBot</h1>
        <p className="text-white/60 text-center mb-6">Creá tu cuenta</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Tu ID de Telegram"
            value={telegramId}
            onChange={(e) => setTelegramId(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            required
          />
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
