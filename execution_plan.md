# DeepAudit — Full Execution Plan

## Project Overview

AI-powered fraud detection system for government benefits auditors. Primary use case: **unemployment benefits**. Designed for extensibility to Medicare, SNAP, and Disability.

**Stack:** FastAPI + PostgreSQL (backend) · React + TypeScript + Tailwind (frontend) · Claude API (AI recommendations) · Recharts + React Flow (visualization)

---

## Phase 1: Database Setup (Hour 0–1)

### Prerequisites
- PostgreSQL running locally
- Python 3.11+
- Node.js 20+
- Anthropic API key

### Steps

```bash
# 1. Create database
createdb deepaudit

# 2. Set up Python environment
cd deepaudit/backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL and ANTHROPIC_API_KEY

# 4. Start server (tables auto-created on startup in dev mode)
uvicorn app.main:app --reload
# → Tables created automatically via SQLAlchemy

# 5. Verify in psql
psql deepaudit -c "\dt"
```

### Tables Created (in order of dependency)
1. `applicants` (no FKs)
2. `addresses` → applicants
3. `household_members` → applicants
4. `financial_records` → applicants
5. `applications` → applicants
6. `employment_history` → applications
7. `weekly_certifications` → applications
8. `submission_metadata` → applications (unique)
9. `fraud_signals` → applications
10. `audit_logs` → applications

---

## Phase 2: Seed Data (Hour 1–2)

### Run the seed script
```bash
cd deepaudit/backend
source venv/bin/activate
python -m app.seed.seed
```

### What it creates
| Pattern | Applicants | Key Fraud Signals |
|---|---|---|
| A — Fraud Ring | Alice Johnson, Bob Martinez, Carol White | Shared bank + shared device + bulk timing + still employed |
| B — Income Misreporting | David Kim, Emily Chen, Frank Torres, Grace Liu | Income during claim + fake job search |
| C — Device Cluster | James Wright, Maria Gonzalez + 3 more | Shared device + shared IP + out-of-state |
| D — Deceased Applicant | Harold Graves (DOB 1935) | Deceased flag + shared device |
| E — Clean Control | 35 random applicants | None / minor |

**Total: ~50 applicants, ~50 applications**

### Verification
```sql
-- Check counts
SELECT COUNT(*) FROM applicants;        -- ~50
SELECT COUNT(*) FROM applications;       -- ~50
SELECT COUNT(*) FROM fraud_signals;      -- ~100-150
SELECT risk_score, COUNT(*) FROM applications GROUP BY risk_score ORDER BY risk_score DESC LIMIT 10;
```

---

## Phase 3: Backend API (Hour 2–4)

### Verify all routes work via Swagger UI
Open: http://localhost:8000/docs

| Endpoint | Test |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` |
| `GET /applications?min_risk=70` | Returns Pattern A + D applications |
| `GET /applications/{id}` | Returns full detail with fraud signals |
| `POST /applications/{id}/decision` | `{"action": "deny", "auditor_name": "Test Auditor"}` |
| `POST /fraud/analyze/{id}` | Re-runs engine + Claude, returns updated signals |
| `GET /graph?min_risk=40` | Returns nodes + edges for fraud networks |

### Key implementation files
- `backend/app/services/fraud_engine.py` — 10-rule engine, `run_fraud_analysis()`
- `backend/app/services/claude_service.py` — Claude API with prompt caching
- `backend/app/services/graph_service.py` — Network graph builder
- `backend/app/routers/applications.py` — Main CRUD routes
- `backend/app/routers/fraud.py` — `POST /fraud/analyze/{id}`
- `backend/app/routers/graph.py` — Graph endpoint

---

## Phase 4: Claude AI Integration (Hour 4–5)

### Configuration
Set `ANTHROPIC_API_KEY` in `backend/.env`

### How it works
1. `GET /applications/{id}` fires Claude lazily if `ai_analyzed_at` is null
2. `POST /fraud/analyze/{id}` forces Claude re-analysis synchronously
3. System prompt uses `cache_control: ephemeral` → ~90% token cost reduction on repeated calls

### Claude outputs (stored on `applications` table)
- `ai_recommendation`: "approve" | "deny" | "investigate"
- `ai_confidence`: "low" | "medium" | "high"
- `ai_headline`: one-sentence summary
- `ai_explanation`: 2-4 sentences of reasoning
- `ai_key_signals`: JSON array of signal types
- `ai_suggested_action`: specific next step for auditor

### Fallback behavior
If Claude API is unavailable: recommendation = "investigate", explanation = "AI analysis unavailable — manual review required."

---

## Phase 5: Frontend (Hour 5–10)

### Setup
```bash
cd deepaudit/frontend
npm install
npm run dev
# → http://localhost:5173
```

### Pages
| Route | Component | Key Features |
|---|---|---|
| `/` | `Dashboard.tsx` | Application table, risk/status charts, filters |
| `/applications/:id` | `ApplicationDetail.tsx` | 3-col layout: applicant info / signals / AI panel |
| `/graph` | `FraudGraph.tsx` | React Flow network graph with dagre layout |

### Components
- `RiskBadge.tsx` — Color-coded score chips (green/yellow/orange/red)
- `StatusBadge.tsx` — Status color chips
- `SignalCard.tsx` — Individual fraud signal with severity, rule ID, description, metadata
- `AuditorActions.tsx` — Approve/Deny/Flag buttons + confirmation modal

### Data flow
```
useApplications (React Query) → GET /applications → Dashboard table
useApplication (React Query) → GET /applications/{id} → Detail page
useGraph (React Query) → GET /graph → FraudGraph
useMutation → POST /applications/{id}/decision → status update
useMutation → POST /fraud/analyze/{id} → re-analysis
```

---

## Phase 6: Demo Validation (Hour 10–12)

### Checklist
- [ ] `http://localhost:5173` loads dashboard with 50 applications
- [ ] Risk score distribution chart shows spread across buckets
- [ ] Filter by "high risk" (min_risk=70) shows fraud ring + deceased applicant
- [ ] Click Alice Johnson → 3-col detail view loads
- [ ] Fraud signals show RULE_001 (still employed) + RULE_003 (shared bank) + RULE_008 (bulk timing)
- [ ] AI recommendation panel shows "deny" with explanation
- [ ] Click "Re-analyze" → spinner → updated result
- [ ] Submit "Flag for Review" decision → status updates to "flagged"
- [ ] Fraud Graph page shows fraud ring (red nodes) connected by red "bank" edges
- [ ] Click node in graph → sidebar shows details + "View Full Application" link

---

## Fraud Detection Rules Reference

| Rule ID | Signal Type | Weight | Trigger Condition |
|---|---|---|---|
| RULE_001 | still_employed_check | 20 | separation_reason=laid_off but end_date is future or null |
| RULE_002 | income_during_claim | 15 | Monthly income > 1.5× weekly_benefit×4, with zero-earnings certs |
| RULE_003 | shared_bank_account | 15 | bank_account_hash used by >1 applicant |
| RULE_004 | shared_device_fingerprint | 12 | device_fingerprint used by >1 application |
| RULE_005 | shared_ip_address | 10 | ip_hash linked to >3 apps in 30 days |
| RULE_006 | duplicate_ssn | 20 | ssn_hash appears >1 time in applicants table |
| RULE_007 | out_of_state_usage | 8 | Weekly cert IP state ≠ registered address state |
| RULE_008 | bulk_submission_timing | 5 | App submitted within 60s of 5+ others |
| RULE_009 | fake_job_search | 8 | Job contacts exactly same every week for 3+ weeks |
| RULE_010 | deceased_applicant | 20 | Applicant.is_deceased = True |

**Risk score** = min(100, sum of triggered rule weights)

---

## Extensibility Guide

### Adding a new program type (e.g., Medicare)
1. Add `MEDICARE = "medicare"` to `ProgramType` enum in `backend/app/models/application.py`
2. Create `backend/app/models/medical.py` with `MedicalClaimHistory`, `ProviderRecord` tables
3. Create `backend/app/services/fraud_rules_medicare.py` with Medicare-specific rules
4. Register new rules in `ALL_RULES` list for Medicare applications
5. No changes needed to core routes, Claude integration, or frontend

### Adding a new fraud rule
1. Create a class implementing the `FraudRule` protocol in `fraud_engine.py`
2. Add an instance to `ALL_RULES` list
3. Risk score automatically recalculates

---

## File Map

```
deepaudit/
├── backend/
│   ├── app/
│   │   ├── main.py                    FastAPI app factory
│   │   ├── config.py                  Settings (DATABASE_URL, ANTHROPIC_API_KEY)
│   │   ├── database.py                SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── applicant.py           Applicant, Address, HouseholdMember
│   │   │   ├── application.py         Application (ProgramType, ApplicationStatus enums)
│   │   │   ├── employment.py          EmploymentHistory, WeeklyCertification
│   │   │   ├── financial.py           FinancialRecord
│   │   │   ├── metadata.py            SubmissionMetadata
│   │   │   ├── fraud.py               FraudSignal, SignalSeverity
│   │   │   └── audit.py               AuditLog, AuditAction
│   │   ├── schemas/
│   │   │   ├── application.py         All Pydantic response models
│   │   │   └── graph.py               GraphNode, GraphEdge, GraphData
│   │   ├── routers/
│   │   │   ├── applications.py        GET/POST /applications routes
│   │   │   ├── fraud.py               POST /fraud/analyze/{id}
│   │   │   └── graph.py               GET /graph
│   │   ├── services/
│   │   │   ├── fraud_engine.py        10 fraud rules + run_fraud_analysis()
│   │   │   ├── claude_service.py      Claude API + prompt caching
│   │   │   └── graph_service.py       build_graph()
│   │   └── seed/
│   │       ├── patterns.py            5 fraud pattern definitions (constants)
│   │       └── seed.py                Seed orchestrator
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/client.ts              Typed API functions (axios)
    │   ├── types/index.ts             TypeScript interfaces
    │   ├── components/
    │   │   ├── RiskBadge.tsx
    │   │   ├── StatusBadge.tsx
    │   │   ├── SignalCard.tsx
    │   │   └── AuditorActions.tsx
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── ApplicationDetail.tsx
    │   │   └── FraudGraph.tsx
    │   └── hooks/
    │       ├── useApplications.ts
    │       ├── useApplication.ts
    │       └── useGraph.ts
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── tsconfig.json
```
