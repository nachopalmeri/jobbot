import LegalPage from "@/components/LegalPage";

export default function TermsPage() {
  return (
    <LegalPage
      eyebrow="Legal"
      title="Términos de servicio"
      intro="Al usar JobBot aceptás estos términos. El producto está pensado para ayudarte a buscar trabajo mejor, no para garantizar resultados concretos de contratación."
      sections={[
        {
          title: "Uso permitido",
          content: [
            "Podés usar JobBot para buscar empleos, organizar postulaciones, analizar CVs y gestionar tu flujo personal de búsqueda laboral.",
            "No podés usar el servicio para scraping abusivo, fraude, automatización maliciosa, ni para interferir con la operación de terceros o del propio producto.",
          ],
        },
        {
          title: "Planes, créditos y acceso",
          content: [
            "Los planes pagos habilitan límites y capacidades superiores. Los créditos de CV Suite son de pago puntual y, salvo aclaración expresa, no expiran.",
            "Las suscripciones mensuales o anuales se renuevan o mantienen según el proveedor de pago y el ciclo contratado.",
          ],
        },
        {
          title: "Disponibilidad y cambios",
          content: [
            "Podemos mejorar, ajustar o retirar funciones para sostener la operación y seguridad del producto. También podemos actualizar precios y límites hacia adelante.",
            "Intentamos mantener el servicio disponible, pero no garantizamos disponibilidad absoluta ni ausencia total de errores.",
          ],
        },
        {
          title: "Limitación de responsabilidad",
          content: [
            "JobBot ofrece herramientas de apoyo para decisiones laborales. La decisión final de aplicar, comprar un plan o seguir una recomendación siempre es tuya.",
            "No garantizamos entrevistas, ofertas ni resultados específicos de carrera.",
          ],
        },
      ]}
    />
  );
}
