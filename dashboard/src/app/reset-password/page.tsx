"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import PublicFooterLinks from "@/components/PublicFooterLinks";
import { apiRequest } from "@/lib/api";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => searchParams.get("token")?.trim() || "", [searchParams]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage("");

    if (!token) {
      setMessage("El enlace de recuperación es inválido.");
      return;
    }

    if (password.length < 6) {
      setMessage("La nueva password debe tener al menos 6 caracteres.");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiRequest<{ message: string }>("/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      });
      setSuccess(true);
      setMessage(data.message);
      window.setTimeout(() => router.replace("/login"), 1200);
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No pudimos actualizar tu password.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.18),_transparent_28%),linear-gradient(180deg,_#18181b,_#0f172a_42%,_#111827)] px-4 py-12 text-white">
      <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[2rem] border border-white/10 bg-white/6 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-indigo-300">
            Recuperación segura
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">Creá una nueva password</h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-white/72">
            Este enlace se usa una sola vez. Cuando la cambies, te redirigimos al login para que
            vuelvas a entrar al dashboard con normalidad.
          </p>

          <div className="mt-8 rounded-[1.5rem] border border-white/10 bg-black/15 p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="password"
                placeholder="Nueva password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
                required
              />
              <input
                type="password"
                placeholder="Repetí la nueva password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className="w-full rounded-2xl border border-white/12 bg-white/10 px-4 py-3 text-white placeholder:text-white/38 focus:border-indigo-300 focus:outline-none"
                required
              />
              {message ? (
                <div
                  className={`rounded-2xl border px-4 py-3 text-sm ${
                    success
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-100"
                      : "border-white/10 bg-white/8 text-white/88"
                  }`}
                >
                  {message}
                </div>
              ) : null}
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-2xl bg-gradient-to-r from-indigo-500 via-sky-500 to-amber-400 px-4 py-3 font-semibold text-slate-950 transition hover:opacity-95 disabled:opacity-60"
              >
                {loading ? "Actualizando..." : "Actualizar password"}
              </button>
            </form>

            <p className="mt-5 text-sm text-white/62">
              ¿Preferís volver?
              <Link href="/login" className="ml-2 font-semibold text-indigo-300 hover:text-indigo-200">
                Ir al login
              </Link>
            </p>

            <PublicFooterLinks />
          </div>
        </section>

        <aside className="rounded-[2rem] border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-300">
            Qué recuperás
          </p>
          <ul className="mt-5 space-y-4 text-sm leading-7 text-white/74">
            <li>Acceso al dashboard, pipeline y CV Suite.</li>
            <li>Tu historial de análisis, postulaciones y configuración.</li>
            <li>El enlace anterior deja de servir en cuanto cambias la clave.</li>
          </ul>
        </aside>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
          Cargando recuperación...
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
