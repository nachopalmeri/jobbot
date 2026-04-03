export const supportEmail =
  process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim() || "support@jobbot.ar";

export const supportMailto = `mailto:${supportEmail}`;

export const appUrl =
  process.env.NEXT_PUBLIC_APP_URL?.trim() || "https://app-jobbot.vercel.app";

export const landingUrl =
  process.env.NEXT_PUBLIC_LANDING_URL?.trim() ||
  "https://jobbotlandingclean.vercel.app";

export const siteName = "JobBot";

export const legalLinks = {
  privacy: "/legal/privacidad",
  terms: "/legal/terminos",
  refunds: "/legal/reembolsos",
  contact: "/contacto",
};
