# AFTR — Security Architecture & Threat Model

## 1. Threat Modeling Overview

As an 18+ anonymous campus social network, AFTR operates under distinct privacy, safety, and security requirements. Our threat model explicitly identifies threat actors, attack vectors, and structural mitigations.

| Threat Actor | Motivation | Capability |
| :--- | :--- | :--- |
| **Malicious Peer / Doxxer** | De-anonymize classmates, expose confessions, stalk victims | Social engineering, writing correlation scripts, targeted harassment |
| **University Administrators / Authorities** | Identify student dissidents, enforce student conduct codes | Legal subpoenas, network sniffing, campus Wi-Fi monitoring |
| **Scraper / Botnet Operator** | Harvest invitation links, spam feeds, scrape confessions | Mass API scanning, distributed IP proxies, brute forcing |
| **Underage User (<18)** | Access adult-oriented discussions and confessions | False declarations, circumventing client-side age gates |
| **Compromised Moderator / Insider** | Access DB records, unmask users | Reading database backups, viewing server logs |

---

## 2. Key Threat Vectors & Engineering Mitigations

### 2.1 De-Anonymization via Data Linkage & Query Correlation
- **Risk**: An attacker correlating an `account_id` (containing email/auth ID) with a `persona_id` (author of a sensitive confession).
- **Mitigation**:
  1. Social endpoints (`/confessions`, `/stories`, `/events`, `/messages`) **never** expose foreign keys back to `account_id` or `supabase_user_id`.
  2. Public profiles expose strictly pseudonymous metadata (`display_name`, `avatar_seed`, optional self-declared campus).
  3. No join queries are exposed to client APIs that could leak linkage through timing or GraphQL-like graph expansion.

### 2.2 Invitation Link Forgery & Recipient Impersonation
- **Risk**: An invite code shared in a private message is intercepted, posted on a public forum (e.g. Reddit), and consumed by arbitrary unauthorized users.
- **Mitigation**:
  1. **Cryptographic Recipient Binding**: When user A creates an invite for user B, user A supplies user B's designated identifier (e.g., email or phone number). The database stores `recipient_hash = HMAC_SHA256(recipient_id, secret_salt)`.
  2. During registration, the invitee must present the matching identifier to claim the token. Even if an invite URL is leaked, unauthorized parties cannot redeem it.
  3. **72-Hour Ephemerality**: Every invitation token hard-expires 72 hours after generation (`expires_at = created_at + interval '72 hours'`).
  4. **Single-Use Guard**: Database row update uses atomic conditional state transition `UPDATE invitations SET status = 'USED' WHERE id = :id AND status = 'PENDING'` to prevent race conditions / replay attacks.

### 2.3 Underage Access to Adult Features
- **Risk**: Minors accessing adult campus confession boards and adult interest discussions.
- **Mitigation**:
  1. **Strict Age Gate Enforcement**: Account registration requires explicit age verification (attestation of age 18+ and birth year).
  2. Server-side middleware checks `account.is_age_verified == True` before granting access to adult confession feeds or adult interest tags.
  3. Underage accounts are immediately blocked from adult social routes.

### 2.4 Doxxing, Non-Consensual Imagery & Stalking
- **Risk**: Users uploading explicit photos, sharing revenge porn, or exposing live GPS coordinates.
- **Mitigation**:
  1. **Scope Restriction**: In accordance with product policy, **no explicit image uploads** or live location sharing are supported in the MVP.
  2. Text pre-filtering automatically blocks phone number patterns, national ID numbers, and campus student ID patterns.
  3. Campus affiliation is optional and strictly self-declared. No GPS geotags are stored or broadcast.

### 2.5 Harassment & Unsolicited Direct Messaging
- **Risk**: Stalkers or bad actors spamming private direct messages to anonymous personas.
- **Mitigation**:
  1. **Strict Consent Gate**: Direct messaging requires a prior mutual connection request. Persona B must actively accept Persona A's request before a conversation channel can be created.
  2. **Universal Blocking**: If Persona B blocks Persona A, all incoming requests and messaging routes are immediately severed at the database level.
  3. **Reporting Pipeline**: In-conversation reporting with message context for moderation review.

### 2.6 Token & Secret Hygiene
- **Risk**: Supabase service-role keys or database credentials exposed in frontend builds.
- **Mitigation**:
  1. Only the Supabase anonymous public key (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) is ever provided to the frontend.
  2. The backend validates Supabase JWTs by verifying the JWT signature against the `SUPABASE_JWT_SECRET` or Supabase JWKS endpoint.
  3. Service-role secrets are strictly confined to backend internal processes and never sent to clients.

### 2.7 Realistic Anonymity Disclaimers
- In compliance with product policy rule 13, AFTR never promises "absolute untraceability" or "bulletproof anonymity". Legal compliance, court-ordered subpoenas, and severe harm intervention protocols (CSAM, imminent violence) remain technically auditable via hashed infrastructure logs while preserving standard end-user privacy.
