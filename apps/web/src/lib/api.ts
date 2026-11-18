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
