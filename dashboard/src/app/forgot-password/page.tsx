"use client";

import { useState } from "react";
import Link from "next/link";

import PublicFooterLinks from "@/components/PublicFooterLinks";
import { apiRequest } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const data = await apiRequest<{ message: string }>("/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMessage(data.message);
    } catch (error) {
      setMessage(
        error && typeof error === "object" && "message" in error
          ? String(error.message)
          : "No pudimos iniciar la recuperación en este momento.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/20 bg-white/10 p-8 backdrop-blur-lg">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">Recuperar password</h1>
        <p className="text-white/60 text-center mb-6">
          Te enviamos un enlace seguro para crear una nueva contraseña.
        </p>

        {message ? (
          <div className="mb-4 rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-sm text-white">
            {message}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="tu@email.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-lg border border-white/20 bg-white/10 px-4 py-3 text-white placeholder-white/50 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 py-3 font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Enviando..." : "Enviar enlace"}
          </button>
        </form>

        <p className="mt-6 text-center text-white/60">
          ¿Ya te acordaste?{" "}
          <Link href="/login" className="text-purple-300 hover:underline">
            Volver al login
          </Link>
        </p>

        <PublicFooterLinks />
      </div>
    </div>
  );
}
