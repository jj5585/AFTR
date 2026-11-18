export interface FixturePersona {
  id: string;
  display_name: string;
  avatar_seed: string;
  bio?: string;
  declared_campus?: string;
  interests?: string[];
  is_active: boolean;
}

export interface FixturePost {
  id: string;
  persona: FixturePersona;
  content: string;
  post_type: "CONFESSION" | "DISCUSSION" | "GENERAL";
  tag: string;
  is_sensitive: boolean;
  upvotes_count: number;
  reactions?: {
    upvotes: number;
    flames: number;
    hearts: number;
    insightful: number;
  };
  comments_count: number;
  created_at: string;
  user_has_reacted?: boolean;
}

export interface FixtureComment {
  id: string;
  post_id: string;
  persona: FixturePersona;
  content: string;
  created_at: string;
  is_op?: boolean;
  replies?: FixtureComment[];
}

export interface FixtureConnection {
  id: string;
  persona: FixturePersona;
  compatibility_score: number;
  mutual_interests: string[];
  status: "NONE" | "PENDING" | "ACCEPTED" | "REJECTED";
  created_at: string;
}

export interface FixtureChatRequest {
  id: string;
  sender_persona: FixturePersona;
  preview_note?: string;
  mutual_interests: string[];
  compatibility_score: number;
  created_at: string;
}

export interface FixtureMessage {
  id: string;
  conversation_id: string;
  sender_persona_id: string;
  content: string;
  created_at: string;
  is_own?: boolean;
}

export interface FixtureConversation {
  id: string;
  other_persona: FixturePersona;
  last_message: string;
  last_message_at: string;
  unread_count: number;
  is_active: boolean;
}

export interface FixtureStory {
  id: string;
  persona: FixturePersona;
  content: string;
  gradient_theme: string;
  expires_in_hours: number;
  created_at: string;
}

export interface FixtureEvent {
  id: string;
  title: string;
  description: string;
  campus_name?: string;
  location_name: string;
  event_time: string;
  attendees_count: number;
  max_attendees?: number;
  is_attending?: boolean;
}

export interface FixtureInvitation {
  id: string;
  token: string;
  bound_email_masked: string;
  status: "ACTIVE" | "REDEEMED" | "EXPIRED" | "REVOKED";
  created_at: string;
  expires_at: string;
  redeemed_by_persona?: string;
}

export interface FixtureModerationItem {
  id: string;
  target_type: "POST" | "COMMENT" | "PERSONA";
  target_id: string;
  reporter_persona: string;
  reason: string;
  details: string;
  content_preview: string;
  status: "PENDING" | "RESOLVED" | "DISMISSED";
  created_at: string;
}

export interface FixtureAuditLog {
  id: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: string;
  timestamp_utc: string;
}

export const CURRENT_USER_PERSONA: FixturePersona = {
  id: "p-current-user",
  display_name: "ShadowFox",
  avatar_seed: "fox-midnight",
  bio: "Late-night architecture & distributed systems student. Seeking thoughtful conversation without performative noise.",
  declared_campus: "Bay Area University",
  interests: ["Night Owl", "Architecture", "Philosophy", "Deep House", "Analog Photography"],
  is_active: true,
};

export const FIXTURE_PERSONAS: FixturePersona[] = [
  CURRENT_USER_PERSONA,
  {
    id: "p-neon-ghost",
    display_name: "NeonGhost",
    avatar_seed: "ghost-emerald",
    bio: "Philosophy, lo-fi beats, and rooftop talks.",
    declared_campus: "West Coast College",
    interests: ["Philosophy", "Lo-Fi", "Stargazing", "Indie Cinema"],
    is_active: true,
  },
  {
    id: "p-midnight-echo",
    display_name: "MidnightEcho",
    avatar_seed: "echo-violet",
    bio: "Exploring honest connections without social baggage.",
    declared_campus: "Bay Area University",
    interests: ["Night Owl", "Writing", "Psychology", "Ambient Music"],
    is_active: true,
  },
  {
    id: "p-cyber-raven",
    display_name: "CyberRaven",
    avatar_seed: "raven-noir",
    bio: "Deep conversations after hours only.",
    declared_campus: "Metro Campus",
    interests: ["Cybersecurity", "Synthesizers", "Sci-Fi", "Chess"],
    is_active: true,
  },
  {
    id: "p-velvet-mist",
    display_name: "VelvetMist",
    avatar_seed: "mist-rose",
    bio: "Art history scholar. Unfiltered thoughts on love, isolation, and ambition.",
    declared_campus: "Pacific Arts Institute",
    interests: ["Art History", "Poetry", "Psychology", "Vinyl Records"],
    is_active: false,
  },
];

export const FIXTURE_POSTS: FixturePost[] = [
  {
    id: "post-1",
    persona: FIXTURE_PERSONAS[0],
    content: "I've spent three terms in a weekly research group with someone I've fallen completely in love with. Every time we review code together, my pulse jumps. Neither of us has ever crossed the boundary, but late night in the lab it feels magnetic.",
    post_type: "CONFESSION",
    tag: "secret-crushes",
    is_sensitive: false,
    upvotes_count: 54,
    reactions: { upvotes: 54, flames: 32, hearts: 41, insightful: 12 },
    comments_count: 12,
    created_at: "2026-11-18T00:30:00Z",
    user_has_reacted: true,
  },
  {
    id: "post-2",
    persona: FIXTURE_PERSONAS[1],
    content: "Walking through campus around 2:45 AM during the foggy midterms week was the first time in six months my brain went quiet. No pressure, no resume expectations. Just cool air and streetlights.",
    post_type: "CONFESSION",
    tag: "mental-health",
    is_sensitive: false,
    upvotes_count: 89,
    reactions: { upvotes: 89, flames: 15, hearts: 67, insightful: 28 },
    comments_count: 19,
    created_at: "2026-11-17T22:15:00Z",
  },
  {
    id: "post-3",
    persona: FIXTURE_PERSONAS[2],
    content: "Anyone else feel like campus social circles are hyper-performative? Everyone pretends to have their life together on Instagram and LinkedIn. Anonymity is the only place where honest vulnerability survives.",
    post_type: "DISCUSSION",
    tag: "campus-life",
    is_sensitive: false,
    upvotes_count: 132,
    reactions: { upvotes: 132, flames: 48, hearts: 95, insightful: 63 },
    comments_count: 34,
    created_at: "2026-11-17T18:40:00Z",
  },
  {
    id: "post-4",
    persona: FIXTURE_PERSONAS[3],
    content: "Unfiltered adult reality: It is deeply exhausting how hard it is to discuss intimacy, modern dating confusion, and boundaries openly without being judged or stigmatized. AFTR having strict adult assurance makes this space feel like an oasis.",
    post_type: "DISCUSSION",
    tag: "unfiltered",
    is_sensitive: true,
    upvotes_count: 76,
    reactions: { upvotes: 76, flames: 51, hearts: 49, insightful: 22 },
    comments_count: 8,
    created_at: "2026-11-17T14:10:00Z",
  },
];

export const FIXTURE_COMMENTS: FixtureComment[] = [
  {
    id: "c-1",
    post_id: "post-1",
    persona: FIXTURE_PERSONAS[1],
    content: "Tell them before the semester ends. Regret is infinitely heavier than a momentary awkward pause.",
    created_at: "2026-11-18T01:10:00Z",
    is_op: false,
    replies: [
      {
        id: "c-1-1",
        post_id: "post-1",
        persona: FIXTURE_PERSONAS[0],
        content: "I'm genuinely terrified it will rupture our project dynamics if they don't reciprocate.",
        created_at: "2026-11-18T01:25:00Z",
        is_op: true,
      },
    ],
  },
  {
    id: "c-2",
    post_id: "post-1",
    persona: FIXTURE_PERSONAS[2],
    content: "If the energy is magnetic, they feel it too. Subtly suggest grabbing a midnight coffee outside the lab first.",
    created_at: "2026-11-18T02:00:00Z",
    is_op: false,
  },
];

export const FIXTURE_CONNECTIONS: FixtureConnection[] = [
  {
    id: "conn-1",
    persona: FIXTURE_PERSONAS[1],
    compatibility_score: 94,
    mutual_interests: ["Night Owl", "Philosophy", "Deep Conversations"],
    status: "NONE",
    created_at: "2026-11-17T12:00:00Z",
  },
  {
    id: "conn-2",
    persona: FIXTURE_PERSONAS[2],
    compatibility_score: 88,
    mutual_interests: ["Psychology", "Writing", "Lo-Fi"],
    status: "NONE",
    created_at: "2026-11-17T11:00:00Z",
  },
  {
    id: "conn-3",
    persona: FIXTURE_PERSONAS[3],
    compatibility_score: 81,
    mutual_interests: ["Synthesizers", "Late Night", "Sci-Fi"],
    status: "PENDING",
    created_at: "2026-11-16T19:00:00Z",
  },
  {
    id: "conn-4",
    persona: FIXTURE_PERSONAS[4],
    compatibility_score: 76,
    mutual_interests: ["Art History", "Poetry"],
    status: "ACCEPTED",
    created_at: "2026-11-15T15:00:00Z",
  },
];

export const FIXTURE_CHAT_REQUESTS: FixtureChatRequest[] = [
  {
    id: "req-1",
    sender_persona: FIXTURE_PERSONAS[2],
    preview_note: "Saw your confession on late night lab sessions. I study in the adjacent hall and would love to chat anonymously.",
    mutual_interests: ["Night Owl", "Philosophy"],
    compatibility_score: 88,
    created_at: "2026-11-18T03:00:00Z",
  },
];

export const FIXTURE_CONVERSATIONS: FixtureConversation[] = [
  {
    id: "conv-1",
    other_persona: FIXTURE_PERSONAS[4],
    last_message: "The way you interpreted that architecture concept made so much sense.",
    last_message_at: "2026-11-18T04:15:00Z",
    unread_count: 1,
    is_active: true,
  },
  {
    id: "conv-2",
    other_persona: FIXTURE_PERSONAS[1],
    last_message: "Let's see if the rooftop observatory event happens this weekend.",
    last_message_at: "2026-11-17T20:30:00Z",
    unread_count: 0,
    is_active: true,
  },
];

export const FIXTURE_MESSAGES: FixtureMessage[] = [
  {
    id: "m-1",
    conversation_id: "conv-1",
    sender_persona_id: "p-velvet-mist",
    content: "Hey, thanks for accepting the connection request! I loved your thoughts on anonymity creating genuine vulnerability.",
    created_at: "2026-11-18T03:45:00Z",
    is_own: false,
  },
  {
    id: "m-2",
    conversation_id: "conv-1",
    sender_persona_id: "p-current-user",
    content: "Thank you! It feels rare to talk without people scoping out your LinkedIn or past friend group dynamics.",
    created_at: "2026-11-18T04:00:00Z",
    is_own: true,
  },
  {
    id: "m-3",
    conversation_id: "conv-1",
    sender_persona_id: "p-velvet-mist",
    content: "The way you interpreted that architecture concept made so much sense. Are you usually up this late?",
    created_at: "2026-11-18T04:15:00Z",
    is_own: false,
  },
];

export const FIXTURE_STORIES: FixtureStory[] = [
  {
    id: "story-1",
    persona: FIXTURE_PERSONAS[1],
    content: "Listening to rainfall against the library windows while drinking bitter espresso. Nothing else exists right now.",
    gradient_theme: "from-purple-900/40 via-indigo-950/50 to-background",
    expires_in_hours: 18,
    created_at: "2026-11-18T02:00:00Z",
  },
  {
    id: "story-2",
    persona: FIXTURE_PERSONAS[2],
    content: "Accidentally made eye contact across the lecture hall for a solid 5 seconds. My heart is still doing flips.",
    gradient_theme: "from-pink-950/40 via-purple-950/50 to-background",
    expires_in_hours: 11,
    created_at: "2026-11-17T21:00:00Z",
  },
  {
    id: "story-3",
    persona: FIXTURE_PERSONAS[3],
    content: "Late-night synth session. If anyone wants to collaborate on atmospheric dark ambient soundscapes, hit connect.",
    gradient_theme: "from-blue-950/40 via-slate-950/50 to-background",
    expires_in_hours: 6,
    created_at: "2026-11-17T16:00:00Z",
  },
];

export const FIXTURE_EVENTS: FixtureEvent[] = [
  {
    id: "event-1",
    title: "Midnight Rooftop Astronomy & Ambient Lo-Fi",
    description: "Bring a warm layer and a mug. Open telescope viewing of the meteor shower and low-key ambient conversation. Strictly pseudonymous.",
    campus_name: "Bay Area University",
    location_name: "Physics Observatory Open Deck",
    event_time: "2026-11-20T05:00:00Z",
    attendees_count: 18,
    max_attendees: 30,
    is_attending: true,
  },
  {
    id: "event-2",
    title: "Anonymous Coffee & Philosophy Circle",
    description: "No introductions by real name, major, or company. Just discuss life, ethics, and art over dark roast.",
    campus_name: "West Coast College",
    location_name: "North Courtyard Benches",
    event_time: "2026-11-21T02:00:00Z",
    attendees_count: 9,
    max_attendees: 15,
    is_attending: false,
  },
  {
    id: "event-3",
    title: "After-Hours Indie Game Jam & Chill",
    description: "Show off anonymous creative prototypes and experimental interactive art. No resumes, no pitch decks.",
    campus_name: "Metro Campus",
    location_name: "Digital Media Common Room",
    event_time: "2026-11-22T04:00:00Z",
    attendees_count: 14,
    max_attendees: 25,
    is_attending: false,
  },
];

export const FIXTURE_INVITATIONS: FixtureInvitation[] = [
  {
    id: "inv-1",
    token: "aftr-88a2-94f1",
    bound_email_masked: "al***@example.com",
    status: "ACTIVE",
    created_at: "2026-11-17T18:00:00Z",
    expires_at: "2026-11-20T18:00:00Z",
  },
  {
    id: "inv-2",
    token: "aftr-31c7-e62a",
    bound_email_masked: "cl***@example.com",
    status: "REDEEMED",
    created_at: "2026-11-16T10:00:00Z",
    expires_at: "2026-11-19T10:00:00Z",
    redeemed_by_persona: "NeonGhost",
  },
  {
    id: "inv-3",
    token: "aftr-79d4-11b9",
    bound_email_masked: "jo***@example.com",
    status: "ACTIVE",
    created_at: "2026-11-18T05:30:00Z",
    expires_at: "2026-11-21T05:30:00Z",
  },
];

export const FIXTURE_MODERATION_ITEMS: FixtureModerationItem[] = [
  {
    id: "mod-1",
    target_type: "POST",
    target_id: "post-99",
    reporter_persona: "VelvetMist",
    reason: "Suspected Personal Contact Information",
    details: "User dropped what looks like a dorm room number and Instagram handle.",
    content_preview: "Come hang out at tower B 402 or follow @...",
    status: "PENDING",
    created_at: "2026-11-18T06:12:00Z",
  },
  {
    id: "mod-2",
    target_type: "COMMENT",
    target_id: "c-44",
    reporter_persona: "ShadowFox",
    reason: "Hostile Harassment",
    details: "Aggressive personal targeting and insults in reply thread.",
    content_preview: "You're pathetic for thinking that way, get off this platform...",
    status: "PENDING",
    created_at: "2026-11-18T05:40:00Z",
  },
];

export const FIXTURE_AUDIT_LOGS: FixtureAuditLog[] = [
  {
    id: "log-1",
    actor: "SYSTEM",
    action: "INVITATION_REDEEMED",
    resource_type: "invitation",
    resource_id: "inv-2",
    details: "Single-use token claimed with valid cryptographic Age Assurance proof.",
    timestamp_utc: "2026-11-16T10:35:12Z",
  },
  {
    id: "log-2",
    actor: "MOD_ADMIN",
    action: "CONTENT_HIDDEN",
    resource_type: "post",
    resource_id: "post-82",
    details: "Post automatically flagged by PII shield for email address pattern.",
    timestamp_utc: "2026-11-17T14:22:01Z",
  },
  {
    id: "log-3",
    actor: "SYSTEM",
    action: "AGE_ASSURANCE_TOKEN_ISSUED",
    resource_type: "account",
    resource_id: "acc-user-99",
    details: "User verified 18+ via legitimate AgeAssuranceEngine proof token.",
    timestamp_utc: "2026-11-18T01:14:09Z",
  },
];

export const CATEGORIES = [
  { id: "all", label: "All Posts" },
  { id: "confessions", label: "Confessions" },
  { id: "dating", label: "Dating" },
  { id: "questions", label: "Questions" },
  { id: "experiences", label: "Experiences" },
  { id: "campus-life", label: "Campus Life" },
  { id: "adult-interests", label: "Adult Interests" },
];
