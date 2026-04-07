import { createHmac } from "crypto";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const TOKEN_SECRET = process.env.JOBBOT_DEMO_SECRET || "jobbot-demo-secret";
const STATE_COOKIE = "jobbot_demo_state";

type PlanId = "free" | "starter" | "pro" | "premium";

type DemoPreferences = {
  experience_level: string;
  role_type: string;
  technologies: string;
  location: string;
  job_modality: string;
  job_schedule: string;
  weekly_goal: number;
  digest_mode: string;
  active_alerts: boolean;
};

type DemoApplication = {
  id: number;
  job_title: string;
  company: string;
  url?: string;
  notes?: string;
  status: "aplicado" | "entrevista" | "rechazado" | "oferta";
  applied_at: string;
};

type DemoCvHistory = {
  id: string;
  created_at: string;
  ats_score: number;
  match_score: number | null;
  job_title: string;
  company_name: string;
  suggestions: string[];
  ai_feedback: string | null;
};

type DemoState = {
  email: string;
  name: string;
  telegram_id: number;
  plan: PlanId;
  is_admin: boolean;
  created_at: string;
  subscription_status: string;
  billing_cycle: "monthly" | "yearly";
  expires_at: string | null;
  weekly_applied: number;
  preferences: DemoPreferences;
  credits: {
    total_credits: number;
    unlock_active: boolean;
    active_packs: Array<{
      id: number;
      pack_type: string;
      credits_remaining: number;
      purchase_price: number;
    }>;
  };
  applications: DemoApplication[];
  cv_history: DemoCvHistory[];
};

type TokenPayload = {
  email: string;
  name: string;
  telegram_id: number;
  is_admin: boolean;
  plan: PlanId;
};

const adminCredentials = {
  email: "admin@jobbot.com",
  password: "JobBotAdmin!2026",
  name: "Admin JobBot",
};

const planLimits: Record<
  PlanId,
  {
    searches_limit: number;
    interviews_limit: number;
    analyses_limit: number;
  }
> = {
  free: { searches_limit: 3, interviews_limit: 0, analyses_limit: 1 },
  starter: { searches_limit: 12, interviews_limit: 0, analyses_limit: 2 },
  pro: { searches_limit: 40, interviews_limit: 2, analyses_limit: 4 },
  premium: { searches_limit: 120, interviews_limit: 10, analyses_limit: 20 },
};

const subscriptionPlans = [
  {
    id: "free",
    name: "Free",
    price: 0,
    currency: "USD",
    features: [
      "3 busquedas por dia",
      "Dashboard base",
      "ATS checker simple",
      "Meta semanal y racha",
    ],
  },
  {
    id: "starter",
    name: "Starter",
    price: 4,
    yearly_price: 40,
    currency: "USD",
    features: [
      "12 busquedas por dia",
      "Pipeline operativo",
      "Alertas por Telegram",
      "Mas foco diario",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    price: 8,
    yearly_price: 80,
    currency: "USD",
    recommended: true,
    features: [
      "40 busquedas por dia",
      "4 analisis IA por mes",
      "Match score y recomendaciones",
      "Mayor seguimiento",
    ],
  },
  {
    id: "premium",
    name: "Premium",
    price: 12,
    yearly_price: 120,
    currency: "USD",
    featured: true,
    features: [
      "120 busquedas por dia",
      "20 analisis IA",
      "Mock interviews",
      "Cover letters",
      "CV Suite completa",
    ],
  },
];

const creditPacks = [
  {
    id: "unlock_suite",
    name: "Unlock CV Suite",
    description: "Activa la suite y habilita historial + herramientas base.",
    credits: 50,
    price_usd: 19,
    is_unlock: true,
    unit_price: 0.38,
  },
  {
    id: "credits_25",
    name: "25 creditos",
    description: "Ideal para scans, cover letters y mejoras puntuales.",
    credits: 25,
    price_usd: 9,
    is_unlock: false,
    unit_price: 0.36,
  },
  {
    id: "credits_60",
    name: "60 creditos",
    description: "El pack mas equilibrado para una busqueda activa.",
    credits: 60,
    price_usd: 19,
    is_unlock: false,
    unit_price: 0.32,
    highlight: true,
  },
  {
    id: "credits_120",
    name: "120 creditos",
    description: "Para iterar fuerte CV, cartas y entrevistas.",
    credits: 120,
    price_usd: 35,
    is_unlock: false,
    unit_price: 0.29,
  },
];

function toBase64Url(value: string) {
  return Buffer.from(value, "utf8").toString("base64url");
}

function fromBase64Url(value: string) {
  return Buffer.from(value, "base64url").toString("utf8");
}

function signPayload(payload: string) {
  return createHmac("sha256", TOKEN_SECRET).update(payload).digest("base64url");
}

function issueToken(payload: TokenPayload) {
  const serialized = JSON.stringify(payload);
  const encoded = toBase64Url(serialized);
  return `jb.${encoded}.${signPayload(encoded)}`;
}

function readTokenPayload(token: string | null): TokenPayload | null {
  if (!token) {
    return null;
  }

  const [prefix, encoded, signature] = token.split(".");
  if (prefix !== "jb" || !encoded || !signature) {
    return null;
  }

  if (signPayload(encoded) !== signature) {
    return null;
  }

  try {
    return JSON.parse(fromBase64Url(encoded)) as TokenPayload;
  } catch {
    return null;
  }
}

function demoJobs(role: string) {
  const roleLabel = role.trim() || "Backend Developer";
  return [
    {
      id: `job-${roleLabel}-1`,
      title: `${roleLabel} | Core Product`,
      company: "Lighthouse Labs",
      location: "Remoto · Latam",
      modality: "remote",
      match_score: 92,
      source: "LinkedIn",
      description: "Rol con ownership, foco en producto y stack moderno.",
      url: "https://example.com/jobs/1",
    },
    {
      id: `job-${roleLabel}-2`,
      title: `${roleLabel} | Growth Systems`,
      company: "Orbit Talent",
      location: "Hibrido · Buenos Aires",
      modality: "hybrid",
      match_score: 84,
      source: "GetOnBoard",
      description: "Busqueda orientada a impacto y trabajo con datos reales.",
      url: "https://example.com/jobs/2",
    },
    {
      id: `job-${roleLabel}-3`,
      title: `${roleLabel} | Platform`,
      company: "Northstar",
      location: "Remoto · Global",
      modality: "remote",
      match_score: 78,
      source: "Indeed",
      description: "Posicion de escala con desafios de arquitectura y delivery.",
      url: "https://example.com/jobs/3",
    },
  ];
}

function buildDefaultState(overrides: Partial<DemoState> = {}): DemoState {
  const now = new Date().toISOString();
  return {
    email: overrides.email || "demo@jobbot.app",
    name: overrides.name || "Demo User",
    telegram_id: overrides.telegram_id || 900001,
    plan: overrides.plan || "free",
    is_admin: overrides.is_admin || false,
    created_at: now,
    subscription_status: "active",
    billing_cycle: "monthly",
    expires_at: null,
    weekly_applied: 3,
    preferences: {
      experience_level: "semi_senior",
      role_type: "Backend Developer",
      technologies: "Python, FastAPI, SQL, React",
      location: "Buenos Aires",
      job_modality: "remoto",
      job_schedule: "full_time",
      weekly_goal: 10,
      digest_mode: "realtime",
      active_alerts: true,
    },
    credits: {
      total_credits: 0,
      unlock_active: false,
      active_packs: [],
    },
    applications: [
      {
        id: 1,
        job_title: "Backend Developer",
        company: "Northstar",
        status: "aplicado",
        notes: "Aplicacion enviada con CV version 3.",
        applied_at: now,
        url: "https://example.com/jobs/1",
      },
      {
        id: 2,
        job_title: "Platform Engineer",
        company: "Lighthouse Labs",
        status: "entrevista",
        notes: "Seguimiento en 48 horas.",
        applied_at: now,
        url: "https://example.com/jobs/2",
      },
    ],
    cv_history: [],
    ...overrides,
  };
}

function buildAdminState() {
  const state = buildDefaultState({
    email: adminCredentials.email,
    name: adminCredentials.name,
    telegram_id: 1,
    plan: "premium",
    is_admin: true,
    expires_at: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString(),
  });
  state.weekly_applied = 8;
  state.credits = {
    total_credits: 120,
    unlock_active: true,
    active_packs: [{ id: 1, pack_type: "unlock_suite", credits_remaining: 120, purchase_price: 19 }],
  };
  return state;
}

function getStateFromCookie(request: NextRequest) {
  const raw = request.cookies.get(STATE_COOKIE)?.value;
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(decodeURIComponent(raw)) as DemoState;
  } catch {
    return null;
  }
}

function stateFromAuth(request: NextRequest) {
  const authHeader = request.headers.get("authorization") || "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;
  const tokenPayload = readTokenPayload(token);
  const cookieState = getStateFromCookie(request);

  if (cookieState && tokenPayload && cookieState.email === tokenPayload.email) {
    return cookieState;
  }

  if (tokenPayload?.email === adminCredentials.email) {
    return buildAdminState();
  }

  if (tokenPayload) {
    return buildDefaultState({
      email: tokenPayload.email,
      name: tokenPayload.name,
      telegram_id: tokenPayload.telegram_id,
      plan: tokenPayload.plan,
      is_admin: tokenPayload.is_admin,
    });
  }

  return null;
}

function withState(body: unknown, state?: DemoState, status = 200) {
  const response = NextResponse.json(body, { status });
  if (state) {
    response.cookies.set(
      STATE_COOKIE,
      encodeURIComponent(JSON.stringify(state)),
      {
        httpOnly: true,
        sameSite: "lax",
        secure: true,
        path: "/",
        maxAge: 60 * 60 * 24 * 30,
      },
    );
  }
  return response;
}

function clearState() {
  const response = NextResponse.json({ message: "Sesion cerrada" });
  response.cookies.set(STATE_COOKIE, "", { path: "/", maxAge: 0 });
  return response;
}

function unauthorized(detail = "Sesion expirada") {
  return NextResponse.json({ detail }, { status: 401 });
}

async function parseJson<T>(request: NextRequest) {
  try {
    return (await request.json()) as T;
  } catch {
    return null;
  }
}

async function parseForm(request: NextRequest) {
  const raw = await request.text();
  return new URLSearchParams(raw);
}

function buildUsage(state: DemoState) {
  const limits = planLimits[state.plan];
  return {
    remaining_searches: limits.searches_limit === 0 ? 0 : Math.max(limits.searches_limit - 2, 0),
    searches_limit: limits.searches_limit,
    searches_used: 2,
    remaining_interviews:
      limits.interviews_limit === 0 ? 0 : Math.max(limits.interviews_limit - 1, 0),
    interviews_limit: limits.interviews_limit,
    remaining_analyses:
      limits.analyses_limit === 0 ? 0 : Math.max(limits.analyses_limit - state.cv_history.length, 0),
    analyses_limit: limits.analyses_limit,
  };
}

function buildDashboardPayload(state: DemoState) {
  const applied = state.applications.filter((item) => item.status === "aplicado").length;
  const interview = state.applications.filter((item) => item.status === "entrevista").length;
  const offer = state.applications.filter((item) => item.status === "oferta").length;
  const rejected = state.applications.filter((item) => item.status === "rechazado").length;

  return {
    plan: state.plan,
    weekly_goal: state.preferences.weekly_goal,
    weekly_applied: state.weekly_applied,
    digest_mode: state.preferences.digest_mode,
    active_alerts: state.preferences.active_alerts,
    applications: state.applications,
    funnel: { applied, interview, offer, rejected },
  };
}

function scanResultFromInput(state: DemoState, fields: { jobTitle?: string; companyName?: string; jobDescription?: string; mode?: string; cvText?: string; }) {
  const text = fields.cvText || "";
  const hasTarget = Boolean(fields.jobTitle || fields.jobDescription);
  const atsScore = Math.min(95, 62 + Math.floor(text.length / 40));
  const matchScore = hasTarget ? Math.min(94, 58 + Math.floor(text.length / 55)) : null;
  const suggestions = [
    "Converti logros en resultados medibles.",
    "Subi keywords del rol en el summary inicial.",
    "Reduce bloques largos y mejora escaneabilidad ATS.",
  ];

  return {
    ats_score: atsScore,
    match_score: matchScore,
    matching_keywords: ["Python", "FastAPI", "SQL"],
    missing_keywords: hasTarget ? ["Ownership", "APIs", "Metrics"] : [],
    extra_keywords: ["Teamwork", "Delivery"],
    suggestions,
    strengths: ["Estructura clara", "Buen stack tecnico", "Experiencia relevante"],
    sections: {
      summary: true,
      experience: true,
      education: true,
      skills: true,
    },
    metrics: {
      word_count: Math.max(180, text.split(/\s+/).filter(Boolean).length || 220),
      keyword_count: 12,
      action_verb_hits: 9,
      metric_hits: 4,
    },
    quota: {
      used: state.cv_history.length + 1,
      limit: planLimits[state.plan].analyses_limit,
      remaining: Math.max(planLimits[state.plan].analyses_limit - (state.cv_history.length + 1), 0),
      ai_enabled: fields.mode === "pro",
    },
    credits: {
      total: state.credits.total_credits,
      unlock_active: state.credits.unlock_active,
    },
    ai_feedback:
      fields.mode === "pro"
        ? "Tu CV ya transmite seniority funcional. El siguiente salto esta en ajustar logros, densidad de keywords y foco por vacante."
        : null,
    ai_feedback_included: fields.mode === "pro",
    job_title: fields.jobTitle || "General",
    company_name: fields.companyName || "JobBot Match",
    mode: fields.mode || "basic",
    used_credits: fields.mode === "pro",
  };
}

async function handleFallback(request: NextRequest, path: string[]) {
  const key = `/${path.join("/")}`;
  const method = request.method.toUpperCase();
  const state = stateFromAuth(request);

  if (key === "/health" && method === "GET") {
    return NextResponse.json({
      status: "ok",
      checks: { database: "demo", auth: "ok", dashboard: "ok" },
    });
  }

  if (key === "/auth/register" && method === "POST") {
    const payload = await parseJson<{ email: string; password: string; name?: string; telegram_id?: number | null }>(request);
    if (!payload?.email || !payload.password) {
      return NextResponse.json({ detail: "Email y password son requeridos" }, { status: 400 });
    }

    const createdState = buildDefaultState({
      email: payload.email.trim().toLowerCase(),
      name: (payload.name || "Usuario").trim() || "Usuario",
      telegram_id: payload.telegram_id || Math.floor(100000 + Math.random() * 900000),
      plan: payload.email.trim().toLowerCase() === adminCredentials.email ? "premium" : "free",
      is_admin: payload.email.trim().toLowerCase() === adminCredentials.email,
    });

    if (createdState.is_admin) {
      createdState.credits = buildAdminState().credits;
      createdState.weekly_applied = 8;
    }

    const accessToken = issueToken({
      email: createdState.email,
      name: createdState.name,
      telegram_id: createdState.telegram_id,
      is_admin: createdState.is_admin,
      plan: createdState.plan,
    });

    return withState(
      {
        message: "Usuario registrado correctamente",
        access_token: accessToken,
        token_type: "bearer",
        telegram_id: createdState.telegram_id,
        email: createdState.email,
        is_admin: createdState.is_admin,
        is_temp_account: !payload.telegram_id,
        has_telegram_link: Boolean(payload.telegram_id),
        account_type: payload.telegram_id ? "telegram-linked" : "web-only",
      },
      createdState,
    );
  }

  if (key === "/auth/token" && method === "POST") {
    const form = await parseForm(request);
    const email = (form.get("username") || "").trim().toLowerCase();
    const password = form.get("password") || "";

    if (!email || !password) {
      return NextResponse.json({ detail: "Email y password son requeridos" }, { status: 400 });
    }

    let nextState: DemoState | null = null;
    if (email === adminCredentials.email && password === adminCredentials.password) {
      nextState = buildAdminState();
    } else if (state && state.email === email) {
      nextState = state;
    } else {
      nextState = buildDefaultState({
        email,
        name: email.split("@")[0] || "Usuario",
        telegram_id: Math.floor(100000 + Math.random() * 900000),
      });
    }

    const accessToken = issueToken({
      email: nextState.email,
      name: nextState.name,
      telegram_id: nextState.telegram_id,
      is_admin: nextState.is_admin,
      plan: nextState.plan,
    });

    return withState(
      {
        access_token: accessToken,
        token_type: "bearer",
        telegram_id: nextState.telegram_id,
        email: nextState.email,
        is_admin: nextState.is_admin,
        plan: nextState.plan,
        name: nextState.name,
        has_telegram_link: nextState.telegram_id > 0,
        account_type: nextState.telegram_id > 0 ? "telegram-linked" : "web-only",
      },
      nextState,
    );
  }

  if (key === "/auth/telegram/code" && method === "POST") {
    const payload = await parseJson<{ code?: string }>(request);
    const code = (payload?.code || "").trim().toUpperCase();
    const nextState = code === "ADMIN" ? buildAdminState() : buildDefaultState();
    const accessToken = issueToken({
      email: nextState.email,
      name: nextState.name,
      telegram_id: nextState.telegram_id,
      is_admin: nextState.is_admin,
      plan: nextState.plan,
    });
    return withState({ access_token: accessToken, token_type: "bearer" }, nextState);
  }

  if (key === "/auth/password-reset/request" && method === "POST") {
    return NextResponse.json({
      message: "Te enviamos instrucciones para restablecer tu password.",
    });
  }

  if (key === "/auth/password-reset/confirm" && method === "POST") {
    return NextResponse.json({
      message: "Password actualizada correctamente.",
    });
  }

  if (!state) {
    return unauthorized();
  }

  if (key === "/auth/me" && method === "GET") {
    return withState(
      {
        telegram_id: state.telegram_id,
        email: state.email,
        plan: state.plan,
        is_admin: state.is_admin,
        has_telegram_link: state.telegram_id > 0,
        is_temp_account: false,
        name: state.name,
      },
      state,
    );
  }

  if (key === "/auth/logout" && method === "POST") {
    return clearState();
  }

  if (key === "/auth/telegram/link-code" && method === "POST") {
    return withState(
      {
        code: state.is_admin ? "ADMIN" : "WEB123",
        expires_in: 600,
        already_linked: state.telegram_id > 0,
        telegram_bot_username: "jobs912bot",
        deep_link: "https://t.me/jobs912bot?start=link_WEB123",
        instructions: "/vincular WEB123",
      },
      state,
    );
  }

  if (key === "/users/preferences" && method === "GET") {
    return withState(
      {
        ...state.preferences,
        weekly_goal: state.preferences.weekly_goal,
      },
      state,
    );
  }

  if (key === "/users/preferences" && method === "POST") {
    const payload = await parseJson<Partial<DemoPreferences>>(request);
    const nextState = {
      ...state,
      preferences: {
        ...state.preferences,
        ...payload,
        weekly_goal: Number(payload?.weekly_goal ?? state.preferences.weekly_goal),
        active_alerts: Boolean(payload?.active_alerts ?? state.preferences.active_alerts),
      },
    };
    return withState({ message: "Preferencias guardadas." }, nextState);
  }

  if (key === "/users/dashboard" && method === "GET") {
    return withState(buildDashboardPayload(state), state);
  }

  if (key === "/users/usage" && method === "GET") {
    return withState(buildUsage(state), state);
  }

  if (key === "/jobs/recommended" && method === "GET") {
    return withState({ jobs: demoJobs(state.preferences.role_type) }, state);
  }

  if (key === "/jobs/search" && method === "GET") {
    const query = request.nextUrl.searchParams.get("q") || state.preferences.role_type;
    return withState({ jobs: demoJobs(query), total: 3 }, state);
  }

  if (key === "/jobs/applications" && method === "GET") {
    return withState({ applications: state.applications }, state);
  }

  if (key === "/jobs/track" && method === "POST") {
    const payload = await parseJson<{ job_title?: string; company?: string; url?: string; notes?: string }>(request);
    const created: DemoApplication = {
      id: Date.now(),
      job_title: payload?.job_title || "Nueva oportunidad",
      company: payload?.company || "Empresa",
      url: payload?.url,
      notes: payload?.notes,
      status: "aplicado",
      applied_at: new Date().toISOString(),
    };
    const nextState = { ...state, applications: [created, ...state.applications], weekly_applied: state.weekly_applied + 1 };
    return withState(created, nextState);
  }

  if (key.startsWith("/jobs/applications/") && method === "PATCH") {
    const appId = key.split("/").pop();
    const payload = await parseJson<{ status?: DemoApplication["status"] }>(request);
    const nextState = {
      ...state,
      applications: state.applications.map((item) =>
        String(item.id) === String(appId) && payload?.status ? { ...item, status: payload.status } : item,
      ),
    };
    return withState({ message: "Estado actualizado" }, nextState);
  }

  if (key === "/subscriptions/plans" && method === "GET") {
    return withState({ plans: subscriptionPlans }, state);
  }

  if (key === "/subscriptions/status" && method === "GET") {
    return withState(
      {
        plan: state.plan,
        status: state.subscription_status,
        provider: state.plan === "free" ? null : "demo",
        billing_cycle: state.billing_cycle,
        expires_at: state.expires_at,
        can_cancel: state.plan !== "free",
        can_manage_billing: state.plan !== "free",
        support_email: "support@jobbot.ar",
      },
      state,
    );
  }

  if (key === "/subscriptions/create-checkout" && method === "POST") {
    const payload = await parseJson<{ plan?: PlanId; billing_cycle?: "monthly" | "yearly" }>(request);
    const selectedPlan = payload?.plan && planLimits[payload.plan] ? payload.plan : "pro";
    const nextState = {
      ...state,
      plan: selectedPlan,
      billing_cycle: payload?.billing_cycle || "monthly",
      subscription_status: "active",
      expires_at: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString(),
    };
    return withState(
      {
        url: `${request.nextUrl.origin}/dashboard/suscripcion?success=1&plan=${selectedPlan}`,
      },
      nextState,
    );
  }

  if (key === "/subscriptions/manage-billing" && method === "POST") {
    return withState(
      { url: `${request.nextUrl.origin}/dashboard/suscripcion?billing=1` },
      state,
    );
  }

  if (key === "/subscriptions/cancel" && method === "POST") {
    const nextState = {
      ...state,
      plan: "free" as PlanId,
      subscription_status: "cancelled",
      expires_at: null,
    };
    return withState(
      {
        message: "Suscripcion cancelada. Tu cuenta vuelve a Free.",
        status: "cancelled",
        expires_at: null,
      },
      nextState,
    );
  }

  if (key === "/credits/packs" && method === "GET") {
    return withState({ packs: creditPacks }, state);
  }

  if (key === "/credits/balance" && method === "GET") {
    return withState(state.credits, state);
  }

  if (key === "/credits/checkout" && method === "POST") {
    const payload = await parseJson<{ pack_type?: string }>(request);
    const pack = creditPacks.find((item) => item.id === payload?.pack_type);
    if (!pack) {
      return NextResponse.json({ detail: "Pack invalido" }, { status: 400 });
    }
    const nextState = { ...state };
    if (pack.is_unlock) {
      nextState.credits.unlock_active = true;
    }
    nextState.credits.total_credits += pack.credits;
    nextState.credits.active_packs = [
      {
        id: Date.now(),
        pack_type: pack.id,
        credits_remaining: pack.credits,
        purchase_price: pack.price_usd,
      },
      ...nextState.credits.active_packs,
    ];
    return withState(
      {
        checkout_url: `${request.nextUrl.origin}/dashboard/creditos?success=true&pack=${pack.id}`,
      },
      nextState,
    );
  }

  if (key === "/cv/scan" && method === "POST") {
    const form = await request.formData();
    const cvText =
      (typeof form.get("cv_text") === "string" ? String(form.get("cv_text")) : "") ||
      (form.get("cv_file") instanceof File ? await (form.get("cv_file") as File).text() : "");
    const jobTitle = typeof form.get("job_title") === "string" ? String(form.get("job_title")) : "";
    const companyName = typeof form.get("company_name") === "string" ? String(form.get("company_name")) : "";
    const jobDescription = typeof form.get("job_description") === "string" ? String(form.get("job_description")) : "";
    const mode = typeof form.get("mode") === "string" ? String(form.get("mode")) : "basic";
    const scan = scanResultFromInput(state, { cvText, jobTitle, companyName, jobDescription, mode });
    const historyEntry: DemoCvHistory = {
      id: String(Date.now()),
      created_at: new Date().toISOString(),
      ats_score: scan.ats_score,
      match_score: scan.match_score,
      job_title: scan.job_title,
      company_name: scan.company_name,
      suggestions: scan.suggestions,
      ai_feedback: scan.ai_feedback,
    };
    const nextState = { ...state, cv_history: [historyEntry, ...state.cv_history] };
    if (mode === "pro" && nextState.credits.total_credits > 0) {
      nextState.credits.total_credits -= 1;
    }
    return withState(scan, nextState);
  }

  if (key === "/cv/proposal" && method === "POST") {
    const payload = await parseJson<{ job_title?: string; company_name?: string; user_cv?: string }>(request);
    return withState(
      {
        company: payload?.company_name || "Empresa",
        job_title: payload?.job_title || "Puesto",
        proposal:
          `Hola equipo de ${payload?.company_name || "la empresa"},\n\n` +
          `Me interesa la posicion de ${payload?.job_title || "este rol"} porque combina ownership, ejecucion y foco en impacto.\n\n` +
          "Vengo trabajando con entregas concretas, mejora continua y colaboracion entre producto y tecnologia. Creo que puedo aportar criterio, velocidad y una comunicacion clara desde el primer sprint.\n\n" +
          "Quedo disponible para conversar mas en detalle.\n\nSaludos,\n" +
          `${state.name}`,
        copied_text:
          `Hola equipo de ${payload?.company_name || "la empresa"},\n` +
          `Me interesa la posicion de ${payload?.job_title || "este rol"} y creo que mi perfil puede aportar valor concreto desde el inicio.\n\nSaludos,\n${state.name}`,
      },
      state,
    );
  }

  if (key === "/cv/mock-interview" && method === "POST") {
    return withState(
      {
        questions: [
          "Contame un proyecto reciente donde hayas tenido ownership real.",
          "Como priorizas cuando hay deadline corto y requisitos cambiantes?",
          "Que mediste para saber si una mejora tecnica valio la pena?",
          "Como adaptas tu CV y narrativa a una vacante distinta?",
          "Que buscas hoy en tu proximo equipo?",
        ],
      },
      state,
    );
  }

  if (key === "/cv/history" && method === "GET") {
    return withState({ analyses: state.cv_history }, state);
  }

  if (key.startsWith("/cv/history/") && method === "GET") {
    const analysisId = key.split("/").pop();
    const entry = state.cv_history.find((item) => item.id === analysisId) || state.cv_history[0];
    if (!entry) {
      return NextResponse.json({ detail: "Analisis no encontrado" }, { status: 404 });
    }
    return withState(
      {
        id: entry.id,
        created_at: entry.created_at,
        ats_score: entry.ats_score,
        match_score: entry.match_score,
        job_title: entry.job_title,
        company_name: entry.company_name,
        suggestions: entry.suggestions,
        ai_feedback: entry.ai_feedback,
      },
      state,
    );
  }

  if (key === "/admin/metrics" && method === "GET") {
    if (!state.is_admin) {
      return NextResponse.json({ detail: "Acceso restringido a administradores" }, { status: 403 });
    }
    return withState(
      {
        users: {
          telegram_total: 148,
          web_total: 87,
          active_today: 19,
          new_this_week: 11,
        },
        revenue: {
          total_usd: 2480,
          monthly_usd: 420,
        },
        plans: [
          { plan: "free", count: 44 },
          { plan: "starter", count: 17 },
          { plan: "pro", count: 15 },
          { plan: "premium", count: 11 },
        ],
        credits: {
          total_sold: 830,
          remaining: 312,
          consumed: 518,
        },
        recent_payments: [
          {
            id: 1,
            email: "founder-test@jobbot.app",
            amount: 12,
            currency: "USD",
            provider: "stripe",
            status: "paid",
            created_at: new Date().toISOString(),
          },
          {
            id: 2,
            email: "pro-user@jobbot.app",
            amount: 19,
            currency: "USD",
            provider: "mercadopago",
            status: "paid",
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
          },
        ],
      },
      state,
    );
  }

  return NextResponse.json({ detail: "Not Found" }, { status: 404 });
}

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function handleRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  return handleFallback(request, path);
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}

export async function OPTIONS(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  return handleRequest(request, context);
}
