# DeepAudit

AI-powered fraud detection system for government benefits auditors. Analyzes unemployment benefit applications, detects fraud patterns using a 10-rule engine, and generates natural language recommendations via Claude AI.

## Quick Start

### Prerequisites
- PostgreSQL running locally
- Python 3.11+
- Node.js 20+
- Anthropic API key

### 1. Backend

```bash
cd deepaudit/backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATABASE_URL and ANTHROPIC_API_KEY
```

Create the database and start the server:

```bash
createdb deepaudit
uvicorn app.main:app --reload
```

API + interactive docs: http://localhost:8000/docs

### 2. Seed the database

```bash
# With the venv active, from backend/ directory:
python -m app.seed.seed
```

This creates ~50 applicants with 4 planted fraud patterns plus 35 clean control applicants, runs the fraud engine on all of them, and calls Claude for AI recommendations on high-risk cases.

### 3. Frontend

```bash
cd deepaudit/frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Features

### Dashboard (`/`)
- Application queue table sorted by risk score (highest risk first)
- Risk score distribution bar chart + status breakdown pie chart
- Filter sidebar: status checkboxes, risk score range, program type
- Color-coded risk badges — green (0–30) / yellow (31–60) / orange (61–80) / red (81–100)
- AI recommendation chips (approve / deny / investigate) on each row

### Application Detail (`/applications/:id`)
Three-column layout:
- **Left** — Applicant demographics, address, financial records, employment history timeline, weekly certifications table
- **Center** — Risk score gauge, fraud signals list (each with rule ID, severity, score contribution, and evidence metadata), Re-analyze button
- **Right** — Claude AI recommendation card (headline, plain-English explanation, key signals, suggested action) + Auditor decision buttons (Approve / Deny / Flag)

### Fraud Network Graph (`/graph`)
- Interactive node graph (React Flow + dagre layout) showing connected fraud networks
- Edge colors: shared bank (red) · shared device (orange) · shared IP (yellow) · shared address (purple)
- Animated edges for bank connections
- Click any node → sidebar with applicant summary + link to full application
- Min-risk slider + relationship type toggles to control graph density

---

## Fraud Detection Rules

| Rule | Signal Type | Weight | Trigger |
|---|---|---|---|
| RULE_001 | still_employed_check | 20 | Layoff claimed but employment end date is in the future or missing |
| RULE_002 | income_during_claim | 15 | Financial records show income inconsistent with zero-earnings certifications |
| RULE_003 | shared_bank_account | 15 | Same bank account used by multiple unrelated applicants |
| RULE_004 | shared_device_fingerprint | 12 | Same device fingerprint across multiple applications |
| RULE_005 | shared_ip_address | 10 | Same IP linked to 3+ applications in 30 days |
| RULE_006 | duplicate_ssn | 20 | SSN appears on more than one applicant record |
| RULE_007 | out_of_state_usage | 8 | Weekly certifications submitted from a different state than the registered address |
| RULE_008 | bulk_submission_timing | 5 | Application submitted within 60 seconds of 5+ others |
| RULE_009 | fake_job_search | 8 | Job search contacts reported as exactly the same number every week |
| RULE_010 | deceased_applicant | 20 | Applicant flagged as deceased |

**Risk score** = min(100, sum of triggered rule weights)

---

## Seed Data — Planted Fraud Patterns

| Pattern | Applicants | Signals |
|---|---|---|
| **A — Fraud Ring** | Alice Johnson, Bob Martinez, Carol White | Shared bank + shared device + bulk timing + still employed |
| **B — Income Misreporting** | David Kim, Emily Chen, Frank Torres, Grace Liu | Income during claim + fake job search (always exactly 3 contacts) |
| **C — Device Cluster** | James Wright, Maria Gonzalez + 3 others | Shared device + shared IP + out-of-state certifications |
| **D — Deceased Applicant** | Harold Graves (DOB 1935, age 91) | Deceased flag + shared device |
| **E — Clean Control** | 35 random applicants | None / minor signals only |

---

## Architecture

```
backend/
  app/
    models/          SQLAlchemy 2.0 ORM models (10 tables)
    schemas/         Pydantic response shapes
    routers/         FastAPI route handlers
    services/
      fraud_engine.py    10-rule rules engine
      claude_service.py  Claude API with prompt caching
      graph_service.py   Network graph builder
    seed/            Realistic mock data with planted fraud

frontend/
  src/
    api/client.ts    Typed Axios API functions
    types/           TypeScript interfaces mirroring backend schemas
    components/      RiskBadge, StatusBadge, SignalCard, AuditorActions
    pages/           Dashboard, ApplicationDetail, FraudGraph
    hooks/           React Query hooks (useApplications, useApplication, useGraph)
```

### AI Integration
Claude API is called with the full fraud signal context for each high-risk application. The system prompt is cached (`cache_control: ephemeral`) to reduce token cost by ~90% on repeated calls. Claude returns structured JSON: recommendation, confidence, headline, explanation, key signals, and suggested action.

### Extensibility
The `program_type` field on `Application` is the single extension point. To add Medicare, SNAP, or Disability:
1. Add the value to the `ProgramType` enum
2. Create program-specific history tables (e.g., `MedicalClaimHistory`)
3. Add new fraud rules to the engine

Core tables, all API routes, Claude integration, and the entire frontend require zero changes.

---

## Demo Walkthrough

1. **Fraud Ring** — Search for "Alice Johnson" in the dashboard. Open her application. See RULE_001 (still employed), RULE_003 (shared bank with 2 others), RULE_008 (bulk timing). Claude recommends "deny".
2. **Deceased Identity** — Find "Harold Graves" (age 91, risk score 95+). RULE_010 critical signal, deceased flag shows in red.
3. **Network Graph** — Go to Fraud Graph, set min_risk=40. The fraud ring (Alice, Bob, Carol) appears as 3 nodes connected by red animated edges (shared bank). The device cluster appears separately.
4. **Auditor Workflow** — Open any flagged application. Review signals + AI explanation. Click "Deny" → enter your name → confirm. Status updates and the decision is logged.
5. **Re-analyze** — Click "Re-analyze" on any application to re-run the fraud engine and generate a fresh Claude recommendation.
