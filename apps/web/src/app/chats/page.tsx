"use client";

import React, { useState } from "react";
import Link from "next/link";
import { MessageCircle, UserCheck, Lock } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { ChatRequestCard } from "@/components/aftr/ChatRequestCard";
import { FIXTURE_CONVERSATIONS, FIXTURE_CHAT_REQUESTS, FixtureConversation, FixtureChatRequest } from "@/lib/fixtures";

export default function ChatsPage() {
  const [activeTab, setActiveTab] = useState<"conversations" | "requests">("conversations");
  const [conversations, setConversations] = useState<FixtureConversation[]>(FIXTURE_CONVERSATIONS);
  const [requests, setRequests] = useState<FixtureChatRequest[]>(FIXTURE_CHAT_REQUESTS);

  const handleAcceptRequest = (requestId: string) => {
    const req = requests.find((r) => r.id === requestId);
    if (req) {
      const newConv: FixtureConversation = {
        id: `conv-${Date.now()}`,
        other_persona: req.sender_persona,
        last_message: "Connection accepted! Say hello anonymously.",
        last_message_at: new Date().toISOString(),
        unread_count: 0,
        is_active: true,
      };
      setConversations([newConv, ...conversations]);
      setRequests(requests.filter((r) => r.id !== requestId));
    }
  };

  const handleDeclineRequest = (requestId: string) => {
    setRequests(requests.filter((r) => r.id !== requestId));
  };

  const formatTimeAgo = (dateStr: string) => {
    try {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      if (diffMins < 60) return `${Math.max(1, diffMins)}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return "yesterday";
    } catch {
      return "";
    }
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-5">
        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-[#9B72CF]" />
              Private Consent-Based Chats
            </h1>
            <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#62C49A]/15 text-[#62C49A] border border-[#62C49A]/30">
              End-to-End Isolated
            </span>
          </div>
          <p className="text-xs text-[#A49BAF]">
            Communicate safely with accepted connections. Direct messaging strictly requires bilateral consent.
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex items-center gap-2 p-1 rounded-xl bg-[#1C1923] border border-[#2D283B]">
          <button
            type="button"
            onClick={() => setActiveTab("conversations")}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "conversations"
                ? "bg-[#9B72CF] text-[#111016] shadow-sm"
                : "text-[#A49BAF] hover:text-[#F6F1FA]"
            }`}
          >
            Conversations ({conversations.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("requests")}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all relative ${
              activeTab === "requests"
                ? "bg-[#9B72CF] text-[#111016] shadow-sm"
                : "text-[#A49BAF] hover:text-[#F6F1FA]"
            }`}
          >
            Connection Requests ({requests.length})
            {requests.length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.2 rounded-full bg-[#E56A75] text-white text-[10px]">
                {requests.length}
              </span>
            )}
          </button>
        </div>

        {/* Tab 1: Conversations */}
        {activeTab === "conversations" && (
          <div className="space-y-3">
            {conversations.length === 0 ? (
              <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 p-6">
                <Lock className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
                <h3 className="text-sm font-semibold text-[#F6F1FA]">No active conversations</h3>
                <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
                  Explore compatible peers in Discover and send a connection request to begin chatting.
                </p>
                <Link
                  href="/discover"
                  className="inline-block text-xs font-semibold px-4 py-2 rounded-xl bg-[#9B72CF] text-[#111016]"
                >
                  Discover Peers
                </Link>
              </div>
            ) : (
              conversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/chats/${conv.id}`}
                  className="block p-4 rounded-2xl bg-[#1C1923] border border-[#2D283B] hover:border-[#9B72CF]/50 transition-all group shadow-sm"
                >
                  <div className="flex items-center justify-between gap-3">
                    <AnonymousPersona persona={conv.other_persona} size="md" />

                    <div className="text-right shrink-0">
                      <span className="text-[11px] text-[#A49BAF]">
                        {formatTimeAgo(conv.last_message_at)}
                      </span>
                      {conv.unread_count > 0 && (
                        <span className="block mt-1 w-5 h-5 rounded-full bg-[#9B72CF] text-[#111016] font-bold text-[10px] flex items-center justify-center ml-auto">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-[#A49BAF] pl-[50px] line-clamp-1 mt-1 group-hover:text-[#F6F1FA] transition-colors">
                    {conv.last_message}
                  </p>
                </Link>
              ))
            )}
          </div>
        )}

        {/* Tab 2: Connection Requests */}
        {activeTab === "requests" && (
          <div className="space-y-3">
            {requests.length === 0 ? (
              <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-2 p-6">
                <UserCheck className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
                <h3 className="text-sm font-semibold text-[#F6F1FA]">No pending connection requests</h3>
                <p className="text-xs text-[#A49BAF]">
                  When another adult campus peer requests to connect, their note will appear here.
                </p>
              </div>
            ) : (
              requests.map((req) => (
                <ChatRequestCard
                  key={req.id}
                  request={req}
                  onAccept={handleAcceptRequest}
                  onDecline={handleDeclineRequest}
                />
              ))
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
