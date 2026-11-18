"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, AlertCircle } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { ConversationWindow, ChatMessage } from "@/components/aftr/ConversationWindow";
import { FIXTURE_CONVERSATIONS, FIXTURE_MESSAGES, FixturePersona } from "@/lib/fixtures";
import { messagingApi } from "@/lib/api";

interface ConversationDetailData {
  id: string;
  participants: Array<{
    persona_id: string;
    conversation_pseudonym: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
    is_online: boolean;
  }>;
  my_conversation_pseudonym: string;
  is_active: boolean;
  is_blocked: boolean;
}

export default function ChatDetailPage() {
  const params = useParams();
  const router = useRouter();
  const convId = params.id as string;

  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [otherPersona, setOtherPersona] = useState<FixturePersona | null>(null);
  const [myPseudonym, setMyPseudonym] = useState<string>("Me");
  const [otherPseudonym, setOtherPseudonym] = useState<string>("Anonymous");
  const [isBlocked, setIsBlocked] = useState<boolean>(false);
  const [isPeerTyping, setIsPeerTyping] = useState<boolean>(false);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  const loadConversation = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch conversation detail
      const detail = (await messagingApi.fetchConversationDetail(convId)) as ConversationDetailData;
      setMyPseudonym(detail.my_conversation_pseudonym);
      setIsBlocked(detail.is_blocked || !detail.is_active);

      // Find other participant
      const otherPart = detail.participants.find(
        (p) => p.conversation_pseudonym !== detail.my_conversation_pseudonym
      ) || detail.participants[0];

      if (otherPart) {
        setOtherPseudonym(otherPart.conversation_pseudonym);
        setIsOnline(otherPart.is_online);
        setOtherPersona({
          id: otherPart.persona_id,
          display_name: otherPart.display_name,
          avatar_seed: otherPart.avatar_seed,
          declared_campus: otherPart.declared_campus || undefined,
          is_active: true,
        });
      }

      // 2. Fetch messages
      const msgsRes = await messagingApi.fetchMessages(convId);
      if (msgsRes.items && msgsRes.items.length > 0) {
        setMessages(msgsRes.items);
      }

      // 3. Mark conversation read
      await messagingApi.markConversationRead(convId);
    } catch {
      // Fallback to local fixtures for demo or unauthenticated state
      const foundConv = FIXTURE_CONVERSATIONS.find((c) => c.id === convId) || FIXTURE_CONVERSATIONS[0];
      setOtherPersona(foundConv.other_persona);
      setOtherPseudonym(foundConv.other_persona.display_name);
      const filteredMsgs: ChatMessage[] = FIXTURE_MESSAGES.filter(
        (m) => m.conversation_id === convId || m.conversation_id === "conv-1"
      ).map((m) => ({
        id: m.id,
        conversation_id: m.conversation_id,
        sender_persona_id: m.sender_persona_id,
        sender_pseudonym: m.is_own ? "Me" : foundConv.other_persona.display_name,
        content: m.content,
        is_mine: m.is_own,
        is_own: m.is_own,
        is_deleted: false,
        created_at: m.created_at,
      }));
      setMessages(filteredMsgs);
    } finally {
      setLoading(false);
    }
  }, [convId]);

  useEffect(() => {
    loadConversation();
  }, [loadConversation]);

  // Real-time WebSocket connection
  useEffect(() => {
    if (!convId || typeof window === "undefined") return;

    try {
      const wsUrl = messagingApi.getWebSocketUrl(convId);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "new_message" && data.message) {
            setMessages((prev) => {
              // Avoid duplicate if already inserted
              if (prev.some((m) => m.id === data.message.id)) return prev;
              return [
                ...prev,
                {
                  id: data.message.id,
                  conversation_id: data.message.conversation_id,
                  sender_persona_id: data.message.sender_persona_id,
                  sender_pseudonym: data.message.sender_pseudonym,
                  content: data.message.content,
                  is_mine: false,
                  is_own: false,
                  is_deleted: data.message.is_deleted,
                  created_at: data.message.created_at,
                },
              ];
            });
            // Auto mark read on receiving while active
            messagingApi.markConversationRead(convId);
          } else if (data.type === "message_deleted") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === data.message_id
                  ? { ...m, is_deleted: true, content: "[This message was deleted]" }
                  : m
              )
            );
          } else if (data.type === "typing") {
            setIsPeerTyping(Boolean(data.is_typing));
          } else if (data.type === "user_status") {
            setIsOnline(Boolean(data.is_online));
          } else if (data.type === "conversation_blocked") {
            setIsBlocked(true);
          }
        } catch {
          // Ignore invalid frame
        }
      };

      ws.onerror = () => {
        // Silent WebSocket error, falls back to polling / HTTP
      };

      return () => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      };
    } catch {
      // WS unsupported or offline
    }
  }, [convId]);

  const handleSendMessage = async (content: string) => {
    try {
      const sent = await messagingApi.sendMessage(convId, content);
      setMessages((prev) => {
        if (prev.some((m) => m.id === sent.id)) return prev;
        return [...prev, sent];
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to send message";
      setErrorMsg(msg);
      throw err;
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    try {
      await messagingApi.deleteMessage(messageId);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, is_deleted: true, content: "[This message was deleted]" } : m
        )
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete message";
      setErrorMsg(msg);
    }
  };

  const handleBlockConversation = async () => {
    try {
      await messagingApi.blockConversation(convId);
      setIsBlocked(true);
      router.push("/chats");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to block conversation";
      setErrorMsg(msg);
    }
  };

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
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-[#A49BAF]">
              Session: {convId.slice(0, 8)}...
            </span>
            <button
              type="button"
              onClick={loadConversation}
              className="p-1 text-[#A49BAF] hover:text-[#F6F1FA] transition-colors"
              title="Refresh messages"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#9B72CF]" : ""}`} />
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/30 flex items-center gap-2 text-xs text-[#F6F1FA]">
            <AlertCircle className="w-4 h-4 text-[#E56A75] shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Conversation Window */}
        {otherPersona && (
          <ConversationWindow
            conversationId={convId}
            otherPersona={otherPersona}
            myPseudonym={myPseudonym}
            otherPseudonym={otherPseudonym}
            initialMessages={messages}
            isBlocked={isBlocked}
            isOnline={isOnline}
            isPeerTyping={isPeerTyping}
            onSendMessage={handleSendMessage}
            onDeleteMessage={handleDeleteMessage}
            onBlockConversation={handleBlockConversation}
          />
        )}
      </div>
    </AppShell>
  );
}
