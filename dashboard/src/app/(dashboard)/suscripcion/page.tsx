"use client";

import { useEffect, useMemo, useState } from "react";
import { Bitcoin, Check, CreditCard, Crown, Sparkles, Wallet } from "lucide-react";

import { apiRequest } from "@/lib/api";

interface Plan {
  id: string;
  name: string;
  price: number;
  currency: string;
  features: string[];
  eyebrow?: string;
  spotlight?: string;
  recommended?: boolean;
  featured?: boolean;
}

const providers = [
  { name: "Stripe", icon: CreditCard, color: "bg-stone-950" },
  { name: "MercadoPago", icon: Wallet, color: "bg-sky-600" },
  { name: "Crypto", icon: Bitcoin, color: "bg-amber-500" },
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
  const [message, setMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [plansData, statusData] = await Promise.all([
          apiRequest<{ plans: Plan[] }>("/subscriptions/plans", {}, true),
          apiRequest<{ plan: string }>("/subscriptions/status", {}, true),
        ]);

        const decoratedPlans: Plan[] = (plansData.plans || []).map((plan) => ({
          ...plan,
          ...(planOverrides[plan.id] || {}),
          features: planOverrides[plan.id]?.features || plan.features,
          price: planOverrides[plan.id]?.price ?? plan.price,
        }));

        setPlans(decoratedPlans);
        const activePlan = statusData.plan || "free";
        setCurrentPlan(activePlan);
        setSelectedPlan(activePlan === "free" ? "pro" : activePlan);
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

  const handleUpgrade = async (provider: string) => {
    try {
      setMessage("");
      const data = await apiRequest<{ url?: string; detail?: string }>(
        "/subscriptions/create-checkout",
        {
          method: "POST",
          body: JSON.stringify({ provider, plan: selectedPlan }),
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
                      ${plan.price}
                    </span>
                    <span className="pb-2 text-stone-500">/mes</span>
                  </div>

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
                Estás por activar <strong>{selectedPlan.toUpperCase()}</strong>. Elegí el medio
                de pago que prefieras.
              </p>

              <div className="mt-5 space-y-3">
                {providers.map((provider) => (
                  <button
                    key={provider.name}
                    type="button"
                    onClick={() => handleUpgrade(provider.name.toLowerCase())}
                    disabled={!paidPlans.some((plan) => plan.id === selectedPlan)}
                    className={`${provider.color} flex w-full items-center justify-between rounded-2xl px-4 py-3 font-medium text-white hover:opacity-90 disabled:opacity-60`}
                  >
                    <span className="inline-flex items-center gap-2">
                      <provider.icon size={18} />
                      {provider.name}
                    </span>
                    <span className="text-sm opacity-80">Continuar</span>
                  </button>
                ))}
              </div>
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
          </div>
        </section>
      </div>
    </div>
  );
}
