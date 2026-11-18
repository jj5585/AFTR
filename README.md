# AFTR — Private Anonymous Campus Social Network (18+)

> **AFTR** is an invitation-only, anonymous social and connection platform engineered specifically for adult (18+) campus communities.

---

## Key Principles & Guardrails

1. **Strictly Invitation-Only**: Access requires a single-use, 72-hour bounded invitation link with HMAC recipient validation.
2. **Quota Seeding**: Every eligible adult member receives 3 invitations upon onboarding.
3. **Zero College Surveillance**: No `.edu` / college email verification and no student ID verifications are ever performed. Campus affiliation is optional and strictly self-declared.
4. **Mandatory Age Assurance**: Server-side enforced adulthood (18+) verification required prior to social interaction.
5. **Identity vs. Persona Isolation**: Authentication accounts (Supabase Auth IDs, email hashes) are structurally decoupled from anonymous personas. Client social APIs never expose account identifiers.
6. **Consent-Gated Messaging**: Private 1-on-1 direct messaging is strictly locked behind a mutual connection request handshake.
7. **No High-Risk MVP Media**: Explicit image uploads and real-time live location tracking are prohibited to prevent non-consensual imagery and stalking.

---

## Monorepo Layout

```
AFTR/
├── apps/
│   └── web/                   # Next.js 14+ (App Router, Tailwind CSS, shadcn/ui)
├── backend/                   # FastAPI Modular Monolith (Python 3.14, SQLAlchemy 2.0, Alembic)
│   ├── app/
│   │   ├── api/v1/            # API version 1 endpoints
│   │   ├── core/              # Config, Database engine, Redis client
│   │   ├── models/            # SQLAlchemy ORM models (UUID PKs, UTC timestamps)
│   │   ├── schemas/           # Pydantic v2 schemas
│   │   └── services/          # Domain services
│   ├── alembic/               # Async database migrations
│   └── tests/                 # Automated pytest suite
├── packages/
│   ├── shared-types/          # TypeScript shared domain models
│   └── validation/            # PII filtering, age validation & input constraints
├── supabase/
│   └── migrations/            # Versioned SQL migrations for Supabase/PostgreSQL
├── infrastructure/            # Multi-container Docker Compose & orchestration
├── docs/                      # Architecture, Security threat model, Implementation status
└── .env.example               # Unified environment variables template
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ (Node 20 recommended) & npm
- Podman or Docker & Docker Compose

### 1. Launch Services (PostgreSQL & Redis)
```bash
podman-compose up -d
# or using docker-compose:
docker compose up -d
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run automated tests
pytest -v

# Start FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to view the application status and live health bridge.

---

## Verification & Health Check

The backend exposes health and liveness probes:
- `GET /` — API service metadata
- `GET /api/v1/health` — Full health verification (API + PostgreSQL + Redis)
- `GET /api/v1/health/live` — Lightweight orchestrator liveness probe
