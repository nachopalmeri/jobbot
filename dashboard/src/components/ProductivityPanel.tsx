"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock3, Pause, Play, Quote, RotateCcw, TimerReset, Trophy } from "lucide-react";

import { buildGoalMessage, getDailyQuote } from "@/lib/dashboard";

interface ProductivityPanelProps {
  weeklyApplied: number;
  weeklyGoal: number;
}

const presetDurations = [15, 25, 45, 60];

export default function ProductivityPanel({
  weeklyApplied,
  weeklyGoal,
}: ProductivityPanelProps) {
  const [now, setNow] = useState(() => new Date());
  const [duration, setDuration] = useState(25);
  const [remainingSeconds, setRemainingSeconds] = useState(25 * 60);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const clock = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(clock);
  }, []);

  useEffect(() => {
    if (!running) {
      return;
    }

    const timer = window.setInterval(() => {
      setRemainingSeconds((current) => {
        if (current <= 1) {
          window.clearInterval(timer);
          setRunning(false);
          return 0;
        }
        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [running]);

  const percent = useMemo(() => {
    if (weeklyGoal <= 0) {
      return 0;
    }

    return Math.min(100, Math.round((weeklyApplied / weeklyGoal) * 100));
  }, [weeklyApplied, weeklyGoal]);

  const minutes = String(Math.floor(remainingSeconds / 60)).padStart(2, "0");
  const seconds = String(remainingSeconds % 60).padStart(2, "0");

  return (
    <aside className="space-y-5">
      <section className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-slate-900 p-3 text-white">
            <Clock3 size={20} />
          </div>
          <div>
            <p className="text-sm font-medium text-stone-500">Fecha y hora</p>
            <p className="text-xl font-semibold text-stone-950">
              {now.toLocaleTimeString("es-AR", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </p>
          </div>
        </div>
        <p className="mt-4 text-sm text-stone-600">
          {now.toLocaleDateString("es-AR", {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}
        </p>
      </section>

      <section className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <div className="rounded-2xl bg-amber-100 p-3 text-amber-700">
            <Trophy size={20} />
          </div>
          <div>
            <p className="text-sm font-medium text-stone-500">Objetivo semanal</p>
            <p className="text-xl font-semibold text-stone-950">
              {weeklyApplied}/{weeklyGoal || 0}
            </p>
          </div>
        </div>

        <div className="h-3 overflow-hidden rounded-full bg-stone-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-indigo-500 to-amber-500"
            style={{ width: `${percent}%` }}
          />
        </div>

        <p className="mt-4 text-sm leading-6 text-stone-600">
          {buildGoalMessage(weeklyApplied, weeklyGoal)}
        </p>
      </section>

      <section className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <div className="rounded-2xl bg-indigo-100 p-3 text-indigo-700">
            <Quote size={20} />
          </div>
          <div>
            <p className="text-sm font-medium text-stone-500">Frase del día</p>
            <p className="text-xl font-semibold text-stone-950">Mantener ritmo</p>
          </div>
        </div>
        <p className="text-sm leading-7 text-stone-700">“{getDailyQuote(now)}”</p>
      </section>

      <section className="rounded-[28px] border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <div className="rounded-2xl bg-white/10 p-3 text-white">
            <TimerReset size={20} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-300">Pomodoro</p>
            <p className="text-xl font-semibold">Bloque de foco</p>
          </div>
        </div>

        <div className="mb-5 flex flex-wrap gap-2">
          {presetDurations.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setDuration(value);
                setRemainingSeconds(value * 60);
                setRunning(false);
              }}
              className={`rounded-full px-3 py-2 text-sm ${
                duration === value ? "bg-white text-slate-950" : "bg-white/10 text-slate-200"
              }`}
            >
              {value} min
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-slate-300">
          <label htmlFor="customDuration" className="font-medium text-slate-400">
            Duración personalizada
          </label>
          <input
            id="customDuration"
            type="number"
            min={5}
            max={90}
            value={duration}
            onChange={(event) => {
              const value = Number(event.target.value);
              if (Number.isNaN(value)) {
                return;
              }
              const normalized = Math.max(5, Math.min(90, Math.floor(value)));
              setDuration(normalized);
              setRemainingSeconds(normalized * 60);
              setRunning(false);
            }}
            className="w-20 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-sm font-semibold text-white outline-none"
          />
          <span>minutos</span>
        </div>

        <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
          <div className="text-5xl font-semibold tracking-tight">
            {minutes}:{seconds}
          </div>
          <p className="mt-3 text-sm text-slate-300">
            Elegí el bloque que quieras dedicar a búsqueda, seguimiento o mejora de CV.
          </p>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setRunning((current) => !current)}
            className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm font-medium text-slate-950"
          >
            {running ? <Pause size={16} /> : <Play size={16} />}
            {running ? "Pausar" : "Empezar"}
          </button>
          <button
            type="button"
            onClick={() => {
              setRunning(false);
              setRemainingSeconds(duration * 60);
            }}
            className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2.5 text-sm font-medium text-white"
          >
            <RotateCcw size={16} />
            Reiniciar
          </button>
        </div>
      </section>
    </aside>
  );
}
