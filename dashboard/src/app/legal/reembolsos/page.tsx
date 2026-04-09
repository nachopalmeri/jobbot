import LegalPage from "@/components/LegalPage";

export default function RefundsPage() {
  return (
    <LegalPage
      eyebrow="Billing"
      title="Cancelación y reembolsos"
      intro="Esta política explica cómo manejamos cancelaciones, renovaciones y pedidos de revisión de cobros para JobBot."
      sections={[
        {
          title: "Cancelación",
          content: [
            "Podés pedir la cancelación desde el dashboard o por soporte. Cuando el proveedor lo permite, la cancelación se programa al final del ciclo ya pagado para no cortarte acceso antes de tiempo.",
          ],
        },
        {
          title: "Reembolsos",
          content: [
            "Revisamos pedidos de reembolso caso por caso cuando hubo doble cobro, error técnico o activación incorrecta del plan.",
            "Los créditos consumidos y servicios efectivamente usados pueden no ser reembolsables.",
          ],
        },
        {
          title: "Créditos y unlocks",
          content: [
            "Los packs de créditos y el unlock de CV Suite son compras one-time. Si hubo un problema técnico al acreditarlos, lo corregimos o revisamos el cobro.",
          ],
        },
        {
          title: "Soporte de facturación",
          content: [
            "Si necesitás ayuda con cobros, cancelaciones o una revisión, escribinos por el canal de soporte publicado en JobBot e incluí el email de tu cuenta y el comprobante si lo tenés.",
          ],
        },
      ]}
    />
  );
}
