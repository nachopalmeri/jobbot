import { ReactNode } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";

import PublicFooterLinks from "@/components/PublicFooterLinks";

interface AuthSplitLayoutProps {
  eyebrow: string;
  title: string;
  description: string;
  highlights: string[];
  asideEyebrow: string;
  asideTitle: string;
  asideDescription: string;
  children: ReactNode;
  secondaryCta?: {
    href: string;
    label: string;
  };
}

export default function AuthSplitLayout({
  eyebrow,
  title,
  description,
  highlights,
  asideEyebrow,
  asideTitle,
  asideDescription,
  children,
  secondaryCta,
}: AuthSplitLayoutProps) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.1),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(217,119,6,0.14),_transparent_24%),linear-gradient(180deg,_#fafaf9,_#f5f5f4_36%,_#ffffff)] px-4 py-10 text-stone-950 lg:px-6 lg:py-14">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="rounded-[2rem] border border-stone-200 bg-white/92 p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-600">
            {eyebrow}
          </p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-stone-950">
            {title}
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-stone-600 lg:text-base">
            {description}
          </p>

          <div className="mt-7 grid gap-3 sm:grid-cols-2">
            {highlights.map((item) => (
              <div
                key={item}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-4 text-sm leading-6 text-stone-700"
              >
                {item}
              </div>
            ))}
          </div>

          {secondaryCta ? (
            <Link
              href={secondaryCta.href}
              className="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-700"
            >
              {secondaryCta.label}
              <ArrowRight size={16} />
            </Link>
          ) : null}
        </section>

        <section className="rounded-[2rem] border border-stone-200 bg-[linear-gradient(180deg,_rgba(255,255,255,0.96),_rgba(250,250,249,0.92))] p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-600">
            {asideEyebrow}
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-stone-950">
            {asideTitle}
          </h2>
          <p className="mt-3 text-sm leading-7 text-stone-600">{asideDescription}</p>

          <div className="mt-6 rounded-[1.7rem] border border-stone-200 bg-white p-6 shadow-sm">
            {children}
          </div>

          <div className="mt-6 rounded-[1.5rem] border border-indigo-100 bg-indigo-50 p-5">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-white p-2 text-indigo-600 shadow-sm">
                <CheckCircle2 size={18} />
              </div>
              <div>
                <p className="text-sm font-semibold text-indigo-950">
                  Todo queda conectado al mismo flujo
                </p>
                <p className="mt-1 text-sm leading-6 text-indigo-900/80">
                  El acceso web, el pipeline, las búsquedas y la CV Suite comparten la misma cuenta.
                </p>
              </div>
            </div>
          </div>

          <PublicFooterLinks tone="light" />
        </section>
      </div>
    </div>
  );
}
