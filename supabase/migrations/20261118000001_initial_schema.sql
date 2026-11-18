-- ========================================================================
-- AFTR Database Schema: Core Modular Monolith Tables
-- PostgreSQL 16+ compatible
-- ========================================================================

-- Enable pgcrypto for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================================================
-- 1. IDENTITY DOMAIN (Protected, Never Exposed Publicly)
-- ========================================================================

CREATE TYPE account_status_enum AS ENUM ('ACTIVE', 'SUSPENDED', 'BANNED');

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supabase_user_id UUID UNIQUE NOT NULL,
    email_hash VARCHAR(64) UNIQUE NOT NULL, -- Salted SHA-256 for lookup without storing plaintext email
    is_age_verified BOOLEAN NOT NULL DEFAULT FALSE,
    birth_year INT,
    invite_quota INT NOT NULL DEFAULT 3,
    status account_status_enum NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_accounts_supabase_user_id ON accounts(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_email_hash ON accounts(email_hash);

-- ========================================================================
-- 2. INVITATIONS DOMAIN
-- ========================================================================

CREATE TYPE invitation_status_enum AS ENUM ('PENDING', 'USED', 'EXPIRED', 'REVOKED');

CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inviter_account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) UNIQUE NOT NULL, -- Stored SHA-256 of the invitation token
    recipient_hash VARCHAR(64) NOT NULL,    -- HMAC-SHA256 of recipient identifier with secret salt
    status invitation_status_enum NOT NULL DEFAULT 'PENDING',
    expires_at TIMESTAMPTZ NOT NULL,        -- strictly now() + 72 hours
    used_by_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_invitations_token_hash ON invitations(token_hash);
CREATE INDEX IF NOT EXISTS idx_invitations_recipient_hash ON invitations(recipient_hash);
CREATE INDEX IF NOT EXISTS idx_invitations_expires_at ON invitations(expires_at);

-- ========================================================================
-- 3. SOCIAL PERSONA DOMAIN (Public/Pseudonymous Identity)
-- ========================================================================

CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    display_name VARCHAR(50) NOT NULL,
    avatar_seed VARCHAR(100) NOT NULL,
    bio TEXT,
    declared_campus VARCHAR(100), -- Strictly optional and self-declared
    adult_interests JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_personas_account_id ON personas(account_id);
CREATE INDEX IF NOT EXISTS idx_personas_declared_campus ON personas(declared_campus);

-- ========================================================================
-- 4. CONNECTIONS & CONSENT-GATED MESSAGING
-- ========================================================================

CREATE TYPE connection_status_enum AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'BLOCKED', 'WITHDRAWN');

CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    recipient_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    status connection_status_enum NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_connection_pair UNIQUE (sender_persona_id, recipient_persona_id),
    CONSTRAINT chk_no_self_connection CHECK (sender_persona_id <> recipient_persona_id)
);

CREATE INDEX IF NOT EXISTS idx_connections_status ON connections(status);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID UNIQUE NOT NULL REFERENCES connections(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- ========================================================================
-- 5. CONFESSIONS & DISCUSSION FEEDS
-- ========================================================================

CREATE TABLE IF NOT EXISTS confessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    tag VARCHAR(50) NOT NULL DEFAULT 'general',
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    view_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_confessions_created_at ON confessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_confessions_tag ON confessions(tag);

CREATE TABLE IF NOT EXISTS confession_reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confession_id UUID NOT NULL REFERENCES confessions(id) ON DELETE CASCADE,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    reaction_type VARCHAR(20) NOT NULL DEFAULT 'upvote',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_confession_reaction UNIQUE (confession_id, persona_id, reaction_type)
);

-- ========================================================================
-- 6. MODERATION & SAFETY
-- ========================================================================

CREATE TYPE report_status_enum AS ENUM ('PENDING', 'REVIEWED', 'ACTIONED', 'DISMISSED');

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    target_type VARCHAR(30) NOT NULL, -- 'confession', 'comment', 'persona', 'message'
    target_id UUID NOT NULL,
    reason TEXT NOT NULL,
    status report_status_enum NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_target ON reports(target_type, target_id);

CREATE TABLE IF NOT EXISTS user_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    blocked_persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT unique_persona_block UNIQUE (blocker_persona_id, blocked_persona_id),
    CONSTRAINT chk_no_self_block CHECK (blocker_persona_id <> blocked_persona_id)
);
