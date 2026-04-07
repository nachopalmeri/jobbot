import Link from "next/link"

const features = [
  "Rating y mejoras de CV con IA",
  "Matches de empleo según tu perfil",
  "Tips accionables y motivación diaria",
  "Objetivo semanal y racha de postulaciones",
  "Conexión opcional con Telegram",
]

const plans = [
  { name: "Free", price: "USD 0", note: "Exploración inicial" },
  { name: "Pro", price: "USD 9.99", note: "Más análisis y seguimiento" },
  { name: "Premium", price: "USD 19.99", note: "Suite completa y prioridad" },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-stone-950 text-stone-100">
      <section className="mx-auto max-w-6xl px-6 pb-12 pt-16 md:pt-20">
        <p className="mb-4 inline-flex rounded-full border border-emerald-400/40 bg-emerald-400/10 px-3 py-1 text-xs font-semibold tracking-wide text-emerald-300">
          JobBot · Landing oficial
        </p>
        <h1 className="max-w-4xl text-4xl font-black leading-tight md:text-6xl">
          Conseguí trabajo con un sistema real, no con caos.
        </h1>
        <p className="mt-5 max-w-3xl text-base text-stone-300 md:text-lg">
          JobBot unifica tu búsqueda laboral: dashboard, CV intelligence, seguimiento de aplicaciones y conexión con Telegram cuando vos quieras.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/register"
            className="rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-stone-950 transition hover:bg-emerald-300"
          >
            Crear cuenta gratis
          </Link>
          <Link
            href="/login"
            className="rounded-xl border border-stone-700 px-5 py-3 font-semibold text-stone-100 transition hover:border-stone-500 hover:bg-stone-900"
          >
            Ya tengo cuenta
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 pb-14 md:grid-cols-2">
        {features.map((item) => (
          <article key={item} className="rounded-2xl border border-stone-800 bg-stone-900/70 p-5">
            <p className="text-sm text-stone-200">{item}</p>
          </article>
        ))}
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="text-2xl font-bold md:text-3xl">Planes</h2>
        <p className="mt-2 text-stone-400">Elegí el nivel que mejor se adapte a tu ritmo.</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.name} className="rounded-2xl border border-stone-800 bg-stone-900 p-5">
              <p className="text-sm text-stone-400">{plan.name}</p>
              <p className="mt-2 text-3xl font-extrabold">{plan.price}</p>
              <p className="mt-2 text-sm text-stone-300">{plan.note}</p>
              <Link
                href={`/register?plan=${plan.name.toLowerCase()}`}
                className="mt-4 inline-block rounded-lg bg-stone-100 px-4 py-2 text-sm font-semibold text-stone-950 hover:bg-white"
              >
                Empezar con {plan.name}
              </Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
