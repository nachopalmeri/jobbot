'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Check, 
  CreditCard, 
  Wallet, 
  Bitcoin,
  Sparkles,
  Zap,
  Shield,
  Clock,
  X
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/components/ui/button';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'para siempre',
    description: 'Perfecto para comenzar tu búsqueda',
    icon: Zap,
    features: [
      '3 alertas por semana',
      '5 búsquedas diarias',
      '2 análisis de CV/mes',
      'Dashboard básico',
      'Soporte por email',
    ],
    notFeatures: [
      'Match con ofertas automático',
      'Job Tracker avanzado',
      'Export PDF de aplicaciones',
    ],
    cta: 'Plan actual',
    current: true,
    popular: false,
  },
  {
    name: 'Premium',
    price: '$5',
    period: 'por mes',
    description: 'Para profesionales serios en búsqueda',
    icon: Sparkles,
    features: [
      'Alertas ilimitadas',
      'Búsquedas ilimitadas',
      'Análisis de CV ilimitados',
      'Match automático con ofertas',
      'Job Tracker con notas',
      'Export PDF de aplicaciones',
      'Soporte prioritario',
      'Acceso anticipado a features',
    ],
    notFeatures: [],
    cta: 'Actualizar a Premium',
    current: false,
    popular: true,
  },
];

const providers = [
  { name: 'Stripe', icon: CreditCard, color: 'bg-purple-600', description: 'Tarjetas de crédito/débito' },
  { name: 'MercadoPago', icon: Wallet, color: 'bg-blue-600', description: 'Efectivo, transferencia' },
  { name: 'Crypto', icon: Bitcoin, color: 'bg-orange-500', description: 'Bitcoin, Ethereum, USDC' },
];

const faqs = [
  {
    question: '¿Puedo cambiar de plan en cualquier momento?',
    answer: 'Sí, puedes actualizar o cancelar tu plan en cualquier momento. Los cambios se aplican inmediatamente.',
  },
  {
    question: '¿Hay período de prueba?',
    answer: 'No necesitas período de prueba. El plan Free te permite probar todas las funciones básicas sin límite de tiempo.',
  },
  {
    question: '¿Qué pasa si cancelo Premium?',
    answer: 'Volverás automáticamente al plan Free al final del período pagado. Tus datos se mantienen seguros.',
  },
];

export default function SuscripcionPage() {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  const handleUpgrade = async (provider: string) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/subscriptions/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ provider }),
      });
      
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      alert('Error al procesar pago');
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 max-w-5xl"
    >
      <motion.div variants={itemVariants} className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">Elige tu plan</h1>
        <p className="text-muted-foreground mt-2 max-w-lg mx-auto">
          JobBot trabaja por ti 24/7. Elige el plan que mejor se adapte a tus necesidades de búsqueda.
        </p>
      </motion.div>

      <motion.div variants={itemVariants} className="grid md:grid-cols-2 gap-6">
        {plans.map((plan) => (
          <Card 
            key={plan.name} 
            className={cn(
              'relative overflow-hidden',
              plan.popular && 'border-primary shadow-lg scale-105 md:scale-105'
            )}
          >
            {plan.popular && (
              <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-xs font-medium px-3 py-1 rounded-bl-lg">
                Más popular
              </div>
            )}
            
            <CardHeader className="pb-4">
              <div className="flex items-center gap-3 mb-2">
                <div className={cn(
                  'h-10 w-10 rounded-lg flex items-center justify-center',
                  plan.popular ? 'bg-primary/10' : 'bg-muted'
                )}>
                  <plan.icon className={cn('h-5 w-5', plan.popular ? 'text-primary' : 'text-muted-foreground')} />
                </div>
                <div>
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{plan.description}</p>
                </div>
              </div>
              <div className="mt-4">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-muted-foreground">/{plan.period}</span>
              </div>
            </CardHeader>
            
            <CardContent>
              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm">
                    <Check className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                    <span className="text-foreground">{feature}</span>
                  </li>
                ))}
                {plan.notFeatures.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm text-muted-foreground">
                    <X className="h-4 w-4 shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Button 
                className={cn('w-full mt-6', plan.current && 'pointer-events-none opacity-60')}
                variant={plan.current ? 'outline' : 'default'}
                size="lg"
              >
                {plan.cta}
              </Button>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              Métodos de pago disponibles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-3 gap-4">
              {providers.map((provider) => (
                <button
                  key={provider.name}
                  onClick={() => setSelectedProvider(provider.name)}
                  className={cn(
                    'flex flex-col items-center p-6 rounded-xl border transition-all duration-200',
                    selectedProvider === provider.name
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'hover:border-primary/50 hover:bg-accent/50'
                  )}
                >
                  <div className={cn('h-12 w-12 rounded-full flex items-center justify-center mb-3', provider.color)}>
                    <provider.icon className="h-6 w-6 text-white" />
                  </div>
                  <span className="font-medium">{provider.name}</span>
                  <span className="text-xs text-muted-foreground mt-1">{provider.description}</span>
                </button>
              ))}
            </div>
            
            {selectedProvider && (
              <div className="mt-6 text-center">
                <Button size="lg" onClick={() => handleUpgrade(selectedProvider.toLowerCase())}>
                  Continuar con {selectedProvider}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Preguntas frecuentes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <div key={index} className="pb-4 border-b last:border-0 last:pb-0">
                  <h3 className="font-medium mb-2">{faq.question}</h3>
                  <p className="text-sm text-muted-foreground">{faq.answer}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemVariants} className="text-center">
        <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Shield className="h-4 w-4" />
          <span>Pagos seguros encriptados • Cancela cuando quieras • Soporte 24/7</span>
        </div>
      </motion.div>
    </motion.div>
  );
}
