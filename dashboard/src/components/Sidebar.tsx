"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Search, 
  FileText, 
  CreditCard, 
  Settings, 
  Zap,
  LogOut
} from "lucide-react"

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Inicio" },
  { href: "/dashboard/buscar", icon: Search, label: "Buscar" },
  { href: "/dashboard/postulaciones", icon: FileText, label: "Postulaciones" },
  { href: "/dashboard/suscripcion", icon: CreditCard, label: "Suscripción" },
  { href: "/dashboard/configuracion", icon: Settings, label: "Configuración" },
]

export default function Sidebar() {
  const pathname = usePathname()

  const handleLogout = () => {
    localStorage.removeItem("token")
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
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-1 ${
                isActive 
                  ? "bg-purple-50 text-purple-700 font-medium" 
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="bg-gradient-to-r from-amber-400 to-orange-500 rounded-xl p-4 text-white mb-4">
          <div className="flex items-center gap-2">
            <Zap size={18} />
            <span className="font-semibold">Plan Free</span>
          </div>
          <p className="text-xs mt-1 opacity-90">Actualiza a Premium</p>
        </div>
        
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
