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
  LogOut,
  Shield,
} from "lucide-react"

import { apiRequest, clearToken } from "@/lib/api"

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Inicio" },
  { href: "/dashboard/buscar", icon: Search, label: "Buscar" },
  { href: "/dashboard/postulaciones", icon: FileText, label: "Postulaciones" },
  { href: "/dashboard/cv", icon: Sparkles, label: "CV" },
  { href: "/dashboard/suscripcion", icon: CreditCard, label: "Plan" },
  { href: "/dashboard/configuracion", icon: Settings, label: "Configuracion" },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [planLabel, setPlanLabel] = useState("FREE")
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    apiRequest<{ plan: string; is_admin: boolean }>("/auth/me", {}, true)
      .then((data) => {
        setPlanLabel((data.plan || "free").toUpperCase())
        setIsAdmin(Boolean(data.is_admin))
      })
      .catch(() => {
        setPlanLabel("FREE")
        setIsAdmin(false)
      })
  }, [])

  const handleLogout = () => {
    clearToken()
    window.location.href = "/login"
  }

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-stone-200 bg-[radial-gradient(circle_at_top,_rgba(79,70,229,0.14),_transparent_26%),linear-gradient(180deg,_#fcfbf7,_#f5f5f4)] text-stone-900">
      <div className="border-b border-stone-200 px-6 py-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-indigo-600">
          JobBot AR
        </p>
        <div className="mt-3 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-stone-950">Dashboard</h1>
            <p className="mt-1 text-sm text-stone-500">Busca, mejora y hace seguimiento.</p>
          </div>
          <span className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            {planLabel}
          </span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-5">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`mb-1.5 flex items-center gap-3 rounded-2xl px-4 py-3 ${
                isActive
                  ? "bg-stone-950 font-medium text-white"
                  : "text-stone-600 hover:bg-white hover:text-stone-950"
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </Link>
          )
        })}

        {isAdmin ? (
          <Link
            href="/dashboard/admin"
            className={`mb-1.5 flex items-center gap-3 rounded-2xl px-4 py-3 ${
              pathname === "/dashboard/admin"
                ? "bg-indigo-600 font-medium text-white"
                : "text-indigo-700 hover:bg-indigo-50 hover:text-indigo-900"
            }`}
          >
            <Shield size={20} />
            <span>Admin</span>
          </Link>
        ) : null}
      </nav>

      <div className="mx-4 mb-4 rounded-[1.5rem] border border-stone-200 bg-white px-4 py-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-500">
          Hoy
        </p>
        <p className="mt-2 text-sm leading-6 text-stone-700">
          Entra, elegi una accion y avanza. El resto puede esperar.
        </p>
      </div>

      <div className="border-t border-stone-200 p-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-stone-600 hover:bg-white hover:text-stone-950"
        >
          <LogOut size={20} />
          <span>Cerrar sesion</span>
        </button>
      </div>
    </aside>
  )
}
