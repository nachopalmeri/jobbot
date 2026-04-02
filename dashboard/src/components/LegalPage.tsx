import Link from "next/link";

import PublicFooterLinks from "@/components/PublicFooterLinks";

export default function LegalPage({
  eyebrow,
  title,
  intro,
  sections,
}: {
  eyebrow: string;
  title: string;
  intro: string;
  sections: Array<{ title: string; content: string[] }>;
}) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.08),_transparent_28%),linear-gradient(180deg,_#fcfbf7,_#ffffff)] px-6 py-12">
      <div className="mx-auto max-w-4xl">
        <Link
          href="/login"
          className="inline-flex items-center rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-700 hover:text-stone-950"
        >
          Volver a JobBot
        </Link>

        <section className="mt-6 rounded-[2rem] border border-stone-200 bg-white/90 p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-indigo-600">
            {eyebrow}
          </p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-stone-950">{title}</h1>
          <p className="mt-4 text-base leading-7 text-stone-600">{intro}</p>

          <div className="mt-10 space-y-8">
            {sections.map((section) => (
              <section key={section.title}>
                <h2 className="text-xl font-semibold text-stone-950">{section.title}</h2>
                <div className="mt-3 space-y-3 text-sm leading-7 text-stone-600">
                  {section.content.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                </div>
              </section>
            ))}
          </div>

          <PublicFooterLinks tone="light" />
        </section>
      </div>
    </main>
  );
}
