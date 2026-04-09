"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageSquareShare, Target, UserRoundCog } from "lucide-react";
import { useSearchParams } from "next/navigation";

import { apiRequest } from "@/lib/api";

const defaultPreferences = {
  location: "Buenos Aires Argentina",
  experience_level: "junior",
  role_type: "",
  technologies: "",
  job_modality: "cualquiera",
  job_schedule: "cualquiera",
  max_job_age_days: 30,
  match_threshold: 70,
  check_interval_hours: 6,
  alert_start_hour: 8,
  alert_end_hour: 22,
  timezone: "America/Buenos_Aires",
  blocked_companies: "",
  preferred_companies: "",
  weekly_goal: 10,
  digest_mode: "realtime",
  active_alerts: false,
};

type PreferencesPayload = typeof defaultPreferences;

interface AccountPayload {
  telegram_id: number;
  email: string;
  plan: string;
  has_telegram_link?: boolean;
  is_temp_account: boolean;
  name: string;
}

interface TelegramLinkPayload {
  code: string | null;
  expires_in: number;
  already_linked: boolean;
  telegram_bot_username: string;
  deep_link?: string;
  instructions?: string;
}

export default function ConfiguracionPage() {
  const searchParams = useSearchParams();
  const [form, setForm] = useState<PreferencesPayload>(defaultPreferences);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [account, setAccount] = useState<AccountPayload | null>(null);
  const [linkData, setLinkData] = useState<TelegramLinkPayload | null>(null);
  const [linkLoading, setLinkLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [preferences, me] = await Promise.all([
          apiRequest<PreferencesPayload>("/users/preferences", {}, true),
          apiRequest<AccountPayload>("/auth/me", {}, true),
        ]);
        setForm((prev) => ({ ...prev, ...preferences }));
        setAccount({
          ...me,
          has_telegram_link: me.has_telegram_link ?? Number(me.telegram_id) > 0,
        });
      } catch {
        setMessage("No se pudieron cargar tus preferencias actuales.");
      }
    };

    void load();
  }, []);

  useEffect(() => {
    if (searchParams.get("linkTelegram") === "1") {
      setMessage(
        "Tu cuenta web ya esta creada. Si queres recibir alertas y entrar desde el bot, conecta Telegram desde esta pantalla.",
      );
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      await apiRequest(
        "/users/preferences",
        {
          method: "POST",
          body: JSON.stringify({
            ...form,
            alert_channel: account?.has_telegram_link ? "telegram" : "web",
          }),
        },
        true,
      );
      setMessage("Preferencias guardadas.");
    } catch (err) {
      setMessage(
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudieron guardar los cambios.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateLinkCode = async () => {
    try {
      setLinkLoading(true);
      setMessage("");
      const data = await apiRequest<TelegramLinkPayload>(
        "/auth/telegram/link-code",
        { method: "POST" },
        true,
      );
      setLinkData(data);
    } catch (err) {
      if (
        err &&
        typeof err === "object" &&
        "status" in err &&
        Number(err.status) === 404
      ) {
        setMessage(
          "La vinculacion por codigo todavia no esta disponible en este deploy. Si queres unir Telegram hoy, registra tu cuenta con tu ID de Telegram o entra desde una cuenta ya vinculada con /web_login.",
        );
        return;
      }

      const detail =
        err && typeof err === "object" && "message" in err
          ? String(err.message)
          : "No se pudo generar el codigo de vinculacion.";
      setMessage(detail);
    } finally {
      setLinkLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,_#f8fafc,_#eef2ff_30%,_#ffffff)] p-6 lg:p-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Configuracion
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
            Ajusta tu sistema de busqueda
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            Define foco, meta semanal y si queres operar con Telegram conectado o solo desde web.
          </p>

          {message ? (
            <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {message}
            </div>
          ) : null}
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <form
            onSubmit={handleSubmit}
            className="space-y-5 rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
                <UserRoundCog size={20} />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-950">Perfil y alertas</h2>
                <p className="text-sm text-slate-500">
                  Esto alimenta busquedas, ranking y recomendaciones.
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Nivel</span>
                <select
                  value={form.experience_level}
                  onChange={(e) => setForm({ ...form, experience_level: e.target.value })}
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <option value="sin_experiencia">Sin experiencia</option>
                  <option value="junior">Junior</option>
                  <option value="semi_senior">Semi senior</option>
                  <option value="senior">Senior</option>
                </select>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  Modalidad objetivo
                </span>
                <select
                  value={form.job_modality}
                  onChange={(e) => setForm({ ...form, job_modality: e.target.value })}
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <option value="cualquiera">Cualquiera</option>
                  <option value="remoto">Remoto</option>
                  <option value="hibrido">Hibrido</option>
                  <option value="presencial">Presencial</option>
                </select>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  Jornada objetivo
                </span>
                <select
                  value={form.job_schedule}
                  onChange={(e) => setForm({ ...form, job_schedule: e.target.value })}
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <option value="cualquiera">Cualquiera</option>
                  <option value="full_time">Jornada completa</option>
                  <option value="part_time">Media jornada</option>
                </select>
              </label>
            </div>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Ubicacion objetivo</span>
              <input
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                placeholder="Buenos Aires, Argentina o Remoto LATAM"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Rol buscado</span>
              <input
                value={form.role_type}
                onChange={(e) => setForm({ ...form, role_type: e.target.value })}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                placeholder="backend, data, frontend..."
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Tecnologias</span>
              <input
                value={form.technologies}
                onChange={(e) => setForm({ ...form, technologies: e.target.value })}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                placeholder="Python, SQL, React..."
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                  <Target size={16} />
                  Objetivo semanal
                </span>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={form.weekly_goal}
                  onChange={(e) =>
                    setForm({ ...form, weekly_goal: Number.parseInt(e.target.value || "0", 10) })
                  }
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">Modo de resumen</span>
                <select
                  value={form.digest_mode}
                  onChange={(e) => setForm({ ...form, digest_mode: e.target.value })}
                  className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                >
                  <option value="realtime">Realtime</option>
                  <option value="daily">Resumen diario</option>
                </select>
              </label>
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-4">
              <div>
                <p className="font-medium text-slate-900">Alertas activas</p>
                <p className="text-sm text-slate-500">
                  {account?.has_telegram_link
                    ? "Se enviaran por Telegram si tu cuenta esta conectada."
                    : "Tu cuenta quedara lista para trabajar solo desde web."}
                </p>
              </div>
              <input
                type="checkbox"
                checked={form.active_alerts}
                onChange={(e) => setForm({ ...form, active_alerts: e.target.checked })}
                className="h-5 w-5"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-2xl bg-slate-950 px-5 py-3 font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Guardando..." : "Guardar cambios"}
            </button>
          </form>

          <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-violet-100 p-3 text-violet-700">
                  <MessageSquareShare size={20} />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-slate-950">Cuenta y Telegram</h2>
                  <p className="text-sm text-slate-500">
                    {account?.email || "Sincronizando identidad..."}
                  </p>
                </div>
              </div>

              <div className="mt-5 space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-slate-500">Plan</span>
                  <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold text-white">
                    {(account?.plan || "free").toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-slate-500">Estado Telegram</span>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      account?.has_telegram_link
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {account?.has_telegram_link ? "Conectado" : "Pendiente"}
                  </span>
                </div>
              </div>

              {account?.has_telegram_link ? (
                <p className="mt-5 text-sm leading-6 text-slate-600">
                  Tu cuenta ya esta lista para usar alertas, login por codigo y deep links del bot.
                </p>
              ) : (
                <div className="mt-5 space-y-4">
                  <p className="text-sm leading-6 text-slate-600">
                    Si queres sumar alertas y acceso directo desde Telegram, genera un codigo y
                    vincula esta cuenta con tu bot.
                  </p>
                  <button
                    type="button"
                    onClick={() => void handleGenerateLinkCode()}
                    disabled={linkLoading}
                    className="rounded-2xl border border-violet-200 bg-violet-50 px-4 py-2.5 font-medium text-violet-800 hover:bg-violet-100 disabled:opacity-60"
                  >
                    {linkLoading ? "Generando codigo..." : "Generar codigo de vinculacion"}
                  </button>
                </div>
              )}

              {linkData && !linkData.already_linked ? (
                <div className="mt-5 rounded-2xl border border-violet-200 bg-violet-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-violet-600">
                    Codigo de vinculacion
                  </p>
                  <div className="mt-3 text-3xl font-semibold tracking-[0.18em] text-slate-950">
                    {linkData.code}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    En Telegram escribe <strong>{linkData.instructions}</strong> o abre el deep
                    link directo.
                  </p>
                  {linkData.deep_link ? (
                    <a
                      href={linkData.deep_link}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-4 py-2.5 font-medium text-white hover:bg-slate-800"
                    >
                      Abrir bot y vincular
                    </a>
                  ) : null}
                </div>
              ) : null}
            </section>

            <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-950">Siguiente paso sugerido</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Ajusta tu objetivo semanal, revisa tu pipeline y despues pasa por CV Suite para
                pulir el perfil antes de aplicar.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/dashboard/postulaciones"
                  className="rounded-2xl border border-slate-200 px-4 py-2.5 font-medium text-slate-700 hover:border-slate-300 hover:text-slate-950"
                >
                  Abrir pipeline
                </Link>
                <Link
                  href="/dashboard/cv"
                  className="rounded-2xl bg-violet-600 px-4 py-2.5 font-medium text-white hover:bg-violet-700"
                >
                  Ir a CV Suite
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
