# Product Requirements Document (PRD) - JobBot
## Q2-Q4 2026 Roadmap & Strategic Planning

---

## Executive Summary

JobBot is an AI-powered job search automation platform targeting tech workers in LATAM. With 2,400+ users and $2,400 MRR, we're positioned to capture the rapidly growing remote work market.

This PRD outlines the strategic roadmap for the next 9 months (Q2-Q4 2026), focusing on product-market fit expansion, revenue growth, and technical foundation for Series A.

---

## 1. Vision & Goals

### Vision Statement
*"The autopilot for tech careers in LATAM — matching every developer with their ideal opportunity using AI."*

### 2026 Goals

| Metric | Current | Q2 Target | Q4 Target |
|--------|---------|-----------|-----------|
| MAU | 2,400 | 8,000 | 25,000 |
| MRR | $2,400 | $8,000 | $25,000 |
| Paying Users | 120 | 400 | 1,250 |
| Churn Rate | 12% | 8% | 6% |
| NPS Score | 42 | 50 | 60 |
| Countries | 1 (AR) | 2 | 3 |

### Strategic Pillars

1. **Product Excellence** → Mobile apps, AI interview coach
2. **Geographic Expansion** → Mexico, Colombia, Brazil
3. **B2B Revenue** → Recruiter dashboard, ATS integrations
4. **Community** → Content, events, career coaching

---

## 2. Q2 2026 (Apr-Jun): Foundation & Mobile

### Theme: "Mobile-First Experience"

#### 2.1 Feature: Native Mobile Apps

**User Story:**
*"As a job seeker, I want to receive instant push notifications when a high-match job appears, so I can apply within minutes."*

**Requirements:**

| Feature | iOS | Android | Priority |
|---------|-----|---------|----------|
| Push notifications | ✅ | ✅ | P0 |
| Job search & filtering | ✅ | ✅ | P0 |
| CV upload (camera/doc) | ✅ | ✅ | P1 |
| In-app browser for applications | ✅ | ✅ | P1 |
| Offline mode (saved jobs) | ✅ | ✅ | P2 |
| Biometric auth | ✅ | ✅ | P2 |

**Acceptance Criteria:**
- [ ] Apps published on App Store & Play Store
- [ ] < 3s cold start time
- [ ] Push notification delivery < 30s
- [ ] 4.5+ star rating
- [ ] 70% of mobile web users migrate to app

**Technical Notes:**
- React Native (shared codebase)
- Expo EAS for builds
- Firebase Cloud Messaging
- Offline-first with WatermelonDB

#### 2.2 Feature: LinkedIn OAuth Integration

**User Story:**
*"As a user, I want to import my LinkedIn profile in one click, so I don't have to manually enter my experience."*

**Requirements:**
- OAuth 2.0 integration with LinkedIn
- Import: work experience, education, skills, certifications
- Auto-generate JobBot profile
- Sync every 30 days
- Handle API rate limits gracefully

**Acceptance Criteria:**
- [ ] 80% of new users choose LinkedIn signup
- [ ] Profile import completes in < 10s
- [ ] < 5% import errors

#### 2.3 Feature: Improved AI Matching V2

**User Story:**
*"As a user, I want the AI to understand not just keywords, but company culture fit and growth trajectory."*

**Requirements:**
- Fine-tuned Llama model on LATAM job market
- Culture fit analysis (remote-friendly, work-life balance)
- Career trajectory prediction
- Company stability scoring (financial data)
- User feedback loop (thumbs up/down on matches)

**Metrics:**
- Match accuracy: 75% → 85%
- False positive rate: 20% → 10%

---

## 3. Q3 2026 (Jul-Sep): Expansion & B2B

### Theme: "Geographic & Revenue Expansion"

#### 3.1 Feature: Mexico Launch

**User Story:**
*"As a Mexican developer, I want to see jobs from Mexican companies and understand local salary expectations."*

**Requirements:**

| Component | Details |
|-----------|---------|
| Job sources | OCC, Computrabajo, LinkedIn MX |
| Salary data | Local benchmarks (pesos) |
| Legal | Mexican labor law compliance |
| Language | Spanish (already supported) |
| Currency | MXN + USD |
| Payment | Stripe + local methods (Oxxo) |

**Acceptance Criteria:**
- [ ] 1,000 Mexican users in first 90 days
- [ ] 50+ Mexican companies posting jobs
- [ ] Localized salary data for 50 job types
- [ ] Mexican Spanish copy review

**Go-to-Market:**
- Partnership with local dev communities (Python MX, JS MX)
- Influencer outreach (tech YouTubers)
- Free tier for first 500 users

#### 3.2 Feature: Recruiter Dashboard (B2B)

**User Story:**
*"As a hiring manager, I want to search a database of pre-screened developers, so I can reduce time-to-hire."*

**Requirements:**

| Feature | Description | Pricing |
|---------|-------------|---------|
| Candidate search | Filter by skills, experience, location | $99/mo |
| AI matching | Match candidates to open positions | Included |
| Outreach | Message qualified candidates | $0.50/msg |
| Analytics | Pipeline tracking, response rates | Included |
| ATS Integrations | Greenhouse, Lever, Workable | $49/integration |

**Acceptance Criteria:**
- [ ] 50 recruiters signed up in Q3
- [ ] 500 candidate profiles searchable
- [ ] 10% candidate response rate to recruiter messages
- [ ] $5,000 MRR from B2B by end of Q3

#### 3.3 Feature: Application Tracking System (ATS) Integrations

**User Story:**
*"As a user, I want JobBot to automatically track my applications in Greenhouse/Lever, so I know my application status."*

**Requirements:**
- Chrome extension for auto-tracking
- Parse confirmation emails
- Integrate with: Greenhouse, Lever, Workable, Ashby
- Status updates: Applied → Phone Screen → Interview → Offer
- Calendar integration (interview scheduling)

**Acceptance Criteria:**
- [ ] Extension installed by 500 users
- [ ] 80% accuracy in status detection
- [ ] 3 ATS integrations live

---

## 4. Q4 2026 (Oct-Dec): AI Coach & Enterprise

### Theme: "AI-Powered Career Growth"

#### 4.1 Feature: AI Interview Coach

**User Story:**
*"As a candidate, I want to practice interviews with AI, so I can improve my chances of getting hired."*

**Requirements:**

| Module | Description |
|--------|-------------|
| Mock interviews | Voice-based technical interviews |
| Feedback | Real-time analysis of answers |
| Questions | Database of 500+ questions by role |
| Improvement | Personalized study plan |
| Recording | Review past interviews |

**AI Capabilities:**
- Speech-to-text (Whisper API)
- Answer evaluation (Groq)
- Soft skills assessment
- Technical depth analysis

**Pricing:**
- Included in Premium ($39/mo)
- $19/mo add-on for Pro users

**Acceptance Criteria:**
- [ ] 500 mock interviews conducted
- [ ] 4.0+ average user rating
- [ ] 25% of Premium users use feature weekly

#### 4.2 Feature: Colombia Launch

**Requirements:**
- Job sources: Computrabajo CO, LinkedIn CO
- Local partnerships: Rappi, MercadoLibre Colombia
- Bogotá/Medellín salary benchmarks
- Spanish localization (minor variations)

**Target:** 500 users by end of Q4

#### 4.3 Feature: Salary Benchmarking API

**User Story:**
*"As a developer, I want to know if my salary is competitive, so I can negotiate better."*

**Requirements:**
- Real-time salary data by: role, experience, location, company size
- Anonymous user contributions
- Trend analysis (YoY growth)
- Personalized recommendations

**API Endpoints:**
```
GET /salary/benchmark?role=backend&exp=3&location=buenos-aires
GET /salary/trends?role=frontend&country=argentina
```

**Monetization:**
- Free: Basic benchmarks
- Pro: Detailed reports
- Enterprise: API access for HR teams

---

## 5. Success Metrics

### North Star Metric
**Weekly Active Job Seekers (WAJ):** Users who view ≥1 job or submit ≥1 application per week.

### KPI Dashboard

| Category | Metric | Q2 Target | Q3 Target | Q4 Target |
|----------|--------|-----------|-----------|-----------|
| **Growth** | New users/month | 1,500 | 2,500 | 4,000 |
| | Organic traffic % | 70% | 65% | 60% |
| **Engagement** | WAJ | 1,800 | 5,500 | 15,000 |
| | Jobs viewed/user/week | 8 | 10 | 12 |
| | Applications submitted | 500 | 2,000 | 6,000 |
| **Revenue** | MRR | $8,000 | $15,000 | $25,000 |
| | ARPU | $20 | $22 | $25 |
| | LTV | $180 | $200 | $240 |
| | CAC | $12 | $15 | $18 |
| **Retention** | D1 retention | 45% | 50% | 55% |
| | D30 retention | 25% | 30% | 35% |
| | Churn (monthly) | 8% | 7% | 6% |
| **Product** | Match score accuracy | 85% | 87% | 90% |
| | NPS | 50 | 55 | 60 |
| | Support tickets/user | 0.5 | 0.3 | 0.2 |

### Leading Indicators

- Activation rate (profile completion): Target 80%
- Feature adoption (AI analysis used): Target 60%
- Referral rate: Target 15%
- App store rating: Target 4.5+

---

## 6. User Stories Backlog

### P0 (Critical - Must Have)

1. **Mobile Push Notifications**
   - *As a user, I want instant notifications for 90+ match jobs*
   - Acceptance: < 30s delivery, 90% delivery rate

2. **LinkedIn OAuth**
   - *As a user, I want one-click signup with LinkedIn*
   - Acceptance: 80% adoption rate

3. **Mexico Localization**
   - *As a Mexican user, I want local job sources and salaries*
   - Acceptance: 1,000 users in 90 days

### P1 (High - Should Have)

4. **Recruiter Dashboard v1**
   - *As a recruiter, I want to search and message candidates*
   - Acceptance: 50 recruiters, $5K MRR

5. **AI Matching V2**
   - *As a user, I want culture fit analysis*
   - Acceptance: 85% match accuracy

6. **ATS Chrome Extension**
   - *As a user, I want auto application tracking*
   - Acceptance: 500 installs, 80% accuracy

### P2 (Medium - Nice to Have)

7. **AI Interview Coach**
   - *As a user, I want to practice with AI*
   - Acceptance: 500 interviews, 4.0+ rating

8. **Colombia Launch**
   - *As a Colombian user, I want local jobs*
   - Acceptance: 500 users

9. **Salary API**
   - *As a developer, I want compensation data*
   - Acceptance: 100 API calls/day

### P3 (Low - Future)

10. **Brazil Launch** (Portuguese required)
11. **Enterprise SSO** (SAML/OAuth)
12. **Team Plans** (for bootcamps/universities)

---

## 7. Technical Debt Plan

### Current Technical Debt

| Issue | Severity | Impact | Plan |
|-------|----------|--------|------|
| SQLite in production | High | Scaling limit | Migrate to PostgreSQL (Q2) |
| Monolithic API | Medium | Deploy risk | Modularize by domain (Q3) |
| No caching layer | Medium | Response times | Redis implementation (Q2) |
| Manual deployment | Medium | Human error | CI/CD automation (Q2) |
| Limited test coverage | Low | Bug risk | 90% coverage target (Q3) |
| No monitoring | High | Blind spots | APM setup (Q2) |

### Q2 Debt Sprints

**Sprint 1-2: Infrastructure**
- PostgreSQL migration (Supabase)
- Redis setup (caching + sessions)
- CI/CD pipeline (GitHub Actions)
- Monitoring (Sentry + PostHog)

**Sprint 3-4: Code Quality**
- Test coverage improvement (85% → 90%)
- API documentation (OpenAPI)
- Dependency updates
- Security audit

### Q3 Debt Sprints

**Sprint 1-2: Modularization**
- Extract auth service
- Extract job service
- Message queue (Redis/Celery)
- API gateway (Kong/AWS API GW)

**Sprint 3-4: Performance**
- Database query optimization
- N+1 query elimination
- Async job processing
- CDN for static assets

---

## 8. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LinkedIn API changes | Medium | High | Multiple job sources, not dependent |
| Groq pricing increase | Low | High | Fallback to self-hosted LLaMA |
| Competitor launches | Medium | Medium | Speed to market, AI moat |
| Economic downturn | Medium | High | Freemium model, B2B diversification |
| Mexico adoption slow | Medium | High | Local partnerships, aggressive GTM |
| Mobile app delays | Medium | Medium | React Native, experienced dev |
| Regulatory (GDPR) | Low | Medium | Privacy by design, EU legal review |

### Contingency Plans

**If Mexico launch underperforms:**
- Pivot to Colombia/Brazil earlier
- Double down on B2B recruiter revenue
- Increase paid acquisition spend

**If Groq becomes expensive:**
- Deploy Llama 70B on RunPod/Vast.ai
- Optimize with caching (70% of CVs are similar)
- Implement tiered AI (free = basic, paid = advanced)

---

## 9. Dependencies

### External APIs

| Service | Usage | SLA Required | Fallback |
|---------|-------|--------------|----------|
| Groq | AI analysis | 99.9% | Self-hosted LLaMA |
| Stripe | Payments | 99.99% | MercadoPago |
| LinkedIn | OAuth + jobs | 99.5% | Email signup + other sources |
| Supabase | Database | 99.9% | Self-hosted PostgreSQL |
| Telegram | Bot | 99.5% | Web dashboard only |

### Team Dependencies

| Role | Q2 | Q3 | Q4 |
|------|----|----|----|
| Backend Engineer | 1 → 2 | 2 | 2 → 3 |
| Frontend/Mobile | 1 → 2 | 2 | 2 → 3 |
| AI/ML Engineer | 0 → 1 | 1 | 1 |
| Product Manager | 0.5 | 0.5 → 1 | 1 |
| Growth/Marketing | 0.5 | 0.5 → 1 | 1 |

---

## 10. Appendix

### A. Competitive Analysis Updates

| Feature | Huntr | Teal | JobBot (Now) | JobBot (Q4) |
|---------|-------|------|--------------|-------------|
| LATAM focus | ❌ | ❌ | ✅ | ✅✅ |
| AI matching | ⚠️ | ✅ | ✅ | ✅✅ |
| Mobile app | ✅ | ✅ | ❌ | ✅ |
| Interview coach | ❌ | ✅ | ❌ | ✅ |
| Recruiter tools | ❌ | ✅ | ❌ | ✅ |
| ATS integrations | 5 | 8 | 0 | 5 |
| Pricing | $15/mo | $9/mo | $9-39/mo | $9-99/mo |

### B. User Feedback Summary

**Top Requests (from 200+ survey responses):**
1. Mobile app (78%)
2. LinkedIn integration (65%)
3. More job sources (52%)
4. Interview prep (48%)
5. Salary data (45%)

**Pain Points:**
- "I miss good jobs because I'm not checking Telegram"
- "Applying is still manual, wish it was one-click"
- "Want to know if my salary ask is reasonable"
- "Need help preparing for technical interviews"

### C. Market Research

**LATAM Tech Workforce:**
- Total developers: 1.2M (growing 25% YoY)
- Remote workers: 400K (expected 800K by 2027)
- Average job search duration: 3.5 months
- Average applications per job: 200+ (juniors), 50+ (seniors)

**TAM/SAM/SOM Update:**
- TAM: $2.4B (LATAM HR tech by 2027)
- SAM: $180M (developer-focused tools)
- SOM: $12M (3% market share by 2027)

---

**Document Owner:** Product Team  
**Review Cycle:** Monthly  
**Last Updated:** April 2026  
**Next Review:** May 1, 2026
