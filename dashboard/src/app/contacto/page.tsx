import LegalPage from "@/components/LegalPage";

import { supportEmail } from "@/lib/site";

export default function ContactPage() {
  return (
    <LegalPage
      eyebrow="Soporte"
      title="Contacto y ayuda"
      intro={`Si algo falla, si tenés dudas con tu cuenta o si necesitás ayuda con cobros, escribinos a ${supportEmail}.`}
      sections={[
        {
          title: "Qué incluir en tu mensaje",
          content: [
            "Mandanos el email de tu cuenta, una descripción corta del problema y, si aplica, una captura o el comprobante del cobro.",
          ],
        },
        {
          title: "Temas que resolvemos",
          content: [
            "Acceso a la cuenta, recuperación de password, facturación, cancelaciones, problemas con créditos, vinculación con Telegram y bugs del dashboard o del bot.",
          ],
        },
      ]}
    />
  );
}
