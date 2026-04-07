import Link from "next/link";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  FileText,
  MessageSquareShare,
  Search,
  Sparkles,
  Target,
} from "lucide-react";

const featureSteps = [
  {
    title: "Descubri oportunidades con criterio",
    body: "Busca vacantes, filtralas por match y guarda solo las que de verdad vale la pena trabajar.",
    icon: Search,
  },
  {
    title: "Mejora tu CV antes de aplicar",
    body: "Subi tu CV, mira el score, detecta keywords faltantes y ajusta el perfil segun cada vacante.",
    icon: FileText,
  },
  {
    title: "Conecta Telegram cuando quieras",
    body: "Recibi alertas, genera tu codigo y vincula tu cuenta sin depender del bot para empezar.",
    icon: MessageSquareShare,
  },
];

const plans = [
  {
    name: "Free",
    price: "USD 0",
    description: "Para explorar el producto y ordenar tu busqueda.",
    features: ["Dashboard base", "Scanner CV basico", "Busqueda limitada"],
  },
  {
    name: "Pro",
    price: "USD 9.99",
    description: "Para usar JobBot todos los dias con mas profundidad.",
    features: ["Mas analisis de CV", "Mas matches", "Seguimiento mas fuerte"],
    featured: true,
  },
  {
    name: "Premium",
    price: "USD 19.99",
    description: "Para desbloquear la capa completa de CV Intelligence.",
    features: ["Mock interviews", "Cover letters", "Historial y prioridad"],
  },
];

const highlights = [
  "CV score y mejoras accionables",
  "Matches de empleo y busqueda guiada",
  "Meta semanal, racha y motivacion diaria",
  "Conexion opcional con Telegram",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,_#fafaf9_0%,_#f5f5f4_42%,_#ffffff_100%)] text-stone-950">
      <nav className="sticky top-0 z-30 border-b border-stone-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="rounded-2xl bg-indigo-600 p-2 text-white">
              <Bot size={18} />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-indigo-600">
                JobBot AR
              </p>
              <p className="text-sm text-stone-500">Asistente para conseguir trabajo</p>
            </div>
          </Link>

          <div className="hidden items-center gap-6 text-sm font-medium text-stone-600 md:flex">
            <a href="#como-funciona" className="hover:text-stone-950">
              Como funciona
            </a>
            <a href="#dashboard" className="hover:text-stone-950">
              Dashboard
            </a>
            <a href="#pricing" className="hover:text-stone-950">
              Pricing
            </a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:border-stone-400 hover:text-stone-950"
            >
              Iniciar sesion
            </Link>
            <Link
              href="/register"
              className="rounded-full bg-stone-950 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-800"
            >
              Empezar gratis
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto grid max-w-7xl gap-10 px-6 pb-16 pt-14 lg:grid-cols-[1.08fr_0.92fr] lg:pt-20">
        <div className="max-w-3xl">
          <p className="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-indigo-700">
            Busqueda laboral con foco
          </p>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight text-stone-950 md:text-6xl">
            Tu asistente para conseguir trabajo sin quemarte.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600">
            JobBot ordena tu busqueda en un solo lugar: dashboard, CV score, mejoras,
            matches, tips, motivacion diaria y conexion con Telegram cuando vos quieras.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700"
            >
              Crear cuenta gratis
              <ArrowRight size={16} />
            </Link>
            <a
              href="#dashboard"
              className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 font-semibold text-stone-800 hover:border-stone-400"
            >
              Ver el producto
            </a>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-2">
            {highlights.map((item) => (
              <div
                key={item}
                className="rounded-[1.4rem] border border-stone-200 bg-white/85 px-4 py-4 text-sm text-stone-700 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-full bg-emerald-100 p-1 text-emerald-700">
                    <CheckCircle2 size={14} />
                  </div>
                  <p>{item}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-x-10 top-8 h-40 rounded-full bg-indigo-200/60 blur-3xl" />
          <div className="relative overflow-hidden rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_24px_80px_rgba(28,25,23,0.10)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
                  Dashboard preview
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                  Menos ruido, mas avance
                </h2>
              </div>
              <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Telegram opcional
              </div>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <article className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-4">
                <p className="text-sm text-stone-500">CV rating</p>
                <p className="mt-2 text-4xl font-semibold text-stone-950">82</p>
                <p className="mt-2 text-sm text-stone-600">
                  Keywords fuertes, experiencia clara y 3 mejoras recomendadas.
                </p>
              </article>
              <article className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-4">
                <p className="text-sm text-stone-500">Meta semanal</p>
                <p className="mt-2 text-4xl font-semibold text-stone-950">5 / 8</p>
                <p className="mt-2 text-sm text-stone-600">
                  Tu racha sigue viva. Faltan 3 postulaciones esta semana.
                </p>
              </article>
            </div>

            <div className="mt-4 rounded-[1.5rem] border border-indigo-100 bg-[linear-gradient(135deg,_#eef2ff,_#fff7ed)] p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-stone-500">Oportunidad destacada</p>
                  <p className="mt-1 text-lg font-semibold text-stone-950">
                    Product Designer - Remote LATAM
                  </p>
                  <p className="mt-1 text-sm text-stone-600">
                    Match 91% · CV listo para aplicar · seguimiento desde dashboard
                  </p>
                </div>
                <div className="rounded-full bg-white px-3 py-1 text-sm font-semibold text-indigo-700 shadow-sm">
                  91%
                </div>
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-[1.35rem] border border-stone-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
                  Tips
                </p>
                <p className="mt-2 text-sm text-stone-700">
                  Mejora el titular del CV para que el match sea mas alto.
                </p>
              </div>
              <div className="rounded-[1.35rem] border border-stone-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
                  Matches
                </p>
                <p className="mt-2 text-sm text-stone-700">
                  12 vacantes filtradas y 3 listas para aplicar hoy.
                </p>
              </div>
              <div className="rounded-[1.35rem] border border-stone-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
                  Plan
                </p>
                <p className="mt-2 text-sm text-stone-700">
                  Free arranca simple. Premium desbloquea la suite completa.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="como-funciona" className="mx-auto max-w-7xl px-6 pb-16">
        <div className="rounded-[2rem] border border-stone-200 bg-white/90 p-8 shadow-sm">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
              Como funciona
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
              Un sistema claro para buscar, mejorar y aplicar mejor.
            </h2>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-3">
            {featureSteps.map((step) => (
              <article
                key={step.title}
                className="rounded-[1.7rem] border border-stone-200 bg-stone-50 p-5"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-indigo-700 shadow-sm">
                  <step.icon size={22} />
                </div>
                <h3 className="mt-5 text-xl font-semibold text-stone-950">{step.title}</h3>
                <p className="mt-3 text-sm leading-7 text-stone-600">{step.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="dashboard" className="mx-auto max-w-7xl px-6 pb-16">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,_#fff7ed,_#ffffff)] p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
              Lo que ves adentro
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-stone-950">
              Dashboard simple para usar todos los dias
            </h2>
            <p className="mt-4 text-base leading-7 text-stone-600">
              El home no te vende nada. Te muestra tu meta semanal, tus matches, tu progreso,
              tus mejoras de CV y el estado de tu conexion con Telegram.
            </p>

            <div className="mt-6 space-y-3">
              <div className="rounded-[1.35rem] border border-stone-200 bg-white px-4 py-4 text-sm text-stone-700">
                Dashboard con meta semanal, racha y motivacion diaria.
              </div>
              <div className="rounded-[1.35rem] border border-stone-200 bg-white px-4 py-4 text-sm text-stone-700">
                CV Suite con rating, insights, mejoras y gating por plan.
              </div>
              <div className="rounded-[1.35rem] border border-stone-200 bg-white px-4 py-4 text-sm text-stone-700">
                Busqueda, pipeline y configuracion conectados al mismo usuario.
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-8 shadow-sm">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 p-4">
                <Target className="text-indigo-700" size={18} />
                <p className="mt-3 text-sm text-stone-500">Meta semanal</p>
                <p className="mt-2 text-2xl font-semibold text-stone-950">8 aplicaciones</p>
              </div>
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 p-4">
                <Sparkles className="text-indigo-700" size={18} />
                <p className="mt-3 text-sm text-stone-500">Motivacion diaria</p>
                <p className="mt-2 text-sm font-medium leading-6 text-stone-800">
                  La constancia gana cuando el mercado parece lento.
                </p>
              </div>
              <div className="rounded-[1.4rem] border border-stone-200 bg-stone-50 p-4">
                <MessageSquareShare className="text-indigo-700" size={18} />
                <p className="mt-3 text-sm text-stone-500">Telegram</p>
                <p className="mt-2 text-sm font-medium text-stone-800">
                  Vincula tu cuenta y recibe alertas cuando quieras.
                </p>
              </div>
            </div>

            <div className="mt-6 rounded-[1.6rem] border border-stone-200 bg-white p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-stone-500">Pipeline</p>
                  <h3 className="mt-1 text-xl font-semibold text-stone-950">
                    Todo el seguimiento en un solo lugar
                  </h3>
                </div>
                <Link
                  href="/dashboard"
                  className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:border-stone-400 hover:text-stone-950"
                >
                  Ver dashboard
                </Link>
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-700">
                    Aplicado
                  </p>
                  <p className="mt-2 text-sm text-stone-700">3 vacantes activas</p>
                </div>
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">
                    Entrevista
                  </p>
                  <p className="mt-2 text-sm text-stone-700">1 proceso avanzado</p>
                </div>
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                    Oferta
                  </p>
                  <p className="mt-2 text-sm text-stone-700">Tu embudo claro y accionable</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-7xl px-6 pb-20">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
              Pricing
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
              Empeza simple y desbloquea mas cuando de verdad lo necesites.
            </h2>
          </div>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-full bg-stone-950 px-5 py-3 font-semibold text-white hover:bg-stone-800"
          >
            Probar JobBot
            <ArrowRight size={16} />
          </Link>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => (
            <article
              key={plan.name}
              className={`rounded-[2rem] border p-6 shadow-sm ${
                plan.featured
                  ? "border-indigo-300 bg-[linear-gradient(180deg,_#eef2ff,_#ffffff)]"
                  : "border-stone-200 bg-white"
              }`}
            >
              <p className="text-sm font-medium text-stone-500">{plan.name}</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight text-stone-950">
                {plan.price}
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-600">{plan.description}</p>

              <div className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3 text-sm text-stone-700">
                    <div className="mt-0.5 rounded-full bg-emerald-100 p-1 text-emerald-700">
                      <CheckCircle2 size={14} />
                    </div>
                    <p>{feature}</p>
                  </div>
                ))}
              </div>

              <Link
                href={`/register?plan=${plan.name.toLowerCase()}`}
                className={`mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full px-4 py-3 text-sm font-semibold ${
                  plan.featured
                    ? "bg-indigo-600 text-white hover:bg-indigo-700"
                    : "border border-stone-300 text-stone-800 hover:border-stone-400"
                }`}
              >
                Elegir {plan.name}
              </Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
