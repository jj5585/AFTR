# AFTR — Implementation Status & Roadmap

**Current State**: Stage 5 (Anonymous Social Feed) Completed  
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
- [x] **Stage 4: AFTR Design System and Frontend**
  - Brand identity: **AFTR** — *"Meet without revealing."*
  - Strict color tokens applied: Background `#111016`, Surface `#1C1923`, Primary `#9B72CF`, Accent `#DCA7E8`, Text `#F6F1FA`, Secondary `#A49BAF`, Danger `#E56A75`, Success `#62C49A`
  - Typography: Geist Sans & Geist Mono with smooth anti-aliasing
  - Navigation Framework:
    - Desktop: Left sidebar (Logo, 9 navigation items, invitation quota counter, current persona pill)
    - Center: Main content area
    - Desktop: Optional right discovery panel (Trending topics, upcoming campus gatherings, zero surveillance charter)
    - Mobile: Compact top header and bottom navigation bar
  - All 15 AFTR Components Implemented:
    1. `AnonymousPersona`: Visual avatar seed graphic, display name, self-declared campus badge, zero identity link
    2. `AnonymousPostCard`: Tag badges, sensitive/adult blur overlay toggle, confession text, relative timestamp, reaction bar, comments link, report & block actions
    3. `CategorySelector`: Horizontal scrollable category pills with active purple gradients
    4. `ReactionBar`: Interactive anonymous reactions (Upvote, Flame, Relatable Heart, Insightful Sparkles) with active count toggles
    5. `CommentList`: Threaded nested anonymous comments, OP indicators, inline reply input, and reporting
    6. `PostComposer`: Confession and adult discussion composer, category picker, character counter, sensitive flag, and **real-time PII & Identity Leak Shield** (detects phone numbers, emails, student IDs, and social handles)
    7. `ConnectionCard`: Anonymous compatibility card, percentage match meter, shared adult interests, declared campus, and consent-based connection request action
    8. `ChatRequestCard`: Inbound/outbound connection request card with accept, decline, and block options
    9. `ConversationWindow`: 1-on-1 private messaging window for accepted connections with mutual consent badge, chronological bubble stream, and message composer
    10. `InvitationCard`: Shareable single-use invitation details, copy-to-clipboard with check feedback, 72h countdown timer, recipient binding mask, and revocation
    11. `InvitationQuota`: Visual meter of the 3 allocated invitation slots, product rule enforcement note, and single-use token issuance workflow
    12. `ReportDialog`: Accessible modal for reporting content with violation category taxonomy and review feedback
    13. `BlockDialog`: Accessible modal for universal persona blocking with clear explanation of privacy protection
    14. `EventCard`: Public campus gathering card with title, date, landmark venue name (strictly no GPS), attendee count, and anonymous RSVP toggling
    15. `SafetyNotice`: Dismissible safety notice detailing the 18+ adult assurance, zero college email surveillance, and mutual consent guarantees
  - All 16 Specified Pages Fully Functional:
    1. `/` (Landing page with brand hero, feature pillars, 18+ assurance, and live backend health bridge)
    2. `/login` (Supabase email/password login with invitation gate redirector)
    3. `/register` (Invitation-bound member registration)
    4. `/invite` (Single-use token entry and verification)
    5. `/onboarding` (4-step onboarding: AgeAssuranceEngine cryptographic verification, policies, persona setup, completion)
    6. `/feed` (Campus confessions & adult discussions feed with category filter and quick composer)
    7. `/discover` (Compatibility discovery with search and interest filtering)
    8. `/create` (Dedicated anonymous post composer with real-time PII shield)
    9. `/post/[id]` (Detailed post view with full threaded comments and OP indicators)
    10. `/chats` (Private conversations list and pending connection requests manager)
    11. `/chats/[id]` (1-on-1 direct private conversation window)
    12. `/stories` (24-hour ephemeral stories board with self-destructing thoughts and composer)
    13. `/events` (Campus group events board with landmark venue and anonymous RSVPs)
    14. `/profile` (Anonymous persona manager, self-declared campus editor, and invitation quota manager)
    15. `/settings` (18+ Age assurance verification badge, content filters, blocked personas list, session sign out)
    16. `/admin` (Moderation review queue, content takedown, persona suspension, and immutable audit log stream)
  - Quality & Verification:
    - `npm run lint` -> 0 errors, 0 warnings
    - `npm run build` -> Static page optimization passed for all routes
    - HTTP 200 response verified on all 17 frontend endpoints
    - Pytest backend test suite: **35/35 tests passing**
- [x] **Stage 5: Anonymous Social Feed**
  - **Anonymous Posts API**: `POST /api/v1/posts`, `GET /api/v1/posts`, `GET /api/v1/posts/me`, `GET /api/v1/posts/{id}`, `DELETE /api/v1/posts/{id}`
  - **Categories**: Confessions, Dating, Questions, Experiences, Campus life, Adult interests (strictly moderated)
  - **Threaded Comments**: `POST /api/v1/posts/{id}/comments`, `GET /api/v1/posts/{id}/comments`, `DELETE /api/v1/posts/comments/{id}`, nested parent-child replies with `is_op` flag
  - **Disabling Comments**: `allow_comments: bool` on posts; rejected with 403 Forbidden when disabled
  - **Anonymous Reactions**: `POST /api/v1/posts/{id}/reactions` (`UPVOTE`, `FLAME`, `HEART`, `INSIGHTFUL`), toggle-off support, reaction summary aggregation
  - **Post Deletion & Ownership**: Author-only deletion (soft delete with `is_deleted = True`), 403 Forbidden for non-authors
  - **Pre-Publication Moderation**: `ContentModerationEngine` evaluating PII patterns (phone numbers, emails, roll numbers, social handles) and severe harm expressions before saving
  - **Universal Blocking & Bilateral Feed Isolation**: `POST /api/v1/blocks`, `DELETE /api/v1/blocks/{persona_id}`, anti-self block constraint, feeds exclude both blocked and blocking personas' posts and comments
  - **Campus Affiliation Filters**: Self-declared campus query parameter `campus=Bay Area University`
  - **Trending Feed**: Dynamic sorting `sort=trending` based on weighted reaction and comment counts with time decay
  - **Keyset Cursor Pagination**: Base64 opaque cursor token `(created_at, id)` with `has_more` and `next_cursor`
  - **Automated Reporting & Audit Logs**: `POST /api/v1/reports` with immutable audit log recording
  - **Frontend Feed Integration**: `apps/web/src/lib/api.ts` connecting `/feed`, `/create`, `/post/[id]`, `AnonymousPostCard`, `PostComposer`, `ReportDialog`, and `BlockDialog`
  - **Automated Tests**: **44/44 test suites passing** (including 9 comprehensive social feed tests)
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
| 2026-11-18 | Stage 4 | AFTR Design System & Frontend: exact brand color tokens, Desktop left sidebar & right discovery panel, Mobile compact header & bottom navigation, all 15 AFTR components, all 16 pages, 0 lint errors, Next.js build passed (18/18 routes), all 17 live routes tested OK 200, 35/35 pytest tests passing | ✅ Completed |
| 2026-11-18 | Stage 5 | Anonymous Social Feed: Alembic migration 006, ContentModerationEngine, Keyset Cursor Pagination, 6 post categories, threaded comments, disabling comments, anonymous reactions, post deletion ownership enforcement, universal bilateral blocking, self-declared campus filtering, trending feed, frontend API integration, 44/44 pytest tests passing | ✅ Completed |
