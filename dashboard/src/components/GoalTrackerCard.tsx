import { Target } from "lucide-react";

interface GoalTrackerCardProps {
  applied: number;
  goal: number;
}

export function GoalTrackerCard({ applied, goal }: GoalTrackerCardProps) {
  const safeGoal = goal > 0 ? goal : 1;
  const progress = Math.min(100, Math.round((applied / safeGoal) * 100));
  const remaining = Math.max(goal - applied, 0);
  const message =
    goal <= 0
      ? "Defini una meta semanal para medir tu avance real."
      : applied >= goal
        ? "Meta cumplida. Aprovecha el impulso y cerra follow-ups pendientes."
        : `Te faltan ${remaining} postulaciones para cerrar tu objetivo semanal.`;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Objetivo Semanal
          </p>
          <div className="mt-2 flex items-end gap-2">
            <span className="text-4xl font-semibold text-slate-950">{applied}</span>
            <span className="pb-1 text-base text-slate-500">/ {goal || "--"}</span>
          </div>
        </div>

        <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-700">
          <Target size={22} />
        </div>
      </div>

      <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="font-medium text-slate-800">{progress}% completado</span>
        <span className="text-slate-500">
          {goal > 0 ? `${remaining} pendientes` : "Sin meta"}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-600">{message}</p>
    </div>
  );
}
