# JobBot Pricing Strategy

> **SV Standard:** Pricing is not about covering costs, it's about capturing value and enabling growth.

**Fecha:** Abril 2026  
**Versión:** 1.0

---

## 🔍 Competitor Analysis

### Huntr.co
| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Freemium |
| **Free** | 10 job apps, basic tracker, 1 board |
| **Pro** | $15/mes - ilimitado, templates, analytics |
| **Enterprise** | Custom - API, SSO, admin dashboard |
| **Fortaleza** | UX polished, integraciones (LinkedIn, email) |
| **Debilidad** | No AI matching, genérico (no específico IT) |
| **Revenue Est.** | ~$2M ARR |

### TealHQ.com
| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Freemium + AI Credits |
| **Free** | Resume builder, job tracker, basic AI |
| **Pro** | $9/mes - AI resume, unlimited jobs, LinkedIn optimization |
| **Business** | $15/mes - todo Pro + career coaching |
| **Fortaleza** | AI-powered resume optimization |
| **Debilidad** | Complejo, steep learning curve |
| **Revenue Est.** | ~$5M ARR |

### Simplify.jobs
| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Freemium |
| **Free** | 40 autofill applications/mes, basic tracker |
| **Pro** | $12/mes - ilimitado, AI cover letters, analytics |
| **Fortaleza** | Autofill forms (tiempo saver masivo) |
| **Debilidad** | Solo US/Canada focus, no LATAM |
| **Revenue Est.** | ~$1M ARR |

### Wonsulting AI
| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Subscription + Services |
| **Free** | Resume scanner, basic tips |
| **Pro** | $15-30/mes - AI tools + 1:1 coaching |
| **Premium** | $200+/mes - Full job search service |
| **Fortaleza** | Human coaching + AI |
| **Debilidad** | Caro, escalabilidad limitada |
| **Revenue Est.** | ~$3M ARR |

### GetOnBoard (LATAM)
| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Job Board (B2B) |
| **Free** | Para candidatos (buscar jobs) |
| **Empresas** | $200-500/mes por job posting |
| **Fortaleza** | Dominio LATAM, conocimiento local |
| **Debilidad** | No tooling para candidatos, solo listings |

---

## 💡 Pricing Strategy JobBot

### Filosofía
1. **Value-Based Pricing:** Precio basado en valor percibido (tiempo ahorrado), no costos
2. **Freemium with Purpose:** Free como funnel de conversion, no charity
3. **Progressive Disclosure:** Features se desbloquean según engagement
4. **LATAM-Optimized:** Precios adaptados a poder adquisitivo local

### Target Customer Value
- **Tiempo ahorrado:** 20h/semana → 2h/semana = 18h/semana valoradas en $10/h = **$180/semana**
- **Jobs encontrados:** 1 job match calificado = potencial de $500-5000 salario aumento
- **Tasa de éxito:** +30% de respuestas con CV optimizado = ROI inmediato

---

## 🎯 Three-Tier Model

### Tier 1: Free (Hunter)
**Propósito:** Adquisición + viral loop

**Features:**
- Job tracking: 5 jobs activos
- Matching score básico (keyword-based)
- CV builder: 1 CV
- Telegram bot: básico (notifications)
- Community support (Discord/Telegram)

**Limitaciones (Upgrade Triggers):**
- Cap de 5 jobs ("Necesitas más slots? Upgrade a Pro")
- Matching limitado ("Ver matches avanzados con Pro")
- Sin warm intros ("Conecta con recruiters - solo Pro")
- Analytics básicos ("Insights avanzados en Pro")

**Target:** 80% de usuarios (funnel top)

---

### Tier 2: Pro (Grower) - **$12/mes** ($8/mes anual)
**Propósito:** Revenue principal + engagement

**Features:**
- **Job tracking ilimitado**
- **AI Matching Score avanzado** (ML-powered)
- **CV Optimizer ilimitado** + A/B testing
- **Cover Letter generator** (AI-powered)
- **Analytics dashboard** avanzado
- **Warm intros:** 2 por mes a recruiters
- **Priority support** (24h response)
- **Application autofill** (integraciones)
- **Salary insights** personalizados
- **LinkedIn optimizer** (profile review)

**Upgrade Triggers (Free → Pro):**
- Alcanzar cap de 5 jobs
- Usar matching score >5 veces
- Querer aplicar a job #6
- Ver "warm intro available" banner

**Value Prop:** "Por $12/mes (menos que 2 cafés), ahorras 18h/semana y multiplicas tus chances"

**Target:** 15% de usuarios activos  
**Objetivo LTV:** $144 (anual) o $180 (12 meses mensual)

---

### Tier 3: Enterprise (Scale) - **Custom ($500-2000/mes)**
**Propósito:** Revenue alto + B2B partnerships

**Features:**
- **Todo Pro +**
- **Dedicated CSM** (Customer Success Manager)
- **Team analytics** (para managers de hiring)
- **Custom integrations** (ATS, HRIS)
- **White-label options**
- **API access** (full read/write)
- **SLA guarantee** (99.9% uptime)
- **Bulk warm intros** (ilimitado)
- **Custom ML models** (company-specific matching)
- **SSO/SAML**

**Target Customers:**
- Bootcamps (Acamica, Coderhouse) - job placement para alumnos
- IT Recruiters - candidate sourcing
- Tech companies - internal mobility
- Coworking spaces - member benefit

**Pricing Model:**
- Base: $500/mes (hasta 50 usuarios)
- Growth: $1000/mes (hasta 200 usuarios)
- Scale: $2000/mes (ilimitado)

---

## 📊 Pricing Tiers Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                        FREEMIUM FUNNEL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                                               │
│   │   FREE      │  80% de usuarios                               │
│   │   $0/mes    │  → Awareness + Education                      │
│   └──────┬──────┘                                               │
│          │                                                      │
│          │ (Upgrade triggers: cap limits, feature teasers)       │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │    PRO      │  15% de usuarios                               │
│   │ $12/mes     │  → Revenue Engine                              │
│   └──────┬──────┘                                               │
│          │                                                      │
│          │ (Teams, API needs, volume)                            │
│          ▼                                                      │
│   ┌─────────────┐                                               │
│   │ ENTERPRISE  │  5% de usuarios (B2B)                          │
│   │ $500+/mes   │  → High-value accounts                         │
│   └─────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Feature Gating Strategy

### Progressive Disclosure
Cada feature premium muestra teaser antes de paywall:

**Ejemplo - Warm Intros:**
1. User ve job match 95%
2. Bot: "¡Excelente match! 🎯 Quieres que te conecte directamente con el recruiter? [Ver cómo - Pro]"
3. Click muestra: "Con Pro, obtienes 2 warm intros/mes directos a recruiters"
4. CTA: "Upgrade a Pro - $12/mes"

### Upgrade Triggers (Contextual)
| Acción | Trigger | Mensaje |
|--------|---------|---------|
| Añadir job #6 | Soft paywall | "Límite de 5 jobs alcanzado. Necesitas más?" |
| Usar matching 5+ veces | Teaser | "Ver matches con 95%+ confianza en Pro" |
| Aplicar a job | Upsell | "Optimizar CV para este job? [Pro feature]" |
| Ver analytics | Teaser | "Ver tendencias de mercado? [Pro]" |
| 7 días sin login | Re-engagement | "Te extrañamos! 50% off primer mes Pro" |

---

## 💵 Revenue Projections

### Assumptions
- **Month 0:** 1,000 users (100% Free)
- **Month 3:** 3,000 users (85% Free, 12% Pro, 3% trials)
- **Month 6:** 8,000 users (80% Free, 15% Pro, 5% Enterprise trials)
- **Month 12:** 20,000 users (75% Free, 18% Pro, 2% Enterprise)
- **Conversion rate:** 15% Free → Pro (industry standard: 2-5%)
- **Churn:** 8% mensual (target <8%)
- **Annual discount:** 33% (paga 8 meses, recibe 12)

### Revenue Model

| Month | Users | Free | Pro | Enterprise | MRR | ARR |
|-------|-------|------|-----|------------|-----|-----|
| M0 | 1,000 | 1,000 | 0 | 0 | $0 | $0 |
| M1 | 1,500 | 1,350 | 150 | 0 | $1,800 | $21,600 |
| M3 | 3,000 | 2,550 | 450 | 0 | $5,400 | $64,800 |
| M6 | 8,000 | 6,400 | 1,200 | 0 | $14,400 | $172,800 |
| M9 | 14,000 | 10,500 | 3,360 | 2 | $40,720 | $488,640 |
| M12 | 20,000 | 15,000 | 4,800 | 5 | $60,100 | $721,200 |

**Notas:**
- Enterprise: $1000/mes average (asumiendo mix de tiers)
- M12: $60K MRR = $720K ARR (en rango Seed-ready)

---

## 🎯 CAC & LTV Analysis

### Customer Acquisition Cost (CAC)

| Channel | CAC | Volume/Mes | Primary? |
|---------|-----|------------|----------|
| Product Hunt | $5 | 200 | ✅ Yes |
| Indie Hackers | $3 | 100 | ✅ Yes |
| LinkedIn Organic | $2 | 150 | ✅ Yes |
| Content/SEO | $1 | 50 | ✅ Yes |
| Telegram | $4 | 100 | ✅ Yes |
| LinkedIn Ads | $25 | 50 | ⚠️ Selective |
| Google Ads | $30 | 30 | ❌ No |
| Referrals | $10 | 80 | ✅ Yes |

**Blended CAC:** ~$8  
**Target CAC:** <$15 (LTV/CAC >3x)

### Lifetime Value (LTV)

**Pro Tier:**
- Monthly: $12
- Churn: 8%/mes
- Avg Lifetime: 1/churn = 12.5 meses
- **LTV:** $12 × 12.5 = **$150**
- **LTV (annual):** $96 × 2 años = **$192**

**Enterprise Tier:**
- Monthly: $1000 avg
- Churn: 2%/mes (B2B stickier)
- Avg Lifetime: 50 meses
- **LTV:** $1000 × 50 = **$50,000**

### Unit Economics

| Métrica | Valor | Benchmark SV | Status |
|---------|-------|--------------|--------|
| LTV Pro | $150 | >$100 | ✅ Good |
| CAC Blended | $8 | <$30 | ✅ Excellent |
| LTV/CAC | 18.75x | >3x | ✅ Excellent |
| Months to Recover CAC | 0.7 | <12 | ✅ Excellent |
| Gross Margin | 85% | >80% | ✅ Good |
| Payback Period | 1 mes | <6 meses | ✅ Excellent |

---

## 🎁 Promotions & Discounts

### Launch Promotions
**Early Adopter (First 100):**
- 50% off forever (Pro: $6/mes)
- Lifetime "Founding Member" badge
- Direct access to founders

**Beta Users:**
- 30% off primer año
- Prioridad en feature requests

### Regular Promotions
**Annual Commitment:**
- 33% discount (paga $96, recibe 12 meses = $8/mes)
- Reduce churn, improve cash flow

**Referral Program:**
- $20 credit para referrer
- $20 discount para nuevo usuario
- Double-sided incentive

**Re-engagement:**
- 7 días inactivo: 20% off
- 30 días inactivo: 50% off primer mes
- Win-back campaigns

**Seasonal:**
- Enero (job search peak): "New Year, New Job" - 20% off
- Black Friday: 40% off annual
- Graduation season: Student discount 50%

---

## 🌍 LATAM Pricing Considerations

### Purchasing Power Parity (PPP)

| País | Pro Price Local | PPP Factor vs US |
|------|-----------------|------------------|
| Argentina | $12 USD (~$12,000 ARS) | 0.6x |
| México | $12 USD (~$200 MXN) | 0.8x |
| Colombia | $12 USD (~$48,000 COP) | 0.7x |
| Brasil | $12 USD (~$60 BRL) | 0.9x |
| Chile | $12 USD (~$11,000 CLP) | 1.0x |

**Strategy:** Uniform USD pricing para simplificar, pero:
- Local payment methods (MercadoPago, OXXO, PSE)
- "Job search cost" positioning vs "subscription cost"
- Emphasis en ROI ("Gana $500/mes más por $12/mes")

### Payment Methods
- Stripe (tarjetas internacionales)
- MercadoPago (LATAM local)
- PayPal
- Crypto (Bitcoin, Ethereum) - opcional
- OXXO/MoneyGram (cash payments - México)

---

## 📈 Pricing Optimization Roadmap

### Phase 1: Launch (M0-M3)
- Precios actuales: Free / $12 Pro / Custom Enterprise
- Focus: Conseguir 1000+ usuarios, validar willingness to pay
- Test: Different upgrade triggers, messaging

### Phase 2: Optimization (M3-M6)
- A/B test: $10 vs $12 vs $15 Pro
- Experiment: Usage-based pricing (credits system)
- Add: Tier intermedio ($7/mes "Starter")
- Implement: Annual plans con discount

### Phase 3: Scale (M6-M12)
- Dynamic pricing según país/currency
- Enterprise self-serve (sin sales)
- API pricing (pay-per-call)
- Usage-based overages

---

## 🔐 Pricing Page Best Practices

### JobBot Pricing Page Structure

```
1. HERO: "Stop job searching. Start job winning."
   Sub: "La plataforma #1 para developers IT en LATAM"

2. TOGGLE: Monthly | Annual (ahorra 33%)

3. CARDS: 3 tiers side-by-side
   - Free: "Get Started"
   - Pro (highlighted): "Most Popular" - $12/mes
   - Enterprise: "Contact Sales"

4. FEATURE COMPARISON TABLE
   - Checkmarks vs crosses
   - "Unlimited" destacado en Pro

5. SOCIAL PROOF
   - "4,000+ developers already using JobBot"
   - Testimonials con foto
   - Logos de companies que contratan

6. FAQ
   - "Puedo cambiar de plan?"
   - "Qué pasa si cancelo?"
   - "Hay garantía?"

7. CTA FINAL
   - "Start Free" / "Upgrade to Pro"
   - "No credit card required"
   - "Cancel anytime"

8. TRUST SIGNALS
   - SSL secure
   - GDPR compliant
   - 24/7 support
```

---

## 📋 Pricing Experiment Log

| Fecha | Experimento | Hypothesis | Result | Decision |
|-------|-------------|------------|--------|----------|
| M0 | Precio Pro $10 | Mayor conversión | TBD | Run |
| M0 | Precio Pro $15 | Mayor LTV | TBD | Run |
| M1 | Annual discount 20% | Reduce churn | TBD | Plan |
| M1 | Free limit 3 jobs | Más upgrades | TBD | Plan |
| M2 | Referral $15 | Mejor viralidad | TBD | Plan |

---

## ✅ Action Items

### Inmediato (P0)
- [ ] Implementar Stripe checkout
- [ ] Crear pricing page (Next.js)
- [ ] Setup feature flags para gating
- [ ] Configurar upgrade triggers (modales contextuales)
- [ ] Implementar free tier limitations

### Corto plazo (P1)
- [ ] A/B testing framework (Optimizely/PostHog)
- [ ] Analytics de conversion funnel
- [ ] Automate annual discount logic
- [ ] Setup referral tracking
- [ ] Integrar MercadoPago

### Medio plazo (P2)
- [ ] Usage-based pricing experiments
- [ ] Dynamic pricing por país
- [ ] Enterprise self-serve flow
- [ ] API monetization

---

*"Price is what you pay. Value is what you get."* — Warren Buffett  
*"The best pricing strategy is the one your customers thank you for."* — SV Wisdom

**Next Step:** Revisar [UNIT_ECONOMICS.md](./UNIT_ECONOMICS.md) para financial modeling detallado.
