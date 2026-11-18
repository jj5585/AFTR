export type UUID = string;

// Health & System
export type ServiceStatus = "healthy" | "degraded" | "disconnected" | "connected";

export interface HealthCheckResponse {
  status: "healthy" | "degraded";
  app: string;
  environment: string;
  timestamp_utc: string;
  services: {
    api: string;
    database: string;
    redis: string;
  };
}

// Account & Identity Domain (Protected)
export type AccountStatus = "ACTIVE" | "SUSPENDED" | "BANNED";

export interface AccountIdentity {
  id: UUID;
  is_age_verified: boolean;
  invite_quota: number;
  status: AccountStatus;
  created_at: string;
}

// Anonymous Persona Domain (Public/Social)
export interface AnonymousPersona {
  id: UUID;
  display_name: string;
  avatar_seed: string;
  bio?: string | null;
  declared_campus?: string | null;
  adult_interests: string[];
  created_at: string;
}

// Invitations
export type InvitationStatus = "PENDING" | "USED" | "EXPIRED" | "REVOKED";

export interface InvitationMetadata {
  id: UUID;
  token_preview: string;
  expires_at: string;
  status: InvitationStatus;
  created_at: string;
}

// Connections & Messaging
export type ConnectionStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "BLOCKED" | "WITHDRAWN";

export interface ConnectionInfo {
  id: UUID;
  sender_persona_id: UUID;
  recipient_persona_id: UUID;
  status: ConnectionStatus;
  created_at: string;
}

export interface PrivateMessage {
  id: UUID;
  conversation_id: UUID;
  sender_persona_id: UUID;
  content: string;
  created_at: string;
}

// Confessions & Stories
export interface ConfessionSummary {
  id: UUID;
  persona_id: UUID;
  content: string;
  tag: string;
  is_sensitive: boolean;
  upvotes_count: number;
  comments_count: number;
  created_at: string;
}
