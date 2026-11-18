# AFTR — Implementation Status & Roadmap

**Current State**: Stage 3 (Authentication and Invitation Gate) Completed  
**Last Updated**: 2026-11-18  
**Architecture Lead**: Antigravity  

---

## 1. Project Overview & Rules Compliance

AFTR is an 18+ anonymous social platform for adult campus communities.

### Non-Negotiable Architectural Principles
| Rule | Status | Implementation Mechanism |
| :--- | :---: | :--- |
| **Invitation-only** | ✅ Enforced (API & Frontend) | All protected routes require verified invitation-redeemed account; strict 72h TTL; 3 slots |
| **No college email verification** | ✅ Enforced | Explicitly omitted; recipient email binding via salted HMAC hashes; no `.edu` requirements |
| **No mandatory college ID** | ✅ Enforced | Prohibited; `campus_affiliations` is purely self-declared and optional |
| **Age assurance (18+)** | ✅ Enforced (Engine & Gate) | Legitimate `AgeAssuranceEngine` generating signed cryptographic proof tokens; no fake checkboxes |
| **Identity / Social separation** | ✅ Enforced | `accounts` (auth credentials/email hash/quota) strictly decoupled from `personas` (display name/avatar) |
| **Consent-based messaging** | ✅ Enforced (DB) | `connection_requests` required before `conversations` and `messages` |
| **Blocking & Reporting** | ✅ Enforced (DB) | `blocks` table with anti-self block constraint & `reports` table |
| **Automated & Human Moderation** | ✅ Enforced (DB) | `moderation_actions`, `appeals`, and immutable `audit_logs` |
| **No explicit images / live location**| ✅ Enforced | `events.location_name` is named venue only; no GPS or explicit image columns |
| **No false anonymity claims** | ✅ Enforced | Pseudonymous isolation with immutable security audit logging for legal compliance |

---

## 2. Implementation Roadmap by Stages

- [x] **Stage 0: Architecture, Threat Model & Repository Documentation**
  - Project directory structure defined
  - Architectural blueprint (`docs/ARCHITECTURE.md`)
  - Threat model and risk mitigation (`docs/SECURITY.md`)
  - Environment variable schema (`.env.example`)
  - Git ignore rules (`.gitignore`)
- [x] **Stage 1: AFTR Project Foundation & Monorepo Architecture**
  - Monorepo directory structure (`apps/web`, `backend/`, `packages/`, `supabase/`, `infrastructure/`, `docs/`)
  - Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui primitives, Lucide icons, responsive layout
  - FastAPI modular backend with Pydantic v2 settings, SQLAlchemy 2.0 async engine, greenlet, Alembic
  - Infrastructure: Docker Compose, PostgreSQL 16, Redis 7
  - Packages: `@aftr/shared-types`, `@aftr/validation`
  - Health & liveness verification bridges
- [x] **Stage 2: Database Implementation & Relational Schemas**
  - 20 Logical Domains mapped to SQLAlchemy 2.0 ORM models
  - 5 Sequenced & Applied Alembic Migrations (`001` through `005`)
  - PostgreSQL Row Level Security (RLS) & PL/pgSQL atomic redemption function
  - Development seed script (`backend/scripts/seed.py`)
- [x] **Stage 3: Authentication and Invitation Gate**
  - Supabase JWT backend verification dependency (`get_current_account`, `get_current_persona`)
  - Complete Invitation Gate Endpoints:
    - `POST /api/v1/invitations` (Issue 72h single-use invitation, decrement quota)
    - `GET /api/v1/invitations` (List user's issued invitations)
    - `GET /api/v1/invitations/quota` (Quota metrics: 3 slots max, remaining, issued, redeemed)
    - `POST /api/v1/invitations/validate` (Public check for VALID, EXPIRED, REVOKED, ALREADY_REDEEMED, NOT_FOUND)
    - `POST /api/v1/invitations/claim` (Recipient email binding validation, returns 30-min signed claim ticket)
    - `POST /api/v1/invitations/redeem` (Atomic redemption, age proof validation, account & persona creation)
    - `DELETE /api/v1/invitations/{id}` (Revocation of unredeemed invitations)
  - Legitimate Age Assurance Engine (`AgeAssuranceEngine` with signed `AGE_ASSURANCE_PROOF` tokens)
  - Auth APIs: `/auth/age/initiate`, `/auth/age/verify`, `/auth/me`, `/auth/logout`, `/auth/recover-password`
  - Frontend Screens:
    - `/login`: Email & password authentication with invite-only notice
    - `/register`: Invitation gate redirector
    - `/invite`: 32-character token entry
    - `/invite/[token]`: Live validation and state screens (`VALID`, `EXPIRED`, `REVOKED`, `ALREADY_REDEEMED`, `NOT_FOUND`)
    - `/onboarding`: 4-step guided onboarding (Age Assurance, Policies, Anonymous Persona setup, Entrance)
  - Automated Tests: **35/35 test suites passing**
- [ ] **Stage 4: Anonymous Personas, Safety, Moderation & Reporting Foundation**
  - Universal block engine
  - Content reporting pipeline
  - Word-filter & regex moderation pre-processor
  - Moderator review queue endpoints
- [ ] **Stage 5: Confessions & Adult Discussion Feeds**
  - Confession CRUD and lifecycle management
  - Adult interest tag taxonomy & NSFW/sensitive content toggles
  - Anonymous reactions (upvotes, reactions without exposing user identity)
  - Threaded anonymous comments
  - Redis rate limiting for anti-spam
- [ ] **Stage 6: Ephemeral Stories & Group Events**
  - Ephemeral 24h anonymous stories with automatic expiration
  - Public group events discovery and creation
  - Event RSVP tracking
  - Self-declared campus filters
- [ ] **Stage 7: Compatibility Matching, Connection Requests & Consent-Based Messaging**
  - Anonymous compatibility questionnaire & affinity scoring
  - Connection request lifecycle (Pending, Accepted, Declined, Withdrawn)
  - Consent-based 1-on-1 private messaging (unlocked strictly upon acceptance)
  - Real-time messaging support (WebSocket / Redis PubSub)
- [ ] **Stage 8: Frontend Application Feature Integration**
  - Anonymous feed UI (Confessions, Stories, Events)
  - Connections & Consent-Based Chat interface
  - Reporting & Safety UI triggers
- [ ] **Stage 9: End-to-End Verification, Security Hardening, Docker & Deployment Readiness**
  - Multi-stage Docker build
  - Production security headers, CORS, and rate limiting audit
  - Deployment configuration for Vercel & FastAPI

---

## 3. Execution Log

| Date | Stage | Action / Changes | Status |
| :--- | :---: | :--- | :---: |
| 2026-11-18 | Stage 0 | Project inspection, system dependency check, architecture blueprint, threat modeling | ✅ Completed |
| 2026-11-18 | Stage 1 | Monorepo layout, Next.js App Router, FastAPI modular monolith, PostgreSQL & Redis containers, Alembic, `@aftr/shared-types`, `@aftr/validation`, test harness, verified live health bridge | ✅ Completed |
| 2026-11-18 | Stage 2 | Implemented 20 domain SQLAlchemy models, 5 sequenced Alembic migrations, PostgreSQL RLS & atomic redemption function, development seed script, 23/23 tests passing | ✅ Completed |
| 2026-11-18 | Stage 3 | Supabase JWT backend verification, 7 endpoints for invitation gate, AgeAssuranceEngine, 5 Next.js screens, 35/35 tests passing | ✅ Completed |
