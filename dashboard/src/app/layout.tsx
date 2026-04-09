import type { Metadata } from "next";
import { DM_Sans, Geist_Mono, Sora } from "next/font/google";

import { appUrl, landingUrl, siteName } from "@/lib/site";

import "./globals.css";

const bodySans = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
});

const displaySans = Sora({
  variable: "--font-display",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: {
    default: `${siteName} | Dashboard y CV Intelligence`,
    template: `%s | ${siteName}`,
  },
  description:
    "JobBot AR automatiza tu búsqueda de empleo tech en LATAM: pipeline, alertas, CV Intelligence y preparación para entrevistas con IA.",
  keywords: [
    "jobbot",
    "dashboard laboral",
    "ats checker",
    "rank my cv",
    "pipeline de postulaciones",
    "busqueda de trabajo argentina",
  ],
  alternates: {
    canonical: appUrl,
  },
  openGraph: {
    type: "website",
    url: appUrl,
    siteName,
    title: `${siteName} | Dashboard y CV Intelligence`,
    description:
      "JobBot AR centraliza tu búsqueda de empleo tech en LATAM: analiza CVs con IA y facilita aplicaciones con información relevante.",
    images: [
      {
        url: `${landingUrl}/og-jobbot-dashboard.png`,
        width: 1200,
        height: 630,
        alt: "JobBot dashboard y CV Suite",
      },
    ],
    locale: "es_AR",
  },
  twitter: {
    card: "summary_large_image",
    title: `${siteName} | Dashboard y CV Intelligence`,
    description:
      "Pipeline, CV Suite, búsquedas guiadas y preparación de entrevistas en un solo lugar.",
    images: [`${landingUrl}/og-jobbot-dashboard.png`],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${bodySans.variable} ${displaySans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
