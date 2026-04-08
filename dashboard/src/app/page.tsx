import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  Bell,
  Bot,
  Brain,
  Briefcase,
  Check,
  FileText,
  Search,
  Sparkles,
  Target,
} from "lucide-react";

const heroStats = [
  { value: "247", label: "Empleos esta semana" },
  { value: "1,200+", label: "Usuarios activos" },
  { value: "15", label: "Portales monitoreados" },
];

const numbers = [
  {
    value: "67%",
    title: "de entrevistas son para los primeros postulantes",
    body: "Speed matters. JobBot te alerta cuando una oportunidad aparece.",
    featured: true,
  },
  {
    value: "40+",
    title: "alertas nuevas antes de que se pierdan",
    body: "Los usuarios con mejor ritmo ven muchas mas oportunidades reales.",
  },
  {
    value: "5x",
    title: "mas volumen con JobBot vs. busqueda manual",
    body: "JobBot ayuda a escalar sin vivir refrescando portales.",
  },
  {
    value: "Perdes",
    title: "oportunidades si todo depende de busqueda manual",
    body: "Mas tiempo perdido, menos foco y menos consistencia en el proceso.",
    warning: true,
  },
];

const useCases = [
  {
    title: "Escaneo masivo automatico",
    body: "JobBot busca en multiples fuentes, filtra por criterio y te devuelve oportunidades usables.",
    href: "/dashboard/buscar",
    link: "Ver volumen",
    icon: Search,
  },
  {
    title: "Filtro inteligente de volumen",
    body: "No aplicas a todo: priorizas por match, senales de calidad y enfoque.",
    href: "/dashboard/configuracion",
    link: "Ver como filtra",
    icon: Brain,
  },
  {
    title: "Personalizacion de CVs",
    body: "Subis tu CV, ves score, mejoras, keywords faltantes y adaptas mejor tu perfil.",
    href: "/dashboard/cv",
    link: "Probar ahora",
    icon: FileText,
  },
  {
    title: "Alertas inteligentes",
    body: "Recibi avisos cuando aparece algo que vale la pena y conecta Telegram si queres.",
    href: "/dashboard/configuracion",
    link: "Configurar alertas",
    icon: Bell,
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "/mes",
    description: "Para empezar a explorar",
    features: [
      "3 busquedas guiadas por dia",
      "Hasta 3 resultados visibles por busqueda",
      "Dashboard liviano",
      "Score ATS inicial de CV",
      "Sin pipeline completo",
      "Sin mock interviews",
    ],
    cta: "Empezar gratis",
    href: "/register",
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/mes",
    description: "Para quienes ya buscan con intencion",
    note: "o plan anual con ahorro",
    features: [
      "Mas busquedas y resultados completos",
      "Analisis IA de CV",
      "Match score y keywords faltantes",
      "Alertas por Telegram",
      "Pipeline completo",
      "Sin mock interviews premium",
    ],
    cta: "Obtener Pro",
    href: "/dashboard/suscripcion",
    featured: true,
    footer: "El mejor equilibrio entre volumen, tracker y CV Suite.",
  },
  {
    name: "Premium",
    price: "$19.99",
    period: "/mes",
    description: "La capa completa de CV Intelligence",
    note: "o plan anual con ahorro",
    features: [
      "Todo lo de Pro",
      "Mas analisis IA de CV",
      "Mock interviews",
      "Cover letters personalizadas",
      "Historial completo",
      "Mayor volumen operativo",
    ],
    cta: "Obtener Premium",
    href: "/dashboard/suscripcion",
    footer: "Tambien podes usar creditos si solo queres CV Suite bajo demanda.",
  },
];

const comparison = [
  ["Ritmo de busqueda", "Irregular", "Constante y medible"],
  ["Decision de que aplicar", "Difusa", "Mas guiada por match"],
  ["Seguimiento", "Notas sueltas", "Pipeline y alertas"],
  ["Mejora del CV", "Esporadica", "ATS, match y feedback"],
];

const previewColumns = [
  {
    label: "Busqueda",
    value: "24",
    note: "nuevos empleos",
  },
  {
    label: "Postulaciones",
    value: "8",
    note: "en seguimiento",
  },
  {
    label: "Entrevistas",
    value: "3",
    note: "en juego",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,_#fafaf9_0%,_#f5f5f4_45%,_#ffffff_100%)] text-stone-950">
      <nav className="sticky top-0 z-30 border-b border-stone-200/80 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-sm">
              J
            </div>
            <span className="font-semibold tracking-tight text-stone-950">JobBot AR</span>
          </Link>

          <div className="hidden items-center gap-6 text-sm font-medium text-stone-600 md:flex">
            <a href="#como-funciona" className="hover:text-stone-950">
              Como funciona
            </a>
            <a href="#dash" className="hover:text-stone-950">
              Tu panel
            </a>
            <a href="#demo" className="hover:text-stone-950">
              Demo
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
              className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(79,70,229,0.18),transparent_28%),radial-gradient(circle_at_80%_16%,rgba(217,119,6,0.14),transparent_24%)]" />
        <div className="mx-auto grid max-w-7xl gap-12 px-6 pb-18 pt-18 lg:grid-cols-[1.02fr_0.98fr] lg:pb-24 lg:pt-24">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-3 rounded-full border border-indigo-200 bg-white/85 px-4 py-2 text-sm text-stone-700 shadow-sm">
              <span className="rounded-full bg-indigo-600 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-white">
                Nuevo
              </span>
              <span>La forma inteligente de buscar trabajo en Argentina</span>
            </div>

            <h1 className="mt-6 text-5xl font-semibold tracking-tight text-stone-950 md:text-7xl">
              <span className="block">Encontra.</span>
              <span className="block">Postula.</span>
              <span className="block text-indigo-600">Triunfa.</span>
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600">
              JobBot escanea portales de empleo por vos, filtra con IA segun tu perfil
              y te avisa solo de las oportunidades que realmente valen la pena.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-5 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700"
              >
                Empezar gratis
                <ArrowRight size={16} />
              </Link>
              <a
                href="#como-funciona"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 font-semibold text-stone-800 hover:border-stone-400"
              >
                Ver como funciona
              </a>
            </div>

            <div className="mt-10 flex flex-wrap gap-6">
              {heroStats.map((stat) => (
                <div key={stat.label} className="min-w-[130px]">
                  <p className="text-3xl font-semibold tracking-tight text-stone-950">
                    {stat.value}
                  </p>
                  <p className="mt-1 text-sm text-stone-500">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="relative z-10">
            <div className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_24px_80px_rgba(28,25,23,0.10)]">
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <span className="h-3 w-3 rounded-full bg-rose-400" />
                  <span className="h-3 w-3 rounded-full bg-amber-400" />
                  <span className="h-3 w-3 rounded-full bg-emerald-400" />
                </div>
                <p className="text-sm text-stone-500">dashboard.jobbot</p>
              </div>

              <div className="mt-6 rounded-[1.6rem] border border-stone-200 bg-stone-50 p-5">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-sm font-semibold text-white">
                      MN
                    </div>
                    <div>
                      <p className="font-semibold text-stone-950">Maria Nunez</p>
                      <p className="text-sm text-stone-500">Frontend Developer</p>
                    </div>
                  </div>
                  <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                    Buscando activamente
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {previewColumns.map((item) => (
                    <div
                      key={item.label}
                      className="rounded-[1.3rem] border border-stone-200 bg-white p-4"
                    >
                      <p className="text-3xl font-semibold text-stone-950">{item.value}</p>
                      <p className="mt-1 text-sm font-medium text-stone-700">{item.label}</p>
                      <p className="mt-1 text-xs text-stone-500">{item.note}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-5 space-y-3">
                  {[
                    ["92%", "Senior Frontend Developer", "TechFlow · Remoto · $2,400 USD"],
                    ["87%", "Full Stack Engineer", "DataViz Labs · Hibrido · $2,800 USD"],
                    ["76%", "React Developer", "Innovate Corp · Remoto · $2,200 USD"],
                  ].map(([match, title, meta]) => (
                    <div
                      key={title}
                      className="flex items-center justify-between gap-4 rounded-[1.3rem] border border-stone-200 bg-white px-4 py-4"
                    >
                      <div>
                        <p className="font-semibold text-stone-950">{title}</p>
                        <p className="text-sm text-stone-500">{meta}</p>
                      </div>
                      <div className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">
                        {match}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800">
                <Sparkles size={16} />
                3 nuevas oportunidades hoy
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-18">
        <div className="rounded-[2rem] border border-stone-200 bg-white/85 p-8 shadow-sm">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold text-amber-700">Sabias que...</p>
            <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
              En el mercado laboral, el que aplica mas, gana mas
            </h2>
            <p className="mt-4 text-base leading-7 text-stone-600">
              El volumen no garantiza trabajo, pero sin volumen no hay trabajo. JobBot
              te da la ventaja del volumen sin el esfuerzo del volumen.
            </p>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-4">
            {numbers.map((item) => (
              <article
                key={item.title}
                className={`rounded-[1.7rem] border p-5 ${
                  item.featured
                    ? "border-indigo-200 bg-indigo-50"
                    : item.warning
                      ? "border-rose-200 bg-rose-50"
                      : "border-stone-200 bg-stone-50"
                }`}
              >
                <p className="text-4xl font-semibold tracking-tight text-stone-950">{item.value}</p>
                <h3 className="mt-3 text-lg font-semibold text-stone-950">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-stone-600">{item.body}</p>
              </article>
            ))}
          </div>

          <div className="mt-8 rounded-[1.7rem] border border-stone-200 bg-[linear-gradient(135deg,_#eef2ff,_#fff7ed)] p-6">
            <p className="text-lg font-medium text-stone-900">
              "Cada dia que no usas JobBot, oportunidades pasan de largo"
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700"
              >
                Empezar a multiplicar mis chances
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section id="use-cases" className="mx-auto max-w-7xl px-6 pb-18">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-500">
            Que podes construir
          </p>
          <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
            Desde la busqueda hasta la oferta
          </h2>
          <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-stone-600">
            JobBot te acompana en cada etapa con herramientas pensadas para resultados.
          </p>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {useCases.map((item) => (
            <article
              key={item.title}
              className="rounded-[1.8rem] border border-stone-200 bg-white p-6 shadow-sm"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700">
                <item.icon size={24} />
              </div>
              <h3 className="mt-5 text-xl font-semibold text-stone-950">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-stone-600">{item.body}</p>
              <Link
                href={item.href}
                className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-indigo-700 hover:text-indigo-800"
              >
                {item.link}
                <ArrowRight size={15} />
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section id="precios" className="mx-auto max-w-7xl px-6 pb-18">
        <div className="text-center">
          <p className="text-sm font-semibold text-indigo-700">Pricing</p>
          <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
            Elegi tu plan
          </h2>
          <p className="mt-4 text-base text-stone-600">
            Empeza gratis y escala cuando quieras. Sin compromisos.
          </p>
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
              <div
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                  plan.featured
                    ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                    : "border-stone-200 bg-stone-50 text-stone-600"
                }`}
              >
                {plan.featured ? "Mas popular" : plan.name}
              </div>
              <div className="mt-5 flex items-end gap-1">
                <span className="text-4xl font-semibold tracking-tight text-stone-950">
                  {plan.price}
                </span>
                <span className="pb-1 text-sm text-stone-500">{plan.period}</span>
              </div>
              {plan.note ? <p className="mt-2 text-sm text-stone-500">{plan.note}</p> : null}
              <p className="mt-3 text-sm leading-7 text-stone-600">{plan.description}</p>

              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm text-stone-700">
                    {feature.startsWith("Sin") ? (
                      <AlertCircle size={16} className="mt-0.5 text-stone-400" />
                    ) : (
                      <Check size={16} className="mt-0.5 text-emerald-600" />
                    )}
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`mt-6 inline-flex w-full items-center justify-center rounded-full px-4 py-3 text-sm font-semibold ${
                  plan.featured
                    ? "bg-indigo-600 text-white hover:bg-indigo-700"
                    : "border border-stone-300 text-stone-800 hover:border-stone-400"
                }`}
              >
                {plan.cta}
              </Link>

              {plan.footer ? (
                <p className="mt-4 text-sm leading-6 text-stone-500">{plan.footer}</p>
              ) : null}
            </article>
          ))}
        </div>

        <div className="mt-8 rounded-[2rem] border border-stone-200 bg-white p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-stone-950">
            Que cambia cuando dejas de buscar en modo manual
          </h3>
          <div className="mt-5 overflow-hidden rounded-[1.4rem] border border-stone-200">
            <div className="grid grid-cols-3 bg-stone-100 px-4 py-3 text-sm font-semibold text-stone-700">
              <span></span>
              <span>Busqueda manual</span>
              <span className="text-indigo-700">Con JobBot</span>
            </div>
            {comparison.map(([topic, manual, withJobbot]) => (
              <div
                key={topic}
                className="grid grid-cols-3 border-t border-stone-200 px-4 py-3 text-sm text-stone-700"
              >
                <span className="font-medium text-stone-900">{topic}</span>
                <span>{manual}</span>
                <span className="font-medium text-indigo-700">{withJobbot}</span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-stone-500">
            El objetivo no es prometer magia: es ordenar mejor tu proceso y ayudarte a
            aplicar con mas criterio.
          </p>
        </div>
      </section>

      <section id="como-funciona" className="mx-auto max-w-7xl px-6 pb-18">
        <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
          <div className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,_#fafaf9,_#fff7ed)] p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-amber-700">
              Como funciona
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
              De la busqueda a la oferta en pasos claros
            </h2>
            <div className="mt-8 space-y-4">
              {[
                ["01", "Escaneo 24/7", "JobBot revisa fuentes y te acerca oportunidades."],
                ["02", "Match inteligente", "Subis tu CV y priorizas mejor que aplicar."],
                ["03", "Seguimiento", "Pipeline, alertas y mejoras para sostener el proceso."],
              ].map(([n, title, body]) => (
                <div key={title} className="rounded-[1.4rem] border border-stone-200 bg-white p-5">
                  <p className="text-sm font-semibold text-indigo-600">{n}</p>
                  <h3 className="mt-2 text-xl font-semibold text-stone-950">{title}</h3>
                  <p className="mt-2 text-sm leading-7 text-stone-600">{body}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-stone-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-500">
              Features reales
            </p>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {[
                ["Match inteligente con tu CV", "Subis tu CV y ves que tan alineada esta cada vacante."],
                ["Pipeline de postulaciones", "Organizas el seguimiento sin notas sueltas."],
                ["Motivacion diaria y meta semanal", "El dashboard te da foco y continuidad."],
                ["Conexion con Telegram", "Canal opcional para alertas y linking."],
              ].map(([title, body]) => (
                <div key={title} className="rounded-[1.4rem] border border-stone-200 bg-stone-50 p-5">
                  <h3 className="text-lg font-semibold text-stone-950">{title}</h3>
                  <p className="mt-3 text-sm leading-7 text-stone-600">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="demo" className="mx-auto max-w-7xl px-6 pb-18">
        <div className="rounded-[2rem] border border-stone-200 bg-white p-8 shadow-sm">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
                Demo
              </p>
              <h2 className="mt-3 text-3xl font-semibold text-stone-950 md:text-4xl">
                Mira como se ve el producto por dentro
              </h2>
              <p className="mt-4 text-base leading-7 text-stone-600">
                Dashboard, CV Suite, progreso semanal, recomendaciones y gating por plan.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-full bg-stone-950 px-5 py-3 font-semibold text-white hover:bg-stone-800"
              >
                Acceder a mi Dashboard
                <ArrowRight size={16} />
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 font-semibold text-stone-800 hover:border-stone-400"
              >
                Crear cuenta
              </Link>
            </div>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="rounded-[1.8rem] border border-stone-200 bg-stone-50 p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-stone-500">Dashboard</p>
                  <h3 className="mt-1 text-2xl font-semibold text-stone-950">
                    Hoy toca foco: una busqueda buena, una mejora de CV y una postulacion solida.
                  </h3>
                </div>
                <div className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">
                  Premium
                </div>
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-[1.3rem] border border-stone-200 bg-white p-4">
                  <p className="text-sm text-stone-500">CV rating</p>
                  <p className="mt-2 text-3xl font-semibold text-stone-950">82</p>
                </div>
                <div className="rounded-[1.3rem] border border-stone-200 bg-white p-4">
                  <p className="text-sm text-stone-500">Meta semanal</p>
                  <p className="mt-2 text-3xl font-semibold text-stone-950">5/8</p>
                </div>
                <div className="rounded-[1.3rem] border border-stone-200 bg-white p-4">
                  <p className="text-sm text-stone-500">Telegram</p>
                  <p className="mt-2 text-sm font-semibold text-stone-950">Conectado</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-[1.6rem] border border-stone-200 bg-[linear-gradient(135deg,_#eef2ff,_#ffffff)] p-5">
                <div className="flex items-center gap-3">
                  <Target className="text-indigo-700" size={20} />
                  <div>
                    <p className="font-semibold text-stone-950">Meta semanal</p>
                    <p className="text-sm text-stone-600">Todavia te quedan 3 aplicaciones.</p>
                  </div>
                </div>
              </div>
              <div className="rounded-[1.6rem] border border-stone-200 bg-[linear-gradient(135deg,_#fff7ed,_#ffffff)] p-5">
                <div className="flex items-center gap-3">
                  <Briefcase className="text-amber-700" size={20} />
                  <div>
                    <p className="font-semibold text-stone-950">Matches</p>
                    <p className="text-sm text-stone-600">3 oportunidades listas para mover hoy.</p>
                  </div>
                </div>
              </div>
              <div className="rounded-[1.6rem] border border-stone-200 bg-[linear-gradient(135deg,_#ecfdf5,_#ffffff)] p-5">
                <div className="flex items-center gap-3">
                  <Bot className="text-emerald-700" size={20} />
                  <div>
                    <p className="font-semibold text-stone-950">Bot conectado</p>
                    <p className="text-sm text-stone-600">Tu cuenta web y Telegram comparten el mismo estado.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="dash" className="mx-auto max-w-7xl px-6 pb-20">
        <div className="rounded-[2rem] border border-stone-200 bg-stone-950 p-8 text-white shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-300">
            Tu panel
          </p>
          <h2 className="mt-3 text-3xl font-semibold md:text-4xl">
            Dashboard, CV Suite y tracking en un solo lugar
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-7 text-stone-300">
            Tambien podes escribir al bot o entrar desde web: la idea es una sola cuenta,
            un solo flujo y un producto que te acompane de punta a punta.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 font-semibold text-stone-950 hover:bg-stone-100"
            >
              Entrar al dashboard
              <ArrowRight size={16} />
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-3 font-semibold text-white hover:bg-white/5"
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
