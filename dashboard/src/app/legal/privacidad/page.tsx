import LegalPage from "@/components/LegalPage";

export default function PrivacyPage() {
  return (
    <LegalPage
      eyebrow="Legal"
      title="Política de privacidad"
      intro="JobBot usa tus datos para darte búsqueda laboral, pipeline, CV Intelligence y alertas. Esta política resume qué guardamos, para qué y cómo podés pedir cambios o eliminación."
      sections={[
        {
          title: "Datos que procesamos",
          content: [
            "Guardamos los datos que nos das al crear cuenta o usar el bot: email, nombre, Telegram ID si lo vinculás, preferencias de búsqueda, postulaciones, CVs y resultados de análisis.",
            "Si activás pagos, también guardamos metadata transaccional como proveedor, estado del cobro, plan, expiración y referencias de pago. No almacenamos datos completos de tarjeta.",
          ],
        },
        {
          title: "Para qué los usamos",
          content: [
            "Usamos estos datos para autenticarte, recomendar empleos, mostrar tu pipeline, analizar tu CV, enviar alertas y sostener tu plan o créditos.",
            "También usamos logs y eventos mínimos para seguridad, rate limit, prevención de abuso e idempotencia de webhooks.",
          ],
        },
        {
          title: "Con quién compartimos información",
          content: [
            "Compartimos lo mínimo necesario con proveedores de infraestructura y cobro como Vercel, Azure, Stripe o MercadoPago cuando hace falta para operar el servicio.",
            "No vendemos tus datos personales a terceros.",
          ],
        },
        {
          title: "Tus derechos",
          content: [
            "Podés pedir acceso, corrección o eliminación de tus datos escribiendo a soporte. Si querés desvincular Telegram o cerrar tu cuenta, también lo gestionamos por ese canal.",
          ],
        },
      ]}
    />
  );
}
