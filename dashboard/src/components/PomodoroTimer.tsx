"use client";

import { useEffect, useMemo, useState } from "react";
import { Pause, Play, RotateCcw, TimerReset } from "lucide-react";

const presetDurations = [15, 25, 45];

function formatRemaining(seconds: number) {
  const minutes = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const secs = (seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${secs}`;
}

export function PomodoroTimer() {
  const [selectedMinutes, setSelectedMinutes] = useState(25);
  const [remainingSeconds, setRemainingSeconds] = useState(25 * 60);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (!isRunning) {
      return;
    }

    const timer = window.setInterval(() => {
      setRemainingSeconds((current) => {
        if (current <= 1) {
          window.clearInterval(timer);
          setIsRunning(false);
          return 0;
        }

        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [isRunning]);

  const progress = useMemo(() => {
    const total = selectedMinutes * 60;
    if (total <= 0) {
      return 0;
    }

    return Math.max(0, Math.min(100, Math.round(((total - remainingSeconds) / total) * 100)));
  }, [remainingSeconds, selectedMinutes]);

  const applyPreset = (minutes: number) => {
    setSelectedMinutes(minutes);
    setRemainingSeconds(minutes * 60);
    setIsRunning(false);
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Pomodoro
          </p>
          <h2 className="mt-2 text-4xl font-semibold tracking-tight text-slate-950">
            {formatRemaining(remainingSeconds)}
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Bloque actual de {selectedMinutes} minutos para buscar, aplicar o ajustar tu CV.
          </p>
        </div>

        <div className="rounded-2xl bg-rose-50 p-3 text-rose-700">
          <TimerReset size={22} />
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {presetDurations.map((minutes) => (
          <button
            key={minutes}
            type="button"
            onClick={() => applyPreset(minutes)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
              selectedMinutes === minutes
                ? "bg-slate-950 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {minutes} min
          </button>
        ))}
      </div>

      <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-rose-500 via-orange-500 to-amber-400 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setIsRunning((current) => !current)}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 font-medium text-white hover:bg-slate-800"
        >
          {isRunning ? <Pause size={18} /> : <Play size={18} />}
          {isRunning ? "Pausar" : "Empezar"}
        </button>

        <button
          type="button"
          onClick={() => {
            setIsRunning(false);
            setRemainingSeconds(selectedMinutes * 60);
          }}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 font-medium text-slate-700 hover:border-slate-300 hover:bg-slate-50"
        >
          <RotateCcw size={18} />
          Reiniciar
        </button>
      </div>
    </div>
  );
}
