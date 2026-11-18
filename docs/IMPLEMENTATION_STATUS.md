# AFTR — Implementation Status & Roadmap

**Current State**: Stage 8 (Stories & Meetups) Completed  
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
- [x] **Stage 6: Discovery and Connections**
  - **Alembic Migration 007**: Adds `is_discoverable`, `relationship_intention`, `min_age_preference`, `max_age_preference`, and `dating_preferences_json` to `personas`; adds `note` to `connection_requests`.
  - **Anonymous Discovery Cards**: `GET /api/v1/discovery/feed` returning public pseudonymous cards with compatibility score (65-99%), mutual interests, relationship intention, connection status, and zero identity leakage (no emails, auth IDs, or real names).
  - **Opt-in Discoverability**: Strict enforcement requiring caller to be discoverable (`is_discoverable: bool`) to view feed; non-discoverable personas are completely excluded from candidate feeds.
  - **Interest Selection & Taxonomy**: `GET /api/v1/discovery/interests`, `PUT /api/v1/discovery/preferences` with default taxonomy of adult campus interest tags.
  - **Private Dating Preferences**: `dating_preferences_json` stored securely and used solely for backend compatibility scoring; never serialized in public responses.
  - **Optional Self-Declared Campus & Intention Filters**: Query filters `campus` and `intention` for campus community discovery without `.edu` surveillance.
  - **Bilateral Connection Request Lifecycle**:
    - `POST /api/v1/connections/request`: Send anonymous request with optional intro note.
    - `GET /api/v1/connections/requests`: Inbound & outbound pending request lists.
    - `POST /api/v1/connections/requests/{id}/accept`: Atomic transition to `ACCEPTED`, canonical `Match` record creation, and unlocking private bilateral `Conversation` with participants and delivered intro note.
    - `POST /api/v1/connections/requests/{id}/reject`: Marks `REJECTED`.
    - `POST /api/v1/connections/requests/{id}/withdraw`: Marks `WITHDRAWN`.
    - `GET /api/v1/connections/matches`: Lists mutual matches and unlocked conversation IDs.
  - **Strict Consent-Gated Messaging Barrier**: Messages and conversations cannot exist without bilateral acceptance of a connection request.
  - **Bilateral Block Isolation**: Complete two-way omission across discovery cards, connection requests, and matches.
  - **Frontend Integration**: `apps/web/src/lib/api.ts` connecting `discover/page.tsx`, `ConnectionCard.tsx`, `chats/page.tsx`, and `ChatRequestCard.tsx`.
  - **Automated Tests**: **54/54 test suites passing** (including 10 comprehensive discovery and mutual consent tests).
- [x] **Stage 7: Private Messaging System**
  - **Alembic Migration 008**: Adds `last_message_at`, `blocked_by_persona_id` to `conversations`; `conversation_pseudonym`, `last_read_at` to `conversation_participants`; `is_deleted`, `deleted_at`, `is_encrypted` to `messages`.
  - **Membership Authorization on Every Operation**: All conversation actions (`GET /conversations`, `GET /messages`, `POST /messages`, `DELETE /messages`, `POST /read`, `POST /block`, WebSocket connection) verify participant membership in database before executing; non-members are strictly rejected with 403 Forbidden.
  - **Mutual Consent Verification**: Conversations cannot exist or receive messages without verified bilateral consent (ACCEPTED connection request).
  - **Conversation-Specific Pseudonyms**: Generated deterministic/localized pseudonyms (e.g. `Echo-...` and `Shadow-...`) decoupling conversation messaging from other site personas.
  - **Encrypted Storage at Rest**: Fernet-authenticated AES-128 symmetric encryption (`backend/app/core/encryption.py`) encrypts all message payloads at rest in PostgreSQL.
  - **Zero Message Content Logging**: Strict audit logs record metadata only (`conv_id`, `sender_persona_id`, `msg_id`); message text is never printed or logged to console or storage.
  - **FastAPI Realtime WebSocket Transport**: `/api/v1/ws/conversations/{id}` with JWT authentication, unauthorized subscription prevention, ping/pong health, real-time message broadcasting, typing indicators, and online status.
  - **Message Deletion**: Author-verified soft deletion replacing content with `[This message was deleted]` and broadcasting realtime deletion event.
  - **Conversation Blocking**: Closes conversation, records bilateral block, and returns 403 Forbidden on any future message attempts.
  - **Notification Indicators & Unread Counters**: `last_read_at` tracking with global `GET /conversations/unread-count` and reset upon opening conversation.
  - **Automated Tests**: **62/62 test suites passing** (including 8 comprehensive messaging authorization and security tests).
- [x] **Stage 8: Ephemeral Stories & Group Events**
  - **Alembic Migration 009**: Adds `category`, `allow_comments`, `visibility`, `campus_name`, `moderation_status`, `is_deleted` to `stories`; creates `story_comments` table; adds `is_deleted` and index `ix_events_time_cancelled` to `events`.
  - **Ephemeral 24-Hour Stories**:
    - Automatic 24-hour expiration (`expires_at = utc_now() + timedelta(hours=24)`). Queries enforce `expires_at > now` and `is_deleted == False`.
    - Categories: `night-thoughts`, `campus-life`, `confessions`, `dating`, `creative`.
    - Anonymous reactions: `POST /api/v1/stories/{id}/reactions` (`UPVOTE` toggle).
    - Optional comments: `allow_comments: bool` toggle by author; disabled comments return 403 Forbidden on reply attempts.
    - Visibility: `PUBLIC` vs `CAMPUS`.
    - Pre-publication content moderation: `ContentModerationEngine.evaluate_text` blocking phone numbers, emails, student IDs, and explicit harm.
    - Author-only story deletion (`DELETE /api/v1/stories/{id}`).
  - **Public Group Events (Meetups)**:
    - Required named public venue landmark (`location_name`), date & time in the future (`event_time`).
    - **Venue Safety Non-Negotiables**:
      - **No live location sharing**: Raw GPS coordinates (`^-?\d{1,3}\.\d+[\s,]+-?\d{1,3}\.\d+$`) strictly rejected with 400 Bad Request.
      - **No private home-address publishing**: Residential keywords (`my house`, `my apt`, `dorm room`, `unit #`, `bedroom`) strictly rejected with 400 Bad Request.
    - **Capacity Enforcement**: `max_attendees` prevents overbooking; when capacity is reached, only `INTERESTED` is permitted (`GOING` rejected with 400 Bad Request).
    - **RSVP Lifecycle**: `GOING`, `INTERESTED`, and attendance withdrawal (`DELETE /api/v1/events/{id}/rsvp`).
    - **Organizer Controls**: Updating event, canceling event (`is_cancelled = True`). Non-organizers rejected with 403 Forbidden.
  - **Bilateral Block Isolation**: Blocked users cannot view, react, comment on, or RSVP to each other's stories and events.
  - **Frontend Integration**:
    - `/stories`: Live ephemeral feed with category filter pills, campus toggle, aura gradients, composer with 24h timer, reactions, inline expandable threaded comments, author deletion, and community safety reporting.
    - `/events`: Live gatherings feed with public venue policy notice, campus filter, event creator with venue safety validation, `EventCard` with cancellation status, "At Capacity" badge, interactive RSVP toggle, and organizer cancel button.
  - **Automated Tests**: **70/70 test suites passing** (including 8 comprehensive story & event tests).
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
| 2026-11-18 | Stage 6 | Anonymous Adult Discovery & Connections: Alembic migration 007, Persona discoverability & dating preferences, Interest taxonomy, Anonymous discovery cards with compatibility scoring, bilateral connection request lifecycle (send, accept, reject, withdraw), canonical Match generation, consent-gated conversation unlocking, bilateral block isolation, frontend integration on /discover and /chats, 54/54 pytest tests passing | ✅ Completed |
| 2026-11-18 | Stage 7 | Private Messaging System: Alembic migration 008, encrypted message storage (Fernet/AES-128), zero message content logging, conversation-specific pseudonyms, authorized WebSocket realtime transport, message deletion, conversation blocking, unread notifications, membership verification on every operation, frontend /chats/[id] live integration, 62/62 pytest tests passing | ✅ Completed |
| 2026-11-18 | Stage 8 | Stories & Meetups: Alembic migration 009, 24h ephemeral story lifecycle, story comments & reaction toggles, public group meetups, GPS & private residence blocking, attendance capacity enforcement, RSVP lifecycle (going, interested, withdraw), organizer cancellation controls, bilateral block isolation, frontend /stories and /events integration, 70/70 pytest tests passing | ✅ Completed |
