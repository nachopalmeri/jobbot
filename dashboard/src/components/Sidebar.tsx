"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Search,
  FileText,
  CreditCard,
  Settings,
  Sparkles,
  Zap,
  LogOut,
  Coins,
  Crown,
  ArrowUpRight,
} from "lucide-react"

import { apiRequest, clearToken } from "@/lib/api"

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Inicio" },
  { href: "/dashboard/buscar", icon: Search, label: "Buscar" },
  { href: "/dashboard/cv", icon: Sparkles, label: "CV Suite" },
  { href: "/dashboard/postulaciones", icon: FileText, label: "Postulaciones" },
  { href: "/dashboard/creditos", icon: Coins, label: "Créditos", highlight: true },
  { href: "/dashboard/suscripcion", icon: CreditCard, label: "Suscripción" },
  { href: "/dashboard/configuracion", icon: Settings, label: "Configuración" },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [planLabel, setPlanLabel] = useState("Free")
  const [credits, setCredits] = useState(0)

  useEffect(() => {
    // Cargar plan
    apiRequest<{ plan: string }>("/subscriptions/status", {}, true)
      .then((data) => setPlanLabel((data.plan || "free").toUpperCase()))
      .catch(() => setPlanLabel("Free"))
    
    // Cargar créditos
    apiRequest<{ total_credits: number }>("/credits/balance", {}, true)
      .then((data) => setCredits(data.total_credits || 0))
      .catch(() => setCredits(0))
  }, [])

  const handleLogout = () => {
    clearToken()
    window.location.href = "/login"
  }

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-stone-900/10 bg-stone-950 text-white">
      <div className="border-b border-white/10 px-6 py-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-indigo-300">
          JobBot AR
        </p>
        <div className="mt-3 flex items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">Dashboard</h1>
            <p className="mt-1 text-sm text-stone-400">
              Buscar, aplicar y mejorar tu CV sin perder foco.
            </p>
          </div>
          <span className="rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-200">
            {planLabel}
          </span>
        </div>
      </div>

      <div className="px-6 py-5">
        {credits > 0 ? (
          <div className="rounded-[1.5rem] border border-amber-400/20 bg-gradient-to-br from-amber-400/15 to-indigo-500/10 p-4">
            <div className="flex items-center gap-2 text-amber-200">
              <Crown size={18} />
              <span className="text-sm font-semibold">{credits} créditos listos</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-stone-300">
              Usalos en CV Suite para scans pro, cover letters y mejoras con IA.
            </p>
          </div>
        ) : (
          <Link
            href="/dashboard/suscripcion"
            className="block rounded-[1.5rem] border border-white/10 bg-white/5 p-4 hover:border-indigo-400/30 hover:bg-indigo-500/10"
          >
            <div className="flex items-center gap-2 text-indigo-200">
              <Zap size={18} />
              <span className="text-sm font-semibold">Subí de plan</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-stone-300">
              Desbloqueá pipeline completo, búsquedas mejores y CV Intelligence.
            </p>
            <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-white">
              Ver planes
              <ArrowUpRight size={14} />
            </span>
          </Link>
        )}
      </div>

      <nav className="flex-1 px-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`mb-1.5 flex items-center gap-3 rounded-2xl px-4 py-3 ${
                isActive 
                  ? "bg-white text-stone-950 font-medium"
                  : item.highlight
                    ? "text-amber-200 hover:bg-white/5 font-medium"
                    : "text-stone-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
              {item.highlight && credits > 0 && (
                <span className="ml-auto rounded-full bg-amber-300 px-2 py-0.5 text-xs font-bold text-stone-950">
                  {credits}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-white/10 p-4">
        <button 
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-stone-300 hover:bg-white/5 hover:text-white"
        >
          <LogOut size={20} />
          <span>Cerrar sesión</span>
        </button>
      </div>
    </aside>
  )
}
