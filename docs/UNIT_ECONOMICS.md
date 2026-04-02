# JobBot Unit Economics

> **SV Standard:** If you can't measure it, you can't improve it. Unit economics separate lifestyle businesses from unicorns.

**Fecha:** Abril 2026  
**Versión:** 1.0

---

## 📊 Financial Model Overview

### Business Model Summary
- **Type:** B2C SaaS + B2B Enterprise
- **Pricing:** Freemium (Free / $12 Pro / Custom Enterprise)
- **Revenue Mix Target:** 80% Subscriptions / 15% Affiliates / 5% Enterprise
- **Gross Margin Target:** 85%+
- **Target LTV/CAC:** >3x
- **Target Payback Period:** <6 meses

---

## 💰 Revenue Projections (12 Meses)

### Assumptions Base
```
Month 0 (Actual):
- Users: 1,000 (100% Free)
- MRR: $0
- Churn: N/A

Growth Rate:
- Month 1-3: 50% MoM (launch phase)
- Month 4-6: 30% MoM (growth phase)
- Month 7-12: 15% MoM (scale phase)

Conversion:
- Free → Pro: 15% (Month 3+), 18% (Month 12)
- Pro → Annual: 30% (Month 6+)
- Free → Enterprise: 0.5% (B2B referrals)

Churn:
- Free: 20% mensual (natural attrition)
- Pro: 8% mensual
- Enterprise: 2% mensual
- Annual plans: 15% anual (equivalente a ~1.3% mensual)
```

### Monthly Revenue Projection

| Month | Total Users | Free Users | Pro Users | Enterprise | MRR | ARR |
|-------|-------------|------------|-----------|------------|-----|-----|
| M0 | 1,000 | 1,000 | 0 | 0 | $0 | $0 |
| M1 | 1,500 | 1,380 | 120 | 0 | $1,440 | $17,280 |
| M2 | 2,250 | 1,950 | 300 | 0 | $3,600 | $43,200 |
| M3 | 3,000 | 2,550 | 450 | 0 | $5,400 | $64,800 |
| M4 | 4,000 | 3,200 | 800 | 0 | $9,600 | $115,200 |
| M5 | 5,200 | 4,056 | 1,144 | 0 | $13,728 | $164,736 |
| M6 | 6,760 | 5,203 | 1,557 | 0 | $18,684 | $224,208 |
| M7 | 8,450 | 6,335 | 2,115 | 0 | $25,380 | $304,560 |
| M8 | 10,140 | 7,502 | 2,638 | 0 | $31,656 | $379,872 |
| M9 | 12,168 | 8,881 | 3,287 | 0 | $39,444 | $473,328 |
| M10 | 14,194 | 10,198 | 3,996 | 0 | $47,952 | $575,424 |
| M11 | 16,323 | 11,588 | 4,735 | 0 | $56,820 | $681,840 |
| M12 | 20,000 | 14,800 | 5,200 | 2 | $64,400 | $772,800 |

**Notas:**
- Enterprise: Asumiendo 2 clientes @ $1000/mes desde M12
- Precio Pro: $12/mes (promedio, asume mix mensual/anual)
- Annual discount: 33% ya aplicado en cálculos

### Revenue by Tier

| Tier | M12 Users | MRR | % Revenue |
|------|-----------|-----|-----------|
| Free | 14,800 | $0 | 0% |
| Pro | 5,200 | $62,400 | 97% |
| Enterprise | 2 | $2,000 | 3% |
| **Total** | **20,000** | **$64,400** | **100%** |

---

## 📈 Key Metrics Dashboard

### CAC (Customer Acquisition Cost)

#### Blended CAC Breakdown

| Channel | Spend/Mes | New Users | CAC | % of Mix |
|---------|-----------|-----------|-----|----------|
| Product Hunt | $1,000 | 200 | $5 | 20% |
| Indie Hackers | $300 | 100 | $3 | 10% |
| LinkedIn Organic | $300 | 150 | $2 | 15% |
| Content/SEO | $150 | 150 | $1 | 15% |
| Telegram | $400 | 100 | $4 | 10% |
| LinkedIn Ads | $1,250 | 50 | $25 | 5% |
| Referrals | $800 | 80 | $10 | 8% |
| Direct/Other | $0 | 170 | $0 | 17% |
| **Total** | **$4,200** | **1,000** | **$4.20** | **100%** |

**Blended CAC:** $4.20 por usuario (mix Free + Pro)  
**Paid CAC:** $8.50 (solo usuarios pagos)  
**Target:** <$15 ✅

### LTV (Lifetime Value)

#### Pro Tier LTV Calculation

**Fórmula:** LTV = ARPU × (1 / Churn Rate)

| Component | Value |
|-----------|-------|
| ARPU (Average Revenue Per User) | $12/mes |
| Churn Rate (mensual) | 8% |
| Avg Lifetime | 12.5 meses |
| **LTV** | **$150** |

**LTV (Annual Plan):**
- ARPU: $8/mes (con 33% discount)
- Churn: 15% anual = 1.3% mensual effective
- Avg Lifetime: 6.7 años
- **LTV:** $96 × 6.7 = **$643**

#### Enterprise Tier LTV

| Component | Value |
|-----------|-------|
| ARPU | $1,000/mes |
| Churn Rate | 2% mensual |
| Avg Lifetime | 50 meses |
| **LTV** | **$50,000** |

### LTV/CAC Ratio

| Tier | LTV | CAC | LTV/CAC | Benchmark | Status |
|------|-----|-----|---------|-----------|--------|
| Pro (Monthly) | $150 | $8.50 | 17.6x | >3x | ✅ Excellent |
| Pro (Annual) | $643 | $8.50 | 75.6x | >3x | ✅ Excellent |
| Enterprise | $50,000 | $500* | 100x | >3x | ✅ Excellent |

*CAC Enterprise asume sales cycle + marketing

### Payback Period

**Cálculo:** CAC / (ARPU × Gross Margin)

| Tier | CAC | ARPU | Gross Margin | Payback | Benchmark | Status |
|------|-----|------|--------------|---------|-----------|--------|
| Pro | $8.50 | $12 | 85% | 0.83 meses | <6 meses | ✅ Excellent |
| Enterprise | $500 | $1,000 | 90% | 0.56 meses | <6 meses | ✅ Excellent |

**Blended Payback:** 1.2 meses ✅

---

## 💸 Cost Structure

### Cost of Goods Sold (COGS)

| Cost Item | M0 | M6 | M12 | % of Revenue M12 |
|-----------|-----|-----|-----|------------------|
| Hosting (AWS/Vercel) | $50 | $200 | $500 | 0.8% |
| Database (PostgreSQL) | $0 | $100 | $300 | 0.5% |
| CDN (CloudFront) | $10 | $50 | $150 | 0.2% |
| AI/ML APIs (OpenAI) | $100 | $400 | $1,200 | 1.9% |
| Scraping Infrastructure | $50 | $200 | $600 | 0.9% |
| Payment Processing (2.9%) | $0 | $542 | $1,868 | 2.9% |
| Customer Support (tools) | $0 | $100 | $300 | 0.5% |
| **Total COGS** | **$210** | **$1,592** | **$4,918** | **7.6%** |

**Gross Margin M12:** 92.4% ✅ (Target >85%)

### Operating Expenses (OPEX)

| Expense Category | M0 | M3 | M6 | M12 | % of Revenue M12 |
|------------------|-----|-----|-----|-----|------------------|
| **R&D (Engineering)** | | | | | |
| Salaries (2 devs) | $3,000 | $4,500 | $6,000 | $9,000 | 14.0% |
| Tools & Licenses | $200 | $300 | $400 | $600 | 0.9% |
| Infrastructure Dev | $100 | $200 | $300 | $500 | 0.8% |
| **R&D Total** | **$3,300** | **$5,000** | **$6,700** | **$10,100** | **15.7%** |
| | | | | | |
| **Sales & Marketing** | | | | | |
| Paid Acquisition | $1,000 | $2,500 | $4,200 | $7,000 | 10.9% |
| Content Creation | $500 | $800 | $1,000 | $1,500 | 2.3% |
| Events/Conferences | $0 | $500 | $1,000 | $2,000 | 3.1% |
| **S&M Total** | **$1,500** | **$3,800** | **$6,200** | **$10,500** | **16.3%** |
| | | | | | |
| **General & Administrative** | | | | | |
| Legal/Compliance | $200 | $300 | $500 | $800 | 1.2% |
| Accounting | $100 | $150 | $200 | $300 | 0.5% |
| Office/Remote Tools | $100 | $150 | $200 | $300 | 0.5% |
| Insurance | $50 | $100 | $150 | $250 | 0.4% |
| **G&A Total** | **$450** | **$700** | **$1,050** | **$1,650** | **2.6%** |
| | | | | | |
| **TOTAL OPEX** | **$5,250** | **$9,500** | **$13,950** | **$22,250** | **34.5%** |

### Monthly P&L Summary

| Item | M0 | M3 | M6 | M12 |
|------|-----|-----|-----|-----|
| **Revenue** | | | | |
| MRR | $0 | $5,400 | $18,684 | $64,400 |
| **Total Revenue** | **$0** | **$5,400** | **$18,684** | **$64,400** |
| | | | | |
| **Costs** | | | | |
| COGS | $210 | $996 | $2,802 | $4,918 |
| OPEX | $5,250 | $9,500 | $13,950 | $22,250 |
| **Total Costs** | **$5,460** | **$10,496** | **$16,752** | **$27,168** |
| | | | | |
| **Profitability** | | | | |
| Gross Profit | -$210 | $4,404 | $15,882 | $59,482 |
| Gross Margin | N/A | 82% | 85% | 92% |
| Operating Profit | -$5,460 | -$5,096 | $1,932 | $37,232 |
| Operating Margin | N/A | -94% | 10% | 58% |
| **EBITDA** | **-$5,460** | **-$5,096** | **$1,932** | **$37,232** |

**Break-even:** Mes 5-6 ✅

---

## 📊 SaaS Metrics Deep Dive

### Cohort Analysis Framework

**Cohorts por mes de signup:**

| Cohort | Month 0 | M1 | M3 | M6 | M12 | Retention M12 |
|--------|---------|-----|-----|-----|-----|---------------|
| M0 | 1,000 | 900 | 720 | 580 | 350 | 35% |
| M1 | 500 | 475 | 400 | 350 | 250 | 50% |
| M2 | 750 | 720 | 650 | 600 | - | - |
| M3 | 750 | 735 | 680 | - | - | - |

**Average 12-month retention:** 35-50%

### Activation Funnel

| Stage | Users | Conversion | Benchmark |
|-------|-------|------------|-----------|
| Signup | 1,000 | 100% | - |
| Complete Profile | 700 | 70% | 60% ✅ |
| First Job Search | 500 | 50% | 50% ✅ |
| Save First Job | 400 | 40% | 40% ✅ |
| Apply to Job | 200 | 20% | 25% ⚠️ |
| Get Interview | 50 | 5% | 8% 🔴 |
| **Aha Moment (First Match >80%)** | **250** | **25%** | **30%** | ⚠️ |
| Convert to Pro | 120 | 12% | 15% | ⚠️ |

**Funnel Analysis:**
- ✅ Strong top funnel (signup → search)
- ⚠️ Weak apply rate (need better UX)
- 🔴 Interview rate low (need CV optimization)
- ⚠️ Conversion 12% vs target 15%

### Churn Analysis

#### Churn by Tier

| Tier | Monthly Churn | Annual Churn | Main Reasons |
|------|---------------|--------------|--------------|
| Free | 20% | 93% | Natural attrition |
| Pro | 8% | 63% | Found job, no ongoing value |
| Annual Pro | 1.3% | 15% | Stickier, lower churn |
| Enterprise | 2% | 22% | Company changes, budget cuts |

#### Churn Prevention Strategy

**Voluntary Churn (70% de churn total):**
1. **"I found a job" (40%)**
   - Solución: Job change alerts, career growth tracking
   - Feature: "Keep me updated on market trends"
   
2. **"Too expensive" (20%)**
   - Solución: Annual discount, referral credits
   - Feature: "Pay what you want" para LATAM
   
3. **"Not finding value" (10%)**
   - Solución: Better onboarding, success metrics
   - Feature: Weekly progress emails

**Involuntary Churn (30% de churn total):**
1. **Payment failure (20%)**
   - Solución: Dunning management, retry logic
   - Feature: Alertas antes de expiry
   
2. **Account issues (10%)**
   - Solución: Proactive support, better UX

### Net Revenue Retention (NRR)

**Cálculo NRR:**
```
NRR = (Starting MRR + Expansion - Contraction - Churn) / Starting MRR

M6 Example:
- Starting MRR: $5,400 (M3)
- Expansion: $1,200 (upgrades, annual switches)
- Contraction: $300 (downgrades)
- Churn: $432 (8% de $5,400)

NRR = ($5,400 + $1,200 - $300 - $432) / $5,400
NRR = $5,868 / $5,400 = 108.7%
```

**Target:** >100% (indicating growth even sin nuevos usuarios)  
**Status:** 108.7% ✅ (Good, not yet excellent)

**Path to 120%+ NRR:**
- Annual plan incentives (reduce churn)
- Usage-based add-ons (expand revenue)
- Enterprise upsells (higher ACV)

---

## 🎯 Milestones & Targets

### Monthly Targets

| Month | Users | MRR | ARR | Churn | LTV/CAC |
|-------|-------|-----|-----|-------|---------|
| M0 | 1,000 | $0 | $0 | - | - |
| M3 | 3,000 | $5,400 | $64,800 | <10% | >5x |
| M6 | 6,760 | $18,684 | $224,208 | <8% | >10x |
| M12 | 20,000 | $64,400 | $772,800 | <6% | >15x |

### Seed Funding Readiness (M6)

| Metric | Target | Actual M6 | Status |
|--------|--------|-----------|--------|
| ARR | $200K | $224K | ✅ |
| MRR Growth (MoM) | 10% | 15% | ✅ |
| Gross Margin | 80% | 85% | ✅ |
| LTV/CAC | >3x | 17.6x | ✅ |
| Churn (Pro) | <10% | 8% | ✅ |
| NPS | >40 | TBD | 🔄 |
| Payback Period | <12 meses | 1 mes | ✅ |

---

## 📈 Financial Forecast (3 Años)

### Optimistic Scenario

| Year | Users | MRR | ARR | Team Size | Burn |
|------|-------|-----|-----|-----------|------|
| Y1 | 50,000 | $200,000 | $2.4M | 8 | $50K/mes |
| Y2 | 200,000 | $800,000 | $9.6M | 25 | $150K/mes |
| Y3 | 600,000 | $2,400,000 | $28.8M | 60 | $400K/mes |

### Base Scenario

| Year | Users | MRR | ARR | Team Size | Burn |
|------|-------|-----|-----|-----------|------|
| Y1 | 20,000 | $64,400 | $773K | 4 | $20K/mes |
| Y2 | 80,000 | $300,000 | $3.6M | 15 | $80K/mes |
| Y3 | 250,000 | $1,000,000 | $12M | 40 | $250K/mes |

### Conservative Scenario

| Year | Users | MRR | ARR | Team Size | Burn |
|------|-------|-----|-----|-----------|------|
| Y1 | 8,000 | $25,000 | $300K | 3 | $15K/mes |
| Y2 | 30,000 | $120,000 | $1.4M | 10 | $50K/mes |
| Y3 | 100,000 | $400,000 | $4.8M | 25 | $120K/mes |

---

## 🎓 Benchmarks SV Standards

| Metric | JobBot M12 | SaaS Median | Top Quartile | Status |
|--------|------------|-------------|--------------|--------|
| ARR | $773K | - | - | Early |
| ARR Growth | 15% MoM | 10% | 20% | ✅ Good |
| Gross Margin | 92% | 75% | 85% | ✅ Excellent |
| LTV/CAC | 17.6x | 3x | 5x | ✅ Excellent |
| CAC | $8.50 | $50 | $20 | ✅ Excellent |
| Churn (Logo) | 8% | 5% | 3% | ⚠️ OK |
| Churn (Revenue) | 5% | 2% | 1% | ⚠️ OK |
| NRR | 108% | 100% | 110% | ✅ Good |
| Payback | 1 mes | 12 meses | 6 meses | ✅ Excellent |
| Months Cash | 12+ | 12 | 18 | ✅ Good |

---

## ✅ Action Items

### Financial Tracking (P0)
- [ ] Setup Stripe dashboard con MRR tracking
- [ ] Implementar cohort analysis (Amplitude/Mixpanel)
- [ ] Automate LTV/CAC calculations
- [ ] Monthly financial review meeting
- [ ] Investor dashboard (Metricool/Public)

### Metrics Infrastructure (P1)
- [ ] Real-time revenue dashboard
- [ ] Churn prediction model
- [ ] Automated cohort reports
- [ ] Funnel analytics (activation tracking)
- [ ] NPS survey automation

### Optimization (P2)
- [ ] A/B test pricing (LTV impact)
- [ ] Reduce churn (better onboarding)
- [ ] Increase ARPU (upsells)
- [ ] Improve payback (organic channels)
- [ ] Gross margin optimization

---

*"Revenue is vanity, profit is sanity, but cash is king."*  
*"Unit economics don't lie. If LTV/CAC < 3x, you have a hobby, not a business."*

**Next Step:** Revisar [GTM_ROADMAP.md](./GTM_ROADMAP.md) para execution plan de 90 días.
