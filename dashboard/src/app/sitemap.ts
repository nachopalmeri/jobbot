import type { MetadataRoute } from "next";

import { appUrl } from "@/lib/site";

const publicRoutes = [
  "",
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/contacto",
  "/legal/privacidad",
  "/legal/terminos",
  "/legal/reembolsos",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return publicRoutes.map((path) => ({
    url: `${appUrl}${path}`,
    lastModified: now,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : 0.7,
  }));
}
