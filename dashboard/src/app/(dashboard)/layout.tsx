"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

import Sidebar from "@/components/Sidebar"
import { getToken } from "@/lib/api"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const token = getToken()

  useEffect(() => {
    if (!token) {
      router.replace(`/login?next=${encodeURIComponent(pathname || "/dashboard")}`)
    }
  }, [pathname, router, token])

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-500">
        Cargando tu dashboard...
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-[linear-gradient(180deg,_#fafaf9,_#f5f5f4_100%)] text-stone-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
