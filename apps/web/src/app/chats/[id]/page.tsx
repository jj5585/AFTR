"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { ConversationWindow } from "@/components/aftr/ConversationWindow";
import { FIXTURE_CONVERSATIONS, FIXTURE_MESSAGES } from "@/lib/fixtures";

export default function ChatDetailPage() {
  const params = useParams();
  const convId = params.id as string;

  const conv =
    FIXTURE_CONVERSATIONS.find((c) => c.id === convId) || FIXTURE_CONVERSATIONS[0];
  const messages = FIXTURE_MESSAGES.filter(
    (m) => m.conversation_id === conv.id || m.conversation_id === "conv-1"
  );

  return (
    <AppShell showRightPanel={false}>
      <div className="max-w-3xl mx-auto space-y-4">
        {/* Back Link */}
        <div className="flex items-center justify-between">
          <Link
            href="/chats"
            className="inline-flex items-center gap-1.5 text-xs text-[#A49BAF] hover:text-[#F6F1FA] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to All Conversations</span>
          </Link>
          <span className="text-[10px] font-mono text-[#A49BAF]">
            Session: {conv.id}
          </span>
        </div>

        {/* Conversation Window */}
        <ConversationWindow
          otherPersona={conv.other_persona}
          initialMessages={messages}
        />
      </div>
    </AppShell>
  );
}
