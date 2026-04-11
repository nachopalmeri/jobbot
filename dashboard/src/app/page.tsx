import Link from "next/link";
import { ArrowRight, Bot, Briefcase, ShieldCheck, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.16),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(245,158,11,0.14),_transparent_22%),linear-gradient(180deg,_#0f172a,_#111827_38%,_#1c1917)] text-white">
      <section className="mx-auto flex max-w-7xl flex-col gap-12 px-6 py-10 lg:px-8 lg:py-16">
        <header className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-300">
              JobBot
            </p>
            <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight lg:text-6xl">
              El copiloto real para buscar trabajo tech en LATAM sin humo ni dashboards fake.
            </h1>
          </div>
          <div className="hidden rounded-full border border-white/10 bg-white/8 px-4 py-2 text-sm text-white/72 lg:block">
            Controlled launch beta
          </div>
        </header>

        <p className="max-w-3xl text-lg leading-8 text-white/72">
          JobBot unifica búsqueda, pipeline, CV intelligence y seguimiento desde una sola app.
          Sin promesas vacías: si algo todavía está en beta, se dice; si está disponible, se
          conecta con la plataforma real.
        </p>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-stone-100"
          >
            Crear cuenta
            <ArrowRight size={16} />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-full border border-white/14 px-5 py-3 text-sm font-semibold text-white hover:bg-white/8"
          >
            Iniciar sesión
          </Link>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            {
              icon: Briefcase,
              title: "Búsqueda guiada",
              body: "Resultados por perfil, modalidad y jornada, conectados al backend real.",
            },
            {
              icon: Sparkles,
              title: "CV Suite",
              body: "ATS, match, cover letters e historial con gating por plan real.",
            },
            {
              icon: Bot,
              title: "Bot + web",
              body: "Telegram sigue siendo un canal fuerte, pero no reemplaza a la app web.",
            },
            {
              icon: ShieldCheck,
              title: "Cuenta segura",
              body: "Sesión web por cookie httpOnly y permisos coherentes entre app, bot y admin.",
            },
          ].map((item) => (
            <article
              key={item.title}
              className="rounded-[1.75rem] border border-white/10 bg-white/6 p-5 shadow-2xl backdrop-blur-xl"
            >
              <item.icon size={18} className="text-amber-300" />
              <h2 className="mt-4 text-lg font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm leading-7 text-white/68">{item.body}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-6 rounded-[2rem] border border-white/10 bg-white/6 p-6 shadow-2xl backdrop-blur-xl lg:grid-cols-[1.15fr_0.85fr] lg:p-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-300">
              Qué podés hacer hoy
            </p>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-white/72">
              <li>Crear cuenta web y entrar al dashboard.</li>
              <li>Configurar preferencias y objetivo semanal.</li>
              <li>Subir CV, recibir insights y seguir postulaciones.</li>
              <li>Vincular Telegram si querés alertas y accesos asistidos.</li>
            </ul>
          </div>
          <div className="rounded-[1.75rem] border border-white/10 bg-black/18 p-5">
            <p className="text-sm font-semibold text-white">Estado del producto</p>
            <p className="mt-3 text-sm leading-7 text-white/68">
              Launch controlado. Dashboard, auth, suscripciones y panel admin viven sobre el
              contrato real de la API. Lo que siga en beta se documenta como beta, no como feature
              terminada.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}
