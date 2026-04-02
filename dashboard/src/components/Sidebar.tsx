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
  Crown
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
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen">
      <div className="p-6">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          JobBot
        </h1>
      </div>
      
      <nav className="px-4 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-1 ${
                isActive 
                  ? "bg-purple-50 text-purple-700 font-medium" 
                  : item.highlight
                    ? "text-pink-600 hover:bg-pink-50 font-medium"
                    : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
              {item.highlight && credits > 0 && (
                <span className="ml-auto bg-pink-100 text-pink-700 text-xs font-bold px-2 py-0.5 rounded-full">
                  {credits}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-200">
        {/* Credit balance card */}
        {credits > 0 ? (
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4 text-white mb-3">
            <div className="flex items-center gap-2">
              <Crown size={18} />
              <span className="font-semibold">{credits} créditos</span>
            </div>
            <p className="text-xs mt-1 opacity-90">Disponibles para usar</p>
          </div>
        ) : (
          <div className="bg-gradient-to-r from-amber-400 to-orange-500 rounded-xl p-4 text-white mb-3">
            <div className="flex items-center gap-2">
              <Zap size={18} />
              <span className="font-semibold">Plan {planLabel}</span>
            </div>
            <p className="text-xs mt-1 opacity-90">
              <Link href="/dashboard/creditos" className="underline hover:no-underline">
                Conseguí créditos →
              </Link>
            </p>
          </div>
        )}
        
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full text-slate-600 hover:bg-slate-50 rounded-lg"
        >
          <LogOut size={20} />
          <span>Cerrar sesión</span>
        </button>
      </div>
    </aside>
  )
}
