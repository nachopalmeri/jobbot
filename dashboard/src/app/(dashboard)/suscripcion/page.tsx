"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Check, CreditCard, Crown, Sparkles, Wallet } from "lucide-react";

import { supportEmail } from "@/lib/site";
import { apiRequest } from "@/lib/api";

interface Plan {
  id: string;
  name: string;
  price: number;
  monthly_price?: number;
  yearly_price?: number;
  yearly_monthly_equivalent?: number;
  yearly_savings_percent?: number;
  currency: string;
  features: string[];
  eyebrow?: string;
  spotlight?: string;
  recommended?: boolean;
  featured?: boolean;
}

interface SubscriptionStatus {
  plan: string;
  status?: string;
  provider?: string | null;
  billing_cycle?: string;
  expires_at?: string | null;
  can_cancel?: boolean;
  can_manage_billing?: boolean;
  support_email?: string;
}

const providers = [
  { name: "Stripe", icon: CreditCard, color: "bg-stone-950", available: true, note: "Suscripción mensual o anual" },
  { name: "MercadoPago", icon: Wallet, color: "bg-sky-600", available: true, note: "Pago único del ciclo elegido" },
];

const planOverrides: Record<
  string,
  {
    price: number;
    features: string[];
    eyebrow?: string;
    spotlight?: string;
    recommended?: boolean;
    featured?: boolean;
  }
> = {
  free: {
    price: 0,
    features: [
      "3 búsquedas guiadas por día",
      "Hasta 3 resultados visibles por consulta",
      "Dashboard liviano",
      "Scanner ATS básico",
    ],
    eyebrow: "Explorar",
  },
  starter: {
    price: 4,
    features: [
      "12 búsquedas por día",
      "Resultados completos",
      "Pipeline de postulaciones",
      "Alertas automáticas por Telegram",
    ],
    eyebrow: "Base de tracción",
  },
  pro: {
    price: 8,
    features: [
      "40 búsquedas por día",
      "4 análisis IA de CV por mes",
      "Match score y keywords faltantes",
      "Pipeline y alertas avanzadas",
    ],
    eyebrow: "Más equilibrado",
    recommended: true,
  },
  premium: {
    price: 12,
    features: [
      "Todo lo de Pro",
      "20 análisis IA + 10 mock interviews por mes",
      "Cover letters personalizadas",
      "Historial completo y workflow de CV",
      "120 búsquedas por día",
    ],
    eyebrow: "CV Intelligence",
    spotlight:
      "La suite completa de CV vive acá: score, ATS, match, cover letters, historial y preparación de entrevista.",
    featured: true,
  },
};

export default function SuscripcionPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [currentPlan, setCurrentPlan] = useState("free");
  const [selectedPlan, setSelectedPlan] = useState("premium");
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [billingLoading, setBillingLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [plansData, statusData] = await Promise.all([
          apiRequest<{ plans: Plan[] }>("/subscriptions/plans", {}, true),
          apiRequest<SubscriptionStatus>("/subscriptions/status", {}, true),
        ]);

        const decoratedPlans: Plan[] = (plansData.plans || []).map((plan) => ({
          ...plan,
          ...(planOverrides[plan.id] || {}),
          features: planOverrides[plan.id]?.features || plan.features,
          price: planOverrides[plan.id]?.price ?? plan.price,
        }));

        setPlans(decoratedPlans);
        const activePlan = statusData.plan || "free";
        setStatus(statusData);
        setCurrentPlan(activePlan);
        setSelectedPlan(activePlan === "free" ? "pro" : activePlan);
        setBillingCycle(
          statusData.billing_cycle === "yearly" && activePlan !== "free" ? "yearly" : "monthly",
        );
      } catch (err) {
        setMessage(
          err && typeof err === "object" && "message" in err
            ? String(err.message)
            : "No se pudieron cargar los planes.",
        );
      }
    };

    void load();
  }, []);

  const paidPlans = useMemo(() => plans.filter((plan) => plan.id !== "free"), [plans]);
  const selectedPlanData = useMemo(
    () => plans.find((plan) => plan.id === selectedPlan),
    [plans, selectedPlan],
  );

  const displayedPrice = (plan: Plan) =>
    billingCycle === "yearly" && plan.yearly_price ? plan.yearly_price : plan.price;

  const displayedPeriod = billingCycle === "yearly" ? "/año" : "/mes";

  const activeSupportEmail = status?.support_email || supportEmail;

  const handleUpgrade = async (provider: string) => {
    try {
      setMessage("");
      const data = await apiRequest<{ url?: string; detail?: string }>(
        "/subscriptions/create-checkout",
        {
          method: "POST",
          body: JSON.stringify({ provider, plan: selectedPlan, billing_cycle: billingCycle }),
        },
        true,
      );

      if (data.url) {
        window.location.assign(data.url);
      } else {
        setMessage(data.detail || "No se pudo iniciar el checkout.");
      }
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "Error al procesar el pago.",
      );
    }
  };

  const handleManageBilling = async () => {
    try {
      setBillingLoading(true);
      setMessage("");
      const data = await apiRequest<{ url?: string; detail?: string }>("/subscriptions/manage-billing", {
        method: "POST",
      }, true);
      if (data.url) {
        window.location.assign(data.url);
        return;
      }
      setMessage(data.detail || `Escribinos a ${activeSupportEmail}`);
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No pudimos abrir la gestión de facturación.",
      );
    } finally {
      setBillingLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      setBillingLoading(true);
      setMessage("");
      const data = await apiRequest<{ message: string; status?: string; expires_at?: string | null }>(
        "/subscriptions/cancel",
        { method: "POST" },
        true,
      );
      setMessage(data.message);
      setStatus((current) =>
        current
          ? { ...current, status: data.status || "cancelled", expires_at: data.expires_at ?? null }
          : current,
      );
      if (!data.expires_at) {
        setCurrentPlan("free");
      }
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No pudimos cancelar la suscripción.",
      );
    } finally {
      setBillingLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#fafaf9,_#f5f5f4_36%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm lg:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
            Pricing
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-950 lg:text-5xl">
            Planes más realistas y con una escalera que sí se entiende.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-stone-600">
            Bajamos el free para que sea una entrada genuina, no un plan que promete demasiado.
            El valor fuerte aparece cuando realmente empezás a operar mejor: tracker, CV suite y preparación.
          </p>

          <div className="mt-6 inline-flex rounded-full border border-stone-200 bg-stone-100 p-1">
            <button
              type="button"
              onClick={() => setBillingCycle("monthly")}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                billingCycle === "monthly"
                  ? "bg-white text-stone-950 shadow-sm"
                  : "text-stone-600 hover:text-stone-950"
              }`}
            >
              Mensual
            </button>
            <button
              type="button"
              onClick={() => setBillingCycle("yearly")}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                billingCycle === "yearly"
                  ? "bg-stone-950 text-white shadow-sm"
                  : "text-stone-600 hover:text-stone-950"
              }`}
            >
              Anual
              <span className="ml-2 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                2 meses off
              </span>
            </button>
          </div>

          {message ? (
            <div className="mt-5 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-700">
              {message}
            </div>
          ) : null}
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-4">
            {plans.map((plan) => {
              const isCurrent = plan.id === currentPlan;
              const isSelected = plan.id === selectedPlan;

              return (
                <article
                  key={plan.id}
                  className={`relative rounded-[2rem] border p-6 shadow-sm transition-all ${
                    plan.featured
                      ? "border-indigo-300 bg-gradient-to-br from-indigo-50 via-white to-amber-50"
                      : isSelected
                        ? "border-stone-950 bg-white"
                        : "border-stone-200 bg-white/90"
                  }`}
                >
                  {plan.recommended ? (
                    <span className="absolute -top-3 left-5 rounded-full bg-stone-950 px-3 py-1 text-xs font-semibold text-white">
                      Más elegido
                    </span>
                  ) : null}

                  {plan.featured ? (
                    <span className="absolute -top-3 right-5 rounded-full bg-indigo-600 px-3 py-1 text-xs font-semibold text-white">
                      Premium
                    </span>
                  ) : null}

                  {plan.eyebrow ? (
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                      {plan.eyebrow}
                    </p>
                  ) : null}

                  <div className="mt-3 flex items-center gap-2">
                    <h2 className="text-2xl font-semibold text-stone-950">{plan.name}</h2>
                    {plan.featured ? (
                      <span className="rounded-full bg-amber-100 p-1 text-amber-700">
                        <Crown size={14} />
                      </span>
                    ) : null}
                  </div>

                  <div className="mt-4 flex items-end gap-2">
                    <span className="text-5xl font-semibold tracking-tight text-stone-950">
                      ${displayedPrice(plan)}
                    </span>
                    <span className="pb-2 text-stone-500">{displayedPeriod}</span>
                  </div>

                  {billingCycle === "yearly" && plan.yearly_price ? (
                    <p className="mt-2 text-sm text-stone-500">
                      Equivale a ${plan.yearly_monthly_equivalent?.toFixed(2) ?? "0"}/mes y te ahorra
                      {` ${plan.yearly_savings_percent ?? 0}%`} frente al mensual.
                    </p>
                  ) : null}

                  {plan.spotlight ? (
                    <div className="mt-5 rounded-2xl border border-indigo-200 bg-indigo-50 p-4">
                      <div className="flex items-center gap-2 text-indigo-700">
                        <Sparkles size={16} />
                        <span className="text-sm font-semibold">Feature destacada</span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-indigo-950">{plan.spotlight}</p>
                    </div>
                  ) : null}

                  <ul className="mt-6 space-y-3">
                    {plan.features.map((feature: string) => (
                      <li key={feature} className="flex items-start gap-2 text-sm leading-6 text-stone-600">
                        <Check className="mt-1 text-emerald-600" size={16} />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <button
                    type="button"
                    onClick={() => setSelectedPlan(plan.id)}
                    disabled={isCurrent || plan.id === "free"}
                    className={`mt-8 w-full rounded-2xl px-4 py-3 font-medium transition-colors ${
                      isCurrent
                        ? "cursor-not-allowed bg-stone-100 text-stone-400"
                        : plan.featured
                          ? "bg-indigo-600 text-white hover:bg-indigo-700"
                          : "bg-stone-950 text-white hover:bg-stone-800"
                    }`}
                  >
                    {isCurrent ? "Plan actual" : plan.id === "free" ? "Incluido" : "Seleccionar"}
                  </button>
                </article>
              );
            })}
          </div>

          <div className="space-y-5">
            <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-stone-950">Checkout del plan</h2>
              <p className="mt-2 text-sm leading-6 text-stone-600">
                Estás por activar <strong>{selectedPlan.toUpperCase()}</strong> en ciclo{" "}
                <strong>{billingCycle === "yearly" ? "anual" : "mensual"}</strong>. Elegí el medio
                de pago que prefieras o comprá créditos si querés pagar solo por uso.
              </p>

              {selectedPlanData ? (
                <div className="mt-4 rounded-2xl border border-stone-200 bg-stone-50 p-4 text-sm text-stone-700">
                  <div className="flex items-center justify-between gap-3">
                    <span>Total del ciclo</span>
                    <strong className="text-stone-950">
                      ${displayedPrice(selectedPlanData)} {selectedPlanData.currency}
                    </strong>
                  </div>
                  {billingCycle === "yearly" && selectedPlanData.yearly_monthly_equivalent ? (
                    <div className="mt-2 flex items-center justify-between gap-3 text-stone-500">
                      <span>Promedio mensual</span>
                      <span>${selectedPlanData.yearly_monthly_equivalent.toFixed(2)}/mes</span>
                    </div>
                  ) : null}
                </div>
              ) : null}

              {status?.provider ? (
                <div className="mt-4 rounded-2xl border border-stone-200 bg-white p-4 text-sm text-stone-700">
                  <div className="flex items-center justify-between gap-3">
                    <span>Proveedor actual</span>
                    <strong className="capitalize text-stone-950">{status.provider}</strong>
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3">
                    <span>Estado</span>
                    <span className="capitalize text-stone-950">{status.status || "active"}</span>
                  </div>
                  {status.expires_at ? (
                    <div className="mt-2 flex items-center justify-between gap-3">
                      <span>Vence / se corta</span>
                      <span className="text-stone-950">
                        {new Date(status.expires_at).toLocaleDateString("es-AR")}
                      </span>
                    </div>
                  ) : null}
                </div>
              ) : null}

              <div className="mt-5 space-y-3">
                {providers.map((provider) => (
                  <button
                    key={provider.name}
                    type="button"
                    onClick={() => handleUpgrade(provider.name.toLowerCase())}
                    disabled={!provider.available || !paidPlans.some((plan) => plan.id === selectedPlan)}
                    className={`${provider.color} flex w-full items-center justify-between rounded-2xl px-4 py-3 font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60`}
                  >
                    <span className="inline-flex items-center gap-2">
                      <provider.icon size={18} />
                      <span>{provider.name}</span>
                    </span>
                    <span className="text-sm opacity-80">{provider.note}</span>
                  </button>
                ))}
              </div>

              <div className="mt-4 rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-950">
                Si preferís no suscribirte, podés ir por <strong>créditos</strong>: desbloqueás la CV
                Suite o comprás packs para usar IA cuando realmente la necesites.
                <Link href="/dashboard/creditos" className="ml-2 font-semibold underline underline-offset-4">
                  Ver créditos
                </Link>
              </div>

              {currentPlan !== "free" ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={handleManageBilling}
                    disabled={billingLoading}
                    className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm font-medium text-stone-950 transition hover:border-stone-950 disabled:opacity-60"
                  >
                    Gestionar facturación
                  </button>
                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={billingLoading || !status?.can_cancel}
                    className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 transition hover:bg-red-100 disabled:opacity-60"
                  >
                    Cancelar suscripción
                  </button>
                </div>
              ) : null}

              <p className="mt-4 text-xs leading-6 text-stone-500">
                Soporte de billing:{" "}
                <a href={`mailto:${activeSupportEmail}`} className="font-semibold text-stone-700 underline underline-offset-4">
                  {activeSupportEmail}
                </a>
              </p>
            </section>

            <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-stone-950">Cómo pensar los planes</h2>
              <div className="mt-4 space-y-3">
                {[
                  "Free es para probar el flujo, no para sostener una búsqueda completa.",
                  "Starter destraba el tracker y las alertas para empezar a operar con orden.",
                  "Pro mete IA donde más ayuda: CV, match y priorización.",
                  "Premium junta toda la capa de CV Intelligence dentro del dashboard.",
                ].map((item) => (
                  <div
                    key={item}
                  className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-600"
                >
                  {item}
                </div>
              ))}
            </div>
          </section>

            <section className="rounded-[2rem] border border-stone-200 bg-white/90 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-stone-950">¿Suscripción o créditos?</h2>
              <div className="mt-4 space-y-3 text-sm leading-6 text-stone-600">
                <p>
                  <strong className="text-stone-950">Mensual o anual</strong> si querés usar JobBot todas
                  las semanas, con tracker, alertas y rutina completa.
                </p>
                <p>
                  <strong className="text-stone-950">Créditos</strong> si tu uso fuerte está en CV,
                  cover letters o entrevistas y preferís pagar por bloques.
                </p>
                <p>
                  <strong className="text-stone-950">Unlock lifetime</strong> si querés la capa CV
                  desbloqueada sin sumar otra suscripción mensual.
                </p>
              </div>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}
