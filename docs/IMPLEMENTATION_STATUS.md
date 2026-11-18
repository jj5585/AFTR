# AFTR — Implementation Status & Roadmap

**Current State**: Stage 2 (Database Implementation & Schema Architecture) Completed  
**Last Updated**: 2026-11-18  
**Architecture Lead**: Antigravity  

---

## 1. Project Overview & Rules Compliance

AFTR is an 18+ anonymous social platform for adult campus communities.

### Non-Negotiable Architectural Principles
| Rule | Status | Implementation Mechanism |
| :--- | :---: | :--- |
| **Invitation-only** | ✅ Enforced (DB) | Bound token hash, 72h TTL, single-use, 3 invites per user, atomic redemption function |
| **No college email verification** | ✅ Enforced | Explicitly omitted; only salted hashes stored for auth binding |
| **No mandatory college ID** | ✅ Enforced | Prohibited; `campus_affiliations` is optional and self-declared |
| **Age assurance (18+)** | ✅ Enforced (DB) | `is_age_verified` boolean & `birth_year` on `accounts` |
| **Identity / Social separation** | ✅ Enforced (DB) | `accounts` table strictly partitioned from `personas` table |
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
  - 20 Logical Domains mapped to SQLAlchemy 2.0 ORM models:
    1. Account and identity (`accounts`)
    2. Anonymous personas (`personas`)
    3. Invitations (`invitations`)
    4. Self-declared campus affiliations (`campus_affiliations`)
    5. Posts (`posts`)
    6. Comments (`comments`)
    7. Reactions (`reactions`)
    8. Stories (`stories`)
    9. Interests (`interests`, `persona_interests`)
    10. Connection requests (`connection_requests`)
    11. Matches (`matches`)
    12. Conversations (`conversations`, `conversation_participants`)
    13. Messages (`messages`)
    14. Events (`events`)
    15. Event attendees (`event_attendees`)
    16. Blocks (`blocks`)
    17. Reports (`reports`)
    18. Moderation actions (`moderation_actions`)
    19. Appeals (`appeals`)
    20. Audit logs (`audit_logs`)
  - 5 Sequenced & Applied Alembic Migrations:
    - `001_initial_schema`: Core domain tables, UUID PKs, UTC timestamps, indexes
    - `002_security_lockdown`: Immutable audit logs, RLS policies, `aftr_app` role grant
    - `003_integrity`: Connections, matches, conversations, blocks, reports, moderation
    - `004_invitation_system`: 72h bound invitations, quota checks, check constraints
    - `005_invitation_hardening`: Single-use & revocation integrity, `aftr_redeem_invitation_atomic` PL/pgSQL function
  - Development seed script (`backend/scripts/seed.py`)
  - Automated test suite: 23/23 tests passing (foreign key cascades, invitation expiry, single-use races, account isolation, persona ownership, conversation membership)
- [ ] **Stage 3: Auth Verification, Age Assurance, & Strict Invitation System APIs**
  - Supabase JWT backend verification dependency
  - Single-use, 72h TTL invitations bound to recipient identifier endpoints
  - 3-invite quota allocation on qualification
  - Age assurance gate (18+)
  - Server-side authorization & RBAC
- [ ] **Stage 4: Anonymous Personas, Safety, Moderation & Reporting Foundation**
  - Anonymous persona generator & customizable pseudonyms/avatars
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
  - Onboarding, invite code validation, and age assurance flow
  - Anonymous feed UI (Confessions, Stories, Events)
  - Connections & Consent-Based Chat interface
  - Reporting & Safety UI triggers
- [ ] **Stage 9: End-to-End Verification, Security Hardening, Docker & Deployment Readiness**
  - Integration and end-to-end test suite
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
