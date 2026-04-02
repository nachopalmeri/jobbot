import Link from "next/link";

import { legalLinks, supportEmail, supportMailto } from "@/lib/site";

export default function PublicFooterLinks({
  tone = "dark",
}: {
  tone?: "dark" | "light";
}) {
  const textClass = tone === "dark" ? "text-white/65" : "text-stone-500";
  const linkClass =
    tone === "dark"
      ? "text-white hover:text-white"
      : "text-stone-700 hover:text-stone-950";

  return (
    <div className={`mt-6 text-center text-xs leading-6 ${textClass}`}>
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
        <Link href={legalLinks.privacy} className={linkClass}>
          Privacidad
        </Link>
        <Link href={legalLinks.terms} className={linkClass}>
          Términos
        </Link>
        <Link href={legalLinks.refunds} className={linkClass}>
          Reembolsos
        </Link>
        <Link href={legalLinks.contact} className={linkClass}>
          Contacto
        </Link>
      </div>
      <p className="mt-2">
        Soporte:{" "}
        <a href={supportMailto} className={linkClass}>
          {supportEmail}
        </a>
      </p>
    </div>
  );
}
