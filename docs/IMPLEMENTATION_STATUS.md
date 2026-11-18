# AFTR — Implementation Status & Roadmap

**Current State**: Greenfield Initialized  
**Last Updated**: 2026-11-18  
**Architecture Lead**: Antigravity  

---

## 1. Project Overview & Rules Compliance

AFTR is a production-oriented, invitation-only anonymous social and connection platform for adult (18+) campus communities.

### Non-Negotiable Architectural Principles
| Rule | Status | Implementation Mechanism |
| :--- | :---: | :--- |
| **Invitation-only** | ⏳ Planned (Stage 2) | Bound token, 72h TTL, single-use, 3 invites per user |
| **No college email verification** | ✅ Enforced | Explicitly omitted from auth & onboarding flows |
| **No mandatory college ID** | ✅ Enforced | Prohibited; self-declared optional campus affiliation |
| **Age assurance (18+)** | ⏳ Planned (Stage 2) | Mandatory age gate & attested adulthood before access |
| **Identity / Social separation** | ⏳ Planned (Stage 1) | Identity tables (`auth_accounts`) isolated from `personas` |
| **Consent-based messaging** | ⏳ Planned (Stage 6) | 3-way handshake (Pending -> Accepted), mutual consent only |
| **Blocking & Reporting** | ⏳ Planned (Stage 3) | Universal block list and content moderation queue |
| **Automated & Human Moderation** | ⏳ Planned (Stage 3) | Pre-publish keyword filter, reporting threshold triggers |
| **No explicit images / live location**| ✅ Enforced | MVP media schema strictly prohibits image/location fields |
| **No false anonymity claims** | ✅ Enforced | Transparent terms: pseudonymous privacy, not absolute untraceability |

---

## 2. Implementation Roadmap by Stages

- [ ] **Stage 0: Architecture, Data Modeling & Repository Foundation**
  - Project directory structure (`backend/`, `frontend/`, `docs/`)
  - Dependency manifests (`pyproject.toml` / `requirements.txt`, `package.json`)
  - Environment variable schema (`.env.example`)
  - Architecture and Threat Model documentation
- [ ] **Stage 1: Core Backend Infrastructure, Database Schema & Alembic Migrations**
  - FastAPI modular monolith application factory
  - SQLAlchemy 2.0 models with UUID primary keys & UTC timestamps
  - Decoupled Identity vs. Persona schema
  - Alembic migration setup
  - Test harness (`pytest`, async test client, SQLite/PostgreSQL fixture)
- [ ] **Stage 2: Auth Verification, Age Assurance, & Strict Invitation System**
  - Supabase JWT backend verification dependency
  - Single-use, 72h TTL invitations bound to recipient identifier
  - 3-invite quota allocation on qualification
  - Age assurance gate (18+)
  - Server-side authorization & RBAC
- [ ] **Stage 3: Anonymous Personas, Safety, Moderation & Reporting Foundation**
  - Anonymous persona generator & customizable pseudonyms/avatars
  - Universal block engine
  - Content reporting pipeline
  - Word-filter & regex moderation pre-processor
  - Moderator review queue endpoints
- [ ] **Stage 4: Confessions & Adult Discussion Feeds**
  - Confession CRUD and lifecycle management
  - Adult interest tag taxonomy & NSFW/sensitive content toggles
  - Anonymous reactions (upvotes, reactions without exposing user identity)
  - Threaded anonymous comments
  - Redis rate limiting for anti-spam
- [ ] **Stage 5: Ephemeral Stories & Group Events**
  - Ephemeral 24h anonymous stories with automatic expiration
  - Public group events discovery and creation
  - Event RSVP tracking
  - Self-declared campus filters
- [ ] **Stage 6: Compatibility Matching, Connection Requests & Consent-Based Messaging**
  - Anonymous compatibility questionnaire & affinity scoring
  - Connection request lifecycle (Pending, Accepted, Declined, Withdrawn)
  - Consent-based 1-on-1 private messaging (unlocked strictly upon acceptance)
  - Real-time messaging support (WebSocket / Redis PubSub)
- [ ] **Stage 7: Frontend Application (Next.js App Router, Tailwind, shadcn/ui)**
  - Clean Next.js 14+ App Router project structure
  - Onboarding, invite code validation, and age assurance flow
  - Anonymous feed UI (Confessions, Stories, Events)
  - Connections & Consent-Based Chat interface
  - Reporting & Safety UI triggers
- [ ] **Stage 8: End-to-End Verification, Security Hardening, Docker & Deployment Readiness**
  - Integration and end-to-end test suite
  - Multi-stage Dockerfile and `docker-compose.yml`
  - Production security headers, CORS, and rate limiting audit
  - Deployment configuration for Vercel & FastAPI

---

## 3. Current Execution Log

| Date | Stage | Action / Changes | Status |
| :--- | :---: | :--- | :---: |
| 2026-11-18 | Stage 0 | Project inspection, system dependency check, architecture blueprint, threat modeling | In Progress |
