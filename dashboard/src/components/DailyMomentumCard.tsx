"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Sparkles } from "lucide-react";

const dailyQuotes = [
  "No hace falta aplicar a todo. Hace falta aplicar mejor.",
  "Cada ajuste fino en tu CV te acerca a una entrevista real.",
  "La constancia gana incluso cuando la motivacion baja.",
  "Un buen pipeline te da calma cuando el mercado mete ruido.",
  "Aplicar con foco vale mas que enviar veinte CVs a ciegas.",
  "Tu proximo si suele llegar despues de varios no. Segui.",
  "Hoy toca avanzar aunque sea un paso pequeno.",
];

export function DailyMomentumCard() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const quote = useMemo(() => dailyQuotes[now.getDay()], [now]);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Ritmo del Dia
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-950">
            {now.toLocaleTimeString("es-AR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </h2>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <CalendarDays size={16} />
            {now.toLocaleDateString("es-AR", {
              weekday: "long",
              day: "numeric",
              month: "long",
            })}
          </p>
        </div>

        <div className="rounded-2xl bg-slate-950 p-3 text-white shadow-sm">
          <Sparkles size={20} />
        </div>
      </div>

      <div className="mt-6 rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50 via-white to-amber-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-600">
          Frase Motivadora
        </p>
        <p className="mt-2 text-lg font-medium leading-7 text-slate-900">{quote}</p>
      </div>
    </div>
  );
}
