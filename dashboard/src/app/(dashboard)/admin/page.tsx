"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CreditCard,
  Crown,
  DollarSign,
  Loader2,
  Shield,
  TrendingUp,
  Users,
} from "lucide-react";

import { apiRequest } from "@/lib/api";

interface AdminMetrics {
  users: {
    telegram_total: number;
    web_total: number;
    active_today: number;
    new_this_week: number;
  };
  revenue: {
    total_usd: number;
    monthly_usd: number;
  };
  plans: Array<{
    plan: string;
    count: number;
  }>;
  credits: {
    total_sold: number;
    remaining: number;
    consumed: number;
  };
  recent_payments: Array<{
    id: number;
    email: string;
    amount: number;
    currency: string;
    provider: string;
    status: string;
    created_at: string;
  }>;
}

const planTone: Record<string, string> = {
  free: "bg-stone-200 text-stone-700",
  starter: "bg-sky-100 text-sky-700",
  pro: "bg-indigo-100 text-indigo-700",
  premium: "bg-amber-100 text-amber-700",
};

export default function AdminPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const user = await apiRequest<{ email: string; is_admin: boolean }>("/auth/me", {}, true);
        setUserEmail(user.email);

        if (!user.is_admin) {
          setIsAdmin(false);
          return;
        }

        setIsAdmin(true);
        const data = await apiRequest<AdminMetrics>("/admin/metrics", {}, true);
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error cargando panel admin");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const topStats = useMemo(
    () =>
      metrics
        ? [
            {
              label: "Revenue total",
              value: `$${metrics.revenue.total_usd.toFixed(2)}`,
              detail: "Acumulado histórico",
              icon: DollarSign,
              tone: "bg-emerald-100 text-emerald-700",
            },
            {
              label: "Revenue 30 días",
              value: `$${metrics.revenue.monthly_usd.toFixed(2)}`,
              detail: "Pulso comercial reciente",
              icon: TrendingUp,
              tone: "bg-indigo-100 text-indigo-700",
            },
            {
              label: "Usuarios web",
              value: String(metrics.users.web_total),
              detail: `+${metrics.users.new_this_week} esta semana`,
              icon: Users,
              tone: "bg-sky-100 text-sky-700",
            },
            {
              label: "Créditos vendidos",
              value: String(metrics.credits.total_sold),
              detail: `${metrics.credits.remaining} sin usar`,
              icon: CreditCard,
              tone: "bg-amber-100 text-amber-700",
            },
          ]
        : [],
    [metrics],
  );

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto flex h-[70vh] max-w-2xl flex-col items-center justify-center px-6 text-center">
        <div className="rounded-full bg-red-100 p-4">
          <AlertCircle className="h-8 w-8 text-red-600" />
        </div>
        <h1 className="mt-5 text-3xl font-semibold text-stone-950">Acceso restringido</h1>
        <p className="mt-3 text-base leading-7 text-stone-600">
          Esta sección solo aparece para cuentas marcadas como admin dentro del sistema.
        </p>
        <p className="mt-2 text-sm text-stone-500">Cuenta actual: {userEmail || "sin email"}</p>
        <Link
          href="/dashboard"
          className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          Volver al dashboard
          <ArrowRight size={16} />
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto flex h-[70vh] max-w-2xl flex-col items-center justify-center px-6 text-center">
        <div className="rounded-full bg-amber-100 p-4">
          <AlertCircle className="h-8 w-8 text-amber-600" />
        </div>
        <h1 className="mt-5 text-3xl font-semibold text-stone-950">No pudimos cargar el panel</h1>
        <p className="mt-3 text-base leading-7 text-stone-600">{error}</p>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  const usageRate = Math.round(
    (metrics.credits.consumed / Math.max(metrics.credits.total_sold, 1)) * 100,
  );

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.08),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(245,158,11,0.09),_transparent_24%),linear-gradient(180deg,_#fafaf9,_#f5f5f4_45%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <section className="overflow-hidden rounded-[2rem] border border-stone-200 bg-white/92 p-6 shadow-sm lg:p-8">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-600">
                Operaciones internas
              </p>
              <h1 className="mt-3 text-3xl font-semibold text-stone-950 lg:text-5xl">
                Panel admin para revenue, usuarios y señales reales de uso.
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600 lg:text-lg">
                Este espacio vive separado del resto del dashboard para que puedas revisar negocio
                sin mezclarlo con la experiencia del usuario final.
              </p>
            </div>

            <div className="rounded-[1.75rem] border border-indigo-200 bg-[linear-gradient(135deg,_rgba(79,70,229,0.08),_rgba(245,158,11,0.08))] p-5">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-white/85 p-3 text-indigo-700 shadow-sm">
                  <Shield size={18} />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-700">
                    Estado admin
                  </p>
                  <h2 className="mt-1 text-2xl font-semibold text-stone-950">Acceso validado</h2>
                </div>
              </div>
              <p className="mt-4 text-sm leading-6 text-stone-600">
                Entraste con <span className="font-medium text-stone-900">{userEmail}</span>. Si
                querés ampliar admins, el backend ya soporta emails y Telegram IDs configurables.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {topStats.map((stat) => (
            <article
              key={stat.label}
              className="rounded-3xl border border-stone-200 bg-white/90 p-5 shadow-sm"
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-stone-500">{stat.label}</p>
                  <p className="mt-3 text-3xl font-semibold text-stone-950">{stat.value}</p>
                  <p className="mt-2 text-sm text-stone-600">{stat.detail}</p>
                </div>
                <div className={`rounded-2xl p-3 ${stat.tone}`}>
                  <stat.icon size={20} />
                </div>
              </div>
            </article>
          ))}
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <article className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
              Distribución de planes
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-950">
              Cómo se reparte la base actual
            </h2>
            <div className="mt-6 space-y-4">
              {metrics.plans.map((plan) => {
                const percentage = Math.round((plan.count / Math.max(metrics.users.web_total, 1)) * 100);
                return (
                  <div key={plan.plan} className="space-y-2">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${planTone[plan.plan] || planTone.free}`}
                        >
                          {plan.plan.toUpperCase()}
                        </span>
                        <span className="text-sm text-stone-600">{plan.count} usuarios</span>
                      </div>
                      <span className="text-sm font-medium text-stone-700">{percentage}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-stone-100">
                      <div
                        className="h-full rounded-full bg-indigo-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <article className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
              Actividad
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-stone-950">
              Señales rápidas del sistema
            </h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {[
                {
                  label: "Activos hoy",
                  value: metrics.users.active_today,
                  tone: "bg-indigo-50",
                },
                {
                  label: "Usuarios Telegram",
                  value: metrics.users.telegram_total,
                  tone: "bg-sky-50",
                },
                {
                  label: "Créditos consumidos",
                  value: metrics.credits.consumed,
                  tone: "bg-amber-50",
                },
                {
                  label: "Tasa de uso",
                  value: `${usageRate}%`,
                  tone: "bg-emerald-50",
                },
              ].map((item) => (
                <div key={item.label} className={`rounded-2xl ${item.tone} p-5`}>
                  <p className="text-sm font-medium text-stone-500">{item.label}</p>
                  <p className="mt-3 text-3xl font-semibold text-stone-950">{item.value}</p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="rounded-[2rem] border border-stone-200 bg-white/92 p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-amber-100 p-3 text-amber-700">
              <Crown size={20} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                Últimos pagos
              </p>
              <h2 className="mt-1 text-2xl font-semibold text-stone-950">
                Revenue reciente y estados de cobro
              </h2>
            </div>
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[680px]">
              <thead>
                <tr className="border-b border-stone-200 text-left">
                  <th className="pb-3 text-sm font-semibold text-stone-600">Email</th>
                  <th className="pb-3 text-sm font-semibold text-stone-600">Monto</th>
                  <th className="pb-3 text-sm font-semibold text-stone-600">Provider</th>
                  <th className="pb-3 text-sm font-semibold text-stone-600">Estado</th>
                  <th className="pb-3 text-sm font-semibold text-stone-600">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {metrics.recent_payments.map((payment) => (
                  <tr key={payment.id}>
                    <td className="py-4 text-sm text-stone-900">{payment.email}</td>
                    <td className="py-4 text-sm font-semibold text-stone-900">
                      ${payment.amount.toFixed(2)} {payment.currency}
                    </td>
                    <td className="py-4 text-sm capitalize text-stone-600">{payment.provider}</td>
                    <td className="py-4">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                          payment.status === "completed"
                            ? "bg-emerald-100 text-emerald-700"
                            : payment.status === "pending"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-rose-100 text-rose-700"
                        }`}
                      >
                        {payment.status}
                      </span>
                    </td>
                    <td className="py-4 text-sm text-stone-500">
                      {new Date(payment.created_at).toLocaleDateString("es-AR")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
