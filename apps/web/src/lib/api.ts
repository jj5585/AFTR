import {
  FixturePost,
  FixtureComment,
  FIXTURE_POSTS,
  FIXTURE_COMMENTS,
  CURRENT_USER_PERSONA,
} from "./fixtures";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeader(): Record<string, string> {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("aftr_access_token") || localStorage.getItem("supabase_token");
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
}

export interface FetchFeedParams {
  category?: string;
  campus?: string;
  sort?: "latest" | "trending";
  cursor?: string;
  limit?: number;
}

export interface PaginatedResult<T> {
  items: T[];
  next_cursor?: string | null;
  has_more: boolean;
}

export const socialApi = {
  async fetchFeed(params: FetchFeedParams = {}): Promise<PaginatedResult<FixturePost>> {
    try {
      const q = new URLSearchParams();
      if (params.category && params.category !== "all") q.append("category", params.category);
      if (params.campus && params.campus !== "all") q.append("campus", params.campus);
      if (params.sort) q.append("sort", params.sort);
      if (params.cursor) q.append("cursor", params.cursor);
      if (params.limit) q.append("limit", params.limit.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/posts?${q.toString()}`, {
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeader(),
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      return {
        items: data.items,
        next_cursor: data.next_cursor,
        has_more: data.has_more,
      };
    } catch {
      // Fallback to local development fixtures
      let filtered = [...FIXTURE_POSTS];
      if (params.category && params.category !== "all") {
        filtered = filtered.filter((p) => p.tag === params.category);
      }
      return {
        items: filtered,
        next_cursor: null,
        has_more: false,
      };
    }
  },

  async fetchPost(id: string): Promise<FixturePost> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/posts/${id}`, {
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      const found = FIXTURE_POSTS.find((p) => p.id === id);
      if (found) return found;
      return FIXTURE_POSTS[0];
    }
  },

  async createPost(data: {
    content: string;
    tag?: string;
    post_type?: string;
    is_sensitive?: boolean;
    allow_comments?: boolean;
    campus_name?: string;
  }): Promise<FixturePost> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/posts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeader(),
        },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create post: HTTP ${res.status}`);
      }

      return await res.json();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error creating post";
      // If network fails in pure UI dev, generate client fixture
      if (message.includes("HTTP") || message.includes("Privacy Shield")) {
        throw err;
      }
      return {
        id: `post-${Date.now()}`,
        persona: CURRENT_USER_PERSONA,
        content: data.content,
        post_type: (data.post_type as "CONFESSION" | "DISCUSSION" | "GENERAL") || "CONFESSION",
        tag: data.tag || "confessions",
        is_sensitive: !!data.is_sensitive,
        upvotes_count: 0,
        comments_count: 0,
        created_at: new Date().toISOString(),
        user_has_reacted: false,
      };
    }
  },

  async deletePost(id: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/posts/${id}`, {
      method: "DELETE",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok && res.status !== 404) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
  },

  async fetchComments(postId: string): Promise<FixtureComment[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/comments`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.items;
    } catch {
      return FIXTURE_COMMENTS.filter((c) => c.post_id === postId);
    }
  },

  async addComment(postId: string, content: string, parentId?: string): Promise<FixtureComment> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/comments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeader(),
        },
        body: JSON.stringify({ content, parent_id: parentId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      return await res.json();
    } catch {
      return {
        id: `c-${Date.now()}`,
        post_id: postId,
        persona: CURRENT_USER_PERSONA,
        content,
        created_at: new Date().toISOString(),
        is_op: false,
      };
    }
  },

  async reactToPost(postId: string, reactionType: string): Promise<unknown> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/reactions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeader(),
        },
        body: JSON.stringify({ reaction_type: reactionType }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { action: "TOGGLED", reaction_type: reactionType };
    }
  },

  async blockPersona(personaId: string, reason?: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/v1/blocks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ blocked_persona_id: personaId, reason }),
    });
  },

  async reportContent(targetType: string, targetId: string, reason: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/v1/reports`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ target_type: targetType, target_id: targetId, reason }),
    });
  },
};

export interface DiscoveryCardItem {
  id: string;
  persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
    is_active?: boolean;
    bio?: string;
  };
  compatibility_score: number;
  mutual_interests: string[];
  relationship_intention?: string | null;
  connection_status: "NONE" | "PENDING" | "PENDING_SENT" | "PENDING_RECEIVED" | "ACCEPTED" | "REJECTED" | "WITHDRAWN";
  connection_request_id?: string | null;
}

export interface DiscoveryPreferencesData {
  is_discoverable: boolean;
  relationship_intention?: string | null;
  min_age_preference: number;
  max_age_preference: number;
  dating_preferences?: Record<string, unknown> | null;
  interests: Array<{ id: string; name: string; slug: string; is_adult: boolean }>;
}

export interface ConnectionRequestItem {
  id: string;
  sender_persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  recipient_persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  note?: string | null;
  status: string;
  created_at: string;
}

export interface MatchItem {
  id: string;
  matched_persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  compatibility_score: number;
  conversation_id?: string | null;
  created_at: string;
}

export const discoveryApi = {
  async fetchInterests(): Promise<Array<{ id: string; name: string; slug: string; is_adult: boolean }>> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/discovery/interests`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.interests;
    } catch {
      return [
        { id: "1", name: "Night Owl", slug: "night-owl", is_adult: true },
        { id: "2", name: "Late Talks", slug: "late-talks", is_adult: true },
        { id: "3", name: "Study Partner", slug: "study-partner", is_adult: false },
        { id: "4", name: "Deep Convos", slug: "deep-convos", is_adult: true },
        { id: "5", name: "Casual Vibe", slug: "casual-vibe", is_adult: true },
        { id: "6", name: "Music & Concerts", slug: "music-concerts", is_adult: false },
      ];
    }
  },

  async fetchPreferences(): Promise<DiscoveryPreferencesData | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/discovery/preferences`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return null;
    }
  },

  async updatePreferences(data: {
    is_discoverable?: boolean;
    relationship_intention?: string;
    min_age_preference?: number;
    max_age_preference?: number;
    dating_preferences?: Record<string, unknown>;
    interest_ids?: string[];
  }): Promise<DiscoveryPreferencesData | null> {
    const res = await fetch(`${API_BASE_URL}/api/v1/discovery/preferences`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchFeed(params: {
    cursor?: string;
    limit?: number;
    campus?: string;
    intention?: string;
  } = {}): Promise<PaginatedResult<DiscoveryCardItem>> {
    try {
      const q = new URLSearchParams();
      if (params.cursor) q.append("cursor", params.cursor);
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.campus && params.campus !== "All") q.append("campus", params.campus);
      if (params.intention && params.intention !== "All") q.append("intention", params.intention);

      const res = await fetch(`${API_BASE_URL}/api/v1/discovery/feed?${q.toString()}`, {
        headers: {
          ...getAuthHeader(),
        },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      const mapped: DiscoveryCardItem[] = data.items.map((item: {
        persona: { id: string; display_name: string; avatar_seed: string; declared_campus?: string | null };
        compatibility_score: number;
        mutual_interests: string[];
        relationship_intention?: string | null;
        connection_status: string;
        connection_request_id?: string | null;
      }) => ({
        id: item.persona.id,
        persona: item.persona,
        compatibility_score: item.compatibility_score,
        mutual_interests: item.mutual_interests,
        relationship_intention: item.relationship_intention,
        connection_status: item.connection_status as DiscoveryCardItem["connection_status"],
        connection_request_id: item.connection_request_id,
      }));

      return {
        items: mapped,
        next_cursor: data.next_cursor,
        has_more: data.has_more,
      };
    } catch {
      // Return empty or fallback
      return {
        items: [],
        next_cursor: null,
        has_more: false,
      };
    }
  },

  async sendConnectionRequest(recipientPersonaId: string, note?: string): Promise<ConnectionRequestItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/connections/request`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({
        recipient_persona_id: recipientPersonaId,
        note,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchConnectionRequests(): Promise<{
    incoming: ConnectionRequestItem[];
    outgoing: ConnectionRequestItem[];
  }> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/connections/requests`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { incoming: [], outgoing: [] };
    }
  },

  async acceptConnectionRequest(requestId: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/connections/requests/${requestId}/accept`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async rejectConnectionRequest(requestId: string): Promise<ConnectionRequestItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/connections/requests/${requestId}/reject`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async withdrawConnectionRequest(requestId: string): Promise<ConnectionRequestItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/connections/requests/${requestId}/withdraw`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchMatches(): Promise<MatchItem[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/connections/matches`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.matches;
    } catch {
      return [];
    }
  },
};

export interface ChatMessageItem {
  id: string;
  conversation_id: string;
  sender_persona_id: string;
  sender_pseudonym: string;
  content: string;
  is_mine: boolean;
  is_deleted: boolean;
  created_at: string;
}

export interface ConversationSummaryItem {
  id: string;
  other_participant: {
    persona_id: string;
    conversation_pseudonym: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
    is_online: boolean;
  };
  my_conversation_pseudonym: string;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  unread_count: number;
  is_active: boolean;
  is_blocked: boolean;
  created_at: string;
}

export const messagingApi = {
  async fetchConversations(): Promise<ConversationSummaryItem[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  async fetchUnreadCount(): Promise<{ total_unread_messages: number; unread_conversations_count: number }> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations/unread-count`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { total_unread_messages: 0, unread_conversations_count: 0 };
    }
  },

  async fetchConversationDetail(conversationId: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}`, {
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchMessages(conversationId: string, cursor?: string): Promise<{ items: ChatMessageItem[]; next_cursor?: string | null; has_more: boolean }> {
    try {
      const q = new URLSearchParams();
      if (cursor) q.append("cursor", cursor);
      const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}/messages?${q.toString()}`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], has_more: false };
    }
  },

  async sendMessage(conversationId: string, content: string): Promise<ChatMessageItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async deleteMessage(messageId: string): Promise<ChatMessageItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/messages/${messageId}`, {
      method: "DELETE",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async blockConversation(conversationId: string, reason?: string): Promise<unknown> {
    const q = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}/block${q}`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async markConversationRead(conversationId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}/read`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    }).catch(() => {});
  },

  getWebSocketUrl(conversationId: string): string {
    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    let token = "";
    if (typeof window !== "undefined") {
      token = localStorage.getItem("aftr_access_token") || localStorage.getItem("supabase_token") || "";
    }
    return `${wsBase}/api/v1/ws/conversations/${conversationId}?token=${encodeURIComponent(token)}`;
  },
};

export interface LiveStoryItem {
  id: string;
  persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  content: string;
  category: string;
  allow_comments: boolean;
  visibility: string;
  campus_name?: string | null;
  reactions_count: number;
  user_has_reacted: boolean;
  comments_count: number;
  is_own: boolean;
  expires_at: string;
  created_at: string;
}

export interface LiveEventItem {
  id: string;
  creator_persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  title: string;
  description: string;
  location_name: string;
  event_time: string;
  campus_name?: string | null;
  max_attendees?: number | null;
  attendees_count: number;
  interested_count: number;
  user_rsvp_status?: string | null;
  is_cancelled: boolean;
  is_organizer: boolean;
  created_at: string;
}

export const storiesApi = {
  async fetchStories(params: { category?: string; campus?: string; cursor?: string; limit?: number } = {}): Promise<PaginatedResult<LiveStoryItem>> {
    try {
      const q = new URLSearchParams();
      if (params.category && params.category !== "all") q.append("category", params.category);
      if (params.campus && params.campus !== "all") q.append("campus", params.campus);
      if (params.cursor) q.append("cursor", params.cursor);
      if (params.limit) q.append("limit", params.limit.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/stories?${q.toString()}`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], has_more: false };
    }
  },

  async createStory(data: {
    content: string;
    category?: string;
    allow_comments?: boolean;
    visibility?: string;
    campus_name?: string;
  }): Promise<LiveStoryItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/stories`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async reactToStory(storyId: string, reactionType = "UPVOTE"): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}/reactions?reaction_type=${reactionType}`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async fetchStoryComments(storyId: string): Promise<unknown[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}/comments`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  async addStoryComment(storyId: string, content: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}/comments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async deleteStory(storyId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}`, {
      method: "DELETE",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
  },
};

export const eventsApi = {
  async fetchEvents(params: { campus?: string; cursor?: string; limit?: number } = {}): Promise<PaginatedResult<LiveEventItem>> {
    try {
      const q = new URLSearchParams();
      if (params.campus && params.campus !== "all") q.append("campus", params.campus);
      if (params.cursor) q.append("cursor", params.cursor);
      if (params.limit) q.append("limit", params.limit.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/events?${q.toString()}`, {
        headers: {
          ...getAuthHeader(),
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], has_more: false };
    }
  },

  async createEvent(data: {
    title: string;
    description: string;
    location_name: string;
    event_time: string;
    max_attendees?: number;
    campus_name?: string;
  }): Promise<LiveEventItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async rsvpEvent(eventId: string, status = "GOING"): Promise<LiveEventItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/rsvp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async withdrawRsvp(eventId: string): Promise<LiveEventItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/rsvp`, {
      method: "DELETE",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async cancelEvent(eventId: string): Promise<LiveEventItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/events/${eventId}/cancel`, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },
};

export interface AdminOverviewData {
  pending_reports_count: number;
  pending_review_queue_count: number;
  pending_appeals_count: number;
  total_active_accounts: number;
  suspended_personas_count: number;
  banned_accounts_count: number;
  total_moderation_actions: number;
  recent_actions: Array<{
    id: string;
    action_type: string;
    target_type: string;
    reason: string;
    created_at: string;
  }>;
}

export interface ReportItem {
  id: string;
  target_type: string;
  target_id: string;
  reason: string;
  status: string;
  reporter_persona_name?: string;
  reporter_persona_id: string;
  resolved_by?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
  content_excerpt?: string | null;
}

export interface ModerationQueueItemData {
  target_type: string;
  target_id: string;
  content: string;
  category?: string | null;
  campus_name?: string | null;
  moderation_status: string;
  author_persona_id: string;
  author_persona_name: string;
  author_avatar_seed: string;
  flagged_reasons: string[];
  reports_count: number;
  created_at: string;
}

export interface AppealItemData {
  id: string;
  moderation_action_id: string;
  appellant_persona_id: string;
  reason: string;
  status: string;
  reviewed_at?: string | null;
  resolution_notes?: string | null;
  created_at: string;
  action_details?: {
    action_type: string;
    reason: string;
    target_type: string;
  } | null;
}

export interface AdminInvitationItemData {
  id: string;
  inviter_persona_name?: string | null;
  recipient_email_masked: string;
  status: string;
  created_at: string;
  expires_at: string;
  redeemed_at?: string | null;
}

export interface AdminAccountItemData {
  id: string;
  status: string;
  role: string;
  personas_count: number;
  persona_display_names: string[];
  invite_quota: number;
  is_age_verified: boolean;
  strike_count: number;
  created_at: string;
}

export interface AuditLogItemData {
  id: string;
  actor_type: string;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  ip_hash?: string | null;
  details?: string | null;
  created_at: string;
}

export interface BlockedPersonaItemData {
  persona_id: string;
  display_name: string;
  avatar_seed: string;
  reason?: string | null;
  blocked_at: string;
}

export interface CommunityStandardRuleData {
  category: string;
  title: string;
  description: string;
  enforcement: string;
}

export const adminApi = {
  async fetchOverview(): Promise<AdminOverviewData | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/admin/overview`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return null;
    }
  },

  async fetchReports(params: { status?: string; target_type?: string; limit?: number; offset?: number } = {}): Promise<{
    items: ReportItem[];
    total: number;
    pending_count: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.status) q.append("status", params.status);
      if (params.target_type) q.append("target_type", params.target_type);
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/reports?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0, pending_count: 0 };
    }
  },

  async resolveReport(reportId: string, action: string, notes?: string): Promise<ReportItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/reports/${reportId}/resolve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ action, notes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchModerationQueue(params: { limit?: number; offset?: number } = {}): Promise<{
    items: ModerationQueueItemData[];
    total: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/moderation/queue?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0 };
    }
  },

  async makeModerationDecision(targetType: string, targetId: string, action: "APPROVE" | "TAKEDOWN", reason?: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/moderation/${targetType}/${targetId}/decision`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ action, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async applyRestriction(
    targetPersonaId: string,
    actionType: string,
    reason: string,
    strikeCount = 1,
    mfaCode?: string
  ): Promise<unknown> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    };
    if (mfaCode) {
      headers["X-Admin-MFA"] = mfaCode;
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/admin/restrictions`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        target_persona_id: targetPersonaId,
        action_type: actionType,
        reason,
        strike_count: strikeCount,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchAppeals(params: { status?: string; limit?: number; offset?: number } = {}): Promise<{
    items: AppealItemData[];
    total: number;
    pending_count: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.status) q.append("status", params.status);
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/appeals?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0, pending_count: 0 };
    }
  },

  async reviewAppeal(appealId: string, decision: "APPROVE" | "REJECT", resolutionNotes?: string): Promise<AppealItemData> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/appeals/${appealId}/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ decision, resolution_notes: resolutionNotes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchInvitations(params: { limit?: number; offset?: number } = {}): Promise<{
    items: AdminInvitationItemData[];
    total: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/invitations?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0 };
    }
  },

  async revokeInvitation(invitationId: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/invitations/${invitationId}/revoke`, {
      method: "POST",
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchAccounts(params: { limit?: number; offset?: number } = {}): Promise<{
    items: AdminAccountItemData[];
    total: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/accounts?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0 };
    }
  },

  async fetchAuditLogs(params: { action?: string; limit?: number; offset?: number } = {}): Promise<{
    items: AuditLogItemData[];
    total: number;
  }> {
    try {
      const q = new URLSearchParams();
      if (params.action) q.append("action", params.action);
      if (params.limit) q.append("limit", params.limit.toString());
      if (params.offset) q.append("offset", params.offset.toString());

      const res = await fetch(`${API_BASE_URL}/api/v1/admin/audit-logs?${q.toString()}`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return { items: [], total: 0 };
    }
  },

  async setupMfa(): Promise<{ secret: string; otpauth_url: string; instruction: string }> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/mfa/setup`, {
      method: "POST",
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  async verifyMfa(code: string): Promise<unknown> {
    const res = await fetch(`${API_BASE_URL}/api/v1/admin/mfa/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },
};

export const safetyApi = {
  async fetchMyBlocks(): Promise<BlockedPersonaItemData[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/blocks`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  async unblockPersona(personaId: string): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/blocks/${personaId}`, {
      method: "DELETE",
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
  },

  async submitAppeal(moderationActionId: string, reason: string): Promise<AppealItemData> {
    const res = await fetch(`${API_BASE_URL}/api/v1/appeals`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeader(),
      },
      body: JSON.stringify({ moderation_action_id: moderationActionId, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return await res.json();
  },

  async fetchMyAppeals(): Promise<AppealItemData[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/appeals/me`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  async fetchCommunityStandards(): Promise<CommunityStandardRuleData[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/safety/standards`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.rules || [];
    } catch {
      return [];
    }
  },

  async deleteAccount(): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/account`, {
      method: "DELETE",
      headers: { ...getAuthHeader() },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
  },
};

