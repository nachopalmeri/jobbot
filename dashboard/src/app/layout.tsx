import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { appUrl, landingUrl, siteName } from "@/lib/site";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
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
    "JobBot centraliza tu búsqueda laboral: pipeline, alertas, CV Intelligence, mock interviews y seguimiento real de tu proceso.",
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
      "Buscá empleo, analizá tu CV y gestioná tus postulaciones desde un solo dashboard.",
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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
