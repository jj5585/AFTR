# AFTR — Production Deployment Guide & Staging Runbook

> **Target Release**: Private Beta Release Candidate (`v0.9.0-rc1`)  
> **Environment**: SRM Closed Campus Private Beta (Staging & Staged Production)  
> **Policy**: Strict zero-automatic-public-deployment policy. All releases require manual promotion and verification.

---

## 1. High-Level Architecture Overview

AFTR utilizes a decoupled modern architecture designed for maximum fault tolerance, pseudonymity isolation, and horizontal scalability:

```
                      ┌────────────────────────────────────────┐
                      │             Vercel Edge                │
                      │     Next.js 14 App Router (Web)        │
                      │   Strict Security Headers & CSP Edge   │
                      └──────────────────┬─────────────────────┘
                                         │
                               HTTPS / WSS (TLS 1.3)
                                         │
                      ┌──────────────────▼─────────────────────┐
                      │         Managed FastAPI Backend        │
                      │   Multi-Stage Container (Non-Root UID) │
                      │  Sliding Window Rate Limiter & Guards  │
                      └─────────────┬─────────────────┬────────┘
                                    │                 │
              SQLAlchemy (AsyncPG)  │                 │ Redis Sentinel / Cluster
              via PgBouncer (:6543) │                 │ (:6379 TLS)
                                    ▼                 ▼
                      ┌──────────────────┐  ┌──────────────────┐
                      │     Supabase     │  │  Managed Redis   │
                      │  PostgreSQL 16   │  │   Sliding Rate   │
                      │  Encrypted Data  │  │   Limits & State │
                      └──────────────────┘  └──────────────────┘
```

---

## 2. Infrastructure Components

### 2.1 Frontend: Vercel (Edge Runtime & Node SSR)
- **Framework**: Next.js 14 App Router (`apps/web`).
- **Build Output**: Static assets with SSR edge handlers.
- **Edge Security**: Managed via [`apps/web/vercel.json`](../apps/web/vercel.json):
  - `Content-Security-Policy`: Disallows unauthorized origins, forbids `eval`, enforces strict frame ancestors (`'none'`).
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()` (strict no-GPS policy).
- **Environment Separation**:
  - `NEXT_PUBLIC_API_URL`: Backend API base URL.
  - `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL.
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Public anonymous API key (*never service-role*).

### 2.2 Backend: Managed FastAPI Container (Google Cloud Run / AWS ECS / Render)
- **Containerization**: Hardened multi-stage Docker build ([`backend/Dockerfile`](../backend/Dockerfile)).
- **Execution User**: Non-root `aftruser:aftrgroup` (`UID 1001`).
- **Process Manager**: `uvicorn` with configurable worker count (`WEB_CONCURRENCY=4`).
- **Healthcheck Probe**: `GET /api/v1/health` responding `{ "status": "healthy", "service": "AFTR API" }`.
- **Graceful Shutdown**: SIGTERM handling with connection draining (15s grace window).

### 2.3 Database: Supabase PostgreSQL 16
- **Connection Modes**:
  - **Transaction Mode** (`port 6543` via PgBouncer) for FastAPI application pooling.
  - **Session Mode** (`port 5432` direct) reserved exclusively for Alembic migrations.
- **Schema Management**: Controlled entirely through Alembic migrations (`backend/alembic/versions/`).
- **Encryption at Rest**: AES-256 block-level encryption managed by AWS KMS / Supabase.
- **Row-Level Privacy**: Real emails and auth UUIDs reside strictly in the isolated identity layer and are never linked into public queries.

### 2.4 Caching & Rate Limiting: Managed Redis 7
- **Engine**: Redis 7.x with TLS enabled.
- **Capabilities**:
  - Distributed sliding-window rate limiting (`backend/app/core/rate_limiter.py`).
  - IP-based anonymous sliding counters with SHA-256 salted keys.
  - Presence and ephemeral heartbeat tracking for realtime messaging.

---

## 3. Environment Variables & Production Secrets

All production secrets must be provisioned through secure secret managers (e.g., Doppler, AWS Secrets Manager, or Google Cloud Secret Manager).

| Variable Name | Environment | Description | Sensitivity |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | PostgreSQL connection string (`postgresql+asyncpg://...`) | **CRITICAL** |
| `REDIS_URL` | Backend | Redis connection string (`rediss://...`) | **HIGH** |
| `SUPABASE_JWT_SECRET` | Backend | Secret used to verify client JWT signatures | **CRITICAL** |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | Administrative key for server-to-server operations (*never client-facing*) | **CRITICAL** |
| `INVITATION_SALT` | Backend | Salt for recipient email HMAC SHA-256 generation | **CRITICAL** |
| `MESSAGE_ENCRYPTION_KEY` | Backend | Fernet 32-byte URL-safe base64 key for resting message encryption | **CRITICAL** |
| `SECURITY_ADMIN_MFA_SECRET` | Backend | Master base32 secret for RFC 6238 TOTP admin validation | **CRITICAL** |
| `CORS_ORIGINS` | Backend | Comma-delimited list of permitted domains (`https://aftr.app,https://beta.aftr.app`) | **MEDIUM** |
| `ENVIRONMENT` | Backend | `staging` or `production` | **LOW** |
| `NEXT_PUBLIC_API_URL` | Frontend | Public URL for backend API | **LOW** |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend | Public Supabase project URL | **LOW** |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`| Frontend | Supabase anonymous public key | **LOW** |

> [!CAUTION]
> Under no circumstances may `SUPABASE_SERVICE_ROLE_KEY`, `INVITATION_SALT`, or `MESSAGE_ENCRYPTION_KEY` be prefixed with `NEXT_PUBLIC_` or bundled into client builds. CI pipeline checks reject builds containing forbidden keys in frontend bundles.

---

## 4. Staging & Beta Deployment Workflow

### Step 1: Pre-Deployment Verification
Before pushing a release candidate to staging:
```bash
# 1. Run full backend test suite (unit, integration, security review)
cd backend
.venv/bin/pytest -v

# 2. Run frontend lint and production build
cd ../apps/web
npm run lint
npm run build
```

### Step 2: Database Migration Execution
Database migrations must be applied using a one-off task runner before promoting container revisions:
```bash
# Execute Alembic migrations against target database
cd backend
DATABASE_URL="postgresql+asyncpg://aftr_admin:${DB_PASSWORD}@${DB_HOST}:5432/aftr_db" \
  .venv/bin/alembic upgrade head
```

### Step 3: Backend Container Build & Deployment
Build the hardened multi-stage Docker container:
```bash
# Build multi-stage image
docker build -t aftr-backend:v0.9.0-rc1 -f backend/Dockerfile .

# Push to private container registry (e.g. Google Artifact Registry)
docker tag aftr-backend:v0.9.0-rc1 gcr.io/aftr-infra/backend:v0.9.0-rc1
docker push gcr.io/aftr-infra/backend:v0.9.0-rc1

# Deploy to Cloud Run / ECS with health check configuration
gcloud run deploy aftr-api-staging \
  --image gcr.io/aftr-infra/backend:v0.9.0-rc1 \
  --platform managed \
  --region us-central1 \
  --port 8000 \
  --min-instances 1 \
  --max-instances 5 \
  --env-vars-file .env.staging.yaml
```

### Step 4: Frontend Deployment (Vercel)
Deploy to Vercel preview/staging:
```bash
cd apps/web
vercel deploy --prebuilt
# Run smoke tests on preview URL before promoting:
vercel promote <DEPLOYMENT_URL>
```

---

## 5. Health Monitoring & Observability

### 5.1 Health Probe Endpoints
The backend exposes dedicated probes:
- **Liveness Probe**: `GET /api/v1/health`
  - Validates process responsiveness.
  - Expected Response: `200 OK`
  ```json
  {
    "status": "healthy",
    "service": "AFTR API"
  }
  ```
- **Readiness Probe**: Included in health probe routing to confirm DB pool and Redis connectivity.

### 5.2 Metrics & Logging Standards
- **Zero Sensitive Data Logging**:
  - Email addresses, raw tokens, message bodies, and passwords are never written to standard output.
  - Rate limiting logs IP hashes (`HMAC_SHA256(ip, salt)[:16]`) instead of raw IPv4/IPv6 addresses.
- **Alert Triggers**:
  - `5xx` error rate > 1% over 5 minutes -> **Sev 2 PagerDuty**.
  - Rate limiter triggers (`429`) > 100 per minute on `/auth/*` -> **Sev 2 Security Alert**.
  - Database pool exhaustion (> 85% connection utilization) -> **Sev 2 Performance Alert**.

---

## 6. Backup & Point-in-Time Recovery (PITR)

### 6.1 Automated Backup Schedule
- **Physical Snapshots**: Daily full backups at 03:00 UTC with 30-day retention.
- **WAL Archiving**: Continuous Write-Ahead Logging streamed to offsite multi-region storage (S3/GCS bucket with immutable Object Lock).
- **Recovery Point Objective (RPO)**: < 5 minutes.
- **Recovery Time Objective (RTO)**: < 30 minutes.

### 6.2 Point-in-Time Restoration Procedure
In the event of database corruption or catastrophic failure:
1. Identify the target timestamp prior to the incident (e.g., `2026-11-18 04:15:00 UTC`).
2. Provision a new Supabase restore instance pointing to the WAL backup.
3. Verify table counts and integrity on the restored instance:
   ```sql
   SELECT count(*) FROM accounts;
   SELECT count(*) FROM anonymous_personas;
   SELECT count(*) FROM invitations;
   ```
4. Update `DATABASE_URL` secret in secret manager to redirect backend traffic to restored cluster.
5. Cycle backend container instances.

---

## 7. Deployment Rollback Procedures

### 7.1 Instant Frontend Rollback (Vercel)
If a frontend defect is detected in staging or beta:
1. Open Vercel Dashboard -> Deployments.
2. Select previous known-good deployment (e.g., commit `58d8a58`).
3. Click **Instant Rollback**. Traffic routes to the prior bundle within ~3 seconds without rebuilding.

### 7.2 Backend Container Rollback
If a defect is observed in API responses:
```bash
# Roll back to the preceding container revision
gcloud run services update-traffic aftr-api-staging \
  --to-revisions=aftr-api-staging-v0-8-9=100
```

### 7.3 Database Schema Rollback
If a migration introduces an issue before new schema features are actively written:
```bash
cd backend
# Revert exactly one migration revision
DATABASE_URL="..." .venv/bin/alembic downgrade -1
```

> [!WARNING]
> Schema rollbacks that drop columns must never be executed while old code revisions that expect those columns are still servicing requests. Always roll back application containers first, then evaluate database state.
