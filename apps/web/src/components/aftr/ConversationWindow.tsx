"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Shield, MoreVertical, Flag, ShieldAlert, Lock, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { ReportDialog } from "./ReportDialog";
import { BlockDialog } from "./BlockDialog";
import { FixturePersona, CURRENT_USER_PERSONA } from "@/lib/fixtures";

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_persona_id: string;
  sender_pseudonym?: string;
  content: string;
  is_mine?: boolean;
  is_own?: boolean;
  is_deleted?: boolean;
  created_at: string;
}

interface ConversationWindowProps {
  conversationId?: string;
  otherPersona: FixturePersona | {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
    is_active?: boolean;
  };
  myPseudonym?: string;
  otherPseudonym?: string;
  initialMessages: ChatMessage[];
  isBlocked?: boolean;
  isOnline?: boolean;
  isPeerTyping?: boolean;
  onSendMessage?: (content: string) => Promise<void> | void;
  onDeleteMessage?: (messageId: string) => Promise<void> | void;
  onBlockConversation?: () => Promise<void> | void;
  className?: string;
}

export function ConversationWindow({
  conversationId,
  otherPersona,
  myPseudonym,
  otherPseudonym,
  initialMessages,
  isBlocked = false,
  isOnline = false,
  isPeerTyping = false,
  onSendMessage,
  onDeleteMessage,
  onBlockConversation,
  className = "",
}: ConversationWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputText, setInputText] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);
  const [showMenu, setShowMenu] = useState<boolean>(false);
  const [reportOpen, setReportOpen] = useState<boolean>(false);
  const [blockOpen, setBlockOpen] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text || sending || isBlocked) return;

    setSending(true);
    setInputText("");

    try {
      if (onSendMessage) {
        await onSendMessage(text);
      } else {
        const localMsg: ChatMessage = {
          id: `msg-${Date.now()}`,
          conversation_id: conversationId || "conv-active",
          sender_persona_id: CURRENT_USER_PERSONA.id,
          sender_pseudonym: myPseudonym || "Me",
          content: text,
          created_at: new Date().toISOString(),
          is_mine: true,
          is_own: true,
        };
        setMessages((prev) => [...prev, localMsg]);
      }
    } catch {
      // Restore input text if send failed
      setInputText(text);
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (msgId: string) => {
    try {
      if (onDeleteMessage) {
        await onDeleteMessage(msgId);
      }
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId ? { ...m, is_deleted: true, content: "[This message was deleted]" } : m
        )
      );
    } catch {
      // Failed to delete
    }
  };

  const handleConfirmBlock = async () => {
    try {
      if (onBlockConversation) {
        await onBlockConversation();
      }
      setBlockOpen(false);
    } catch {
      setBlockOpen(false);
    }
  };

  const formatMsgTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  const normalizedPersona: FixturePersona = {
    id: otherPersona.id,
    display_name: otherPseudonym || otherPersona.display_name,
    avatar_seed: otherPersona.avatar_seed,
    declared_campus: otherPersona.declared_campus || undefined,
    is_active: otherPersona.is_active ?? true,
  };

  return (
    <>
      <div
        className={`flex flex-col h-[640px] max-h-[82vh] bg-[#1C1923] border border-[#2D283B] rounded-2xl overflow-hidden shadow-lg ${className}`}
      >
        {/* Conversation Header */}
        <div className="p-4 border-b border-[#2D283B] flex items-center justify-between bg-[#111016]/60 backdrop-blur">
          <div className="flex items-center gap-3">
            <AnonymousPersona persona={normalizedPersona} size="md" />
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#F6F1FA]">
                  {otherPseudonym || otherPersona.display_name}
                </span>
                {isOnline && (
                  <span className="w-2 h-2 rounded-full bg-[#62C49A]" title="Online now" />
                )}
              </div>
              <span className="text-[10px] text-[#A49BAF]">
                Conversation Pseudonym • End-to-End Isolated
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowMenu(!showMenu)}
                className="p-1.5 rounded-lg text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] transition-colors"
                aria-label="Conversation options"
              >
                <MoreVertical className="w-4 h-4" />
              </button>

              {showMenu && (
                <div className="absolute right-0 mt-1 w-40 bg-[#111016] border border-[#2D283B] rounded-xl shadow-xl z-20 py-1 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      setShowMenu(false);
                      setReportOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#A49BAF] hover:text-[#E56A75] hover:bg-[#1C1923]"
                  >
                    <Flag className="w-3.5 h-3.5" />
                    Report Message/Chat
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowMenu(false);
                      setBlockOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#E56A75] hover:bg-[#1C1923]"
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Block Conversation
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Consent & Safety Guarantee Banner */}
        <div className="px-4 py-2 bg-[#9B72CF]/10 border-b border-[#2D283B] flex items-center justify-between text-[11px] text-[#DCA7E8]">
          <div className="flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
            <span>
              Bilateral consent verified. Messages are encrypted at rest with zero real-identity leakage.
            </span>
          </div>
          {myPseudonym && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#111016] text-[#A49BAF]">
              You: {myPseudonym}
            </span>
          )}
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-[#111016]/30">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#A49BAF]">
              <Shield className="w-8 h-8 text-[#9B72CF]/40" />
              <p className="text-xs font-medium text-[#F6F1FA]">Direct Connection Active</p>
              <p className="text-[11px] max-w-xs">
                You both agreed to connect. Say hello and break the ice anonymously.
              </p>
            </div>
          ) : (
            messages.map((msg) => {
              const isOwn = msg.is_mine ?? msg.is_own ?? false;
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col group ${isOwn ? "items-end" : "items-start"}`}
                >
                  <div className="flex items-center gap-1.5 max-w-[80%]">
                    {isOwn && !msg.is_deleted && (
                      <button
                        type="button"
                        onClick={() => handleDelete(msg.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-[#A49BAF] hover:text-[#E56A75] transition-opacity"
                        title="Delete message"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                    <div
                      className={`rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                        msg.is_deleted
                          ? "bg-[#111016] text-[#A49BAF]/60 italic border border-[#2D283B]"
                          : isOwn
                          ? "bg-gradient-to-r from-[#9B72CF] to-[#805ad5] text-white rounded-br-none shadow-sm"
                          : "bg-[#262230] text-[#F6F1FA] border border-[#2D283B] rounded-bl-none"
                      }`}
                    >
                      <p>{msg.content}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 px-1 mt-1 text-[10px] text-[#A49BAF]/60">
                    <span>{formatMsgTime(msg.created_at)}</span>
                    {msg.sender_pseudonym && (
                      <span>• {msg.sender_pseudonym}</span>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {isPeerTyping && (
            <div className="flex items-center gap-2 text-xs text-[#A49BAF] italic">
              <span className="w-2 h-2 rounded-full bg-[#9B72CF] animate-pulse" />
              <span>{otherPseudonym || otherPersona.display_name} is typing...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Message Input Footer */}
        {isBlocked ? (
          <div className="p-3 border-t border-[#2D283B] bg-[#111016] text-center text-xs text-[#E56A75]">
            This conversation is blocked. Messaging is disabled.
          </div>
        ) : (
          <form
            onSubmit={handleSend}
            className="p-3 border-t border-[#2D283B] bg-[#111016] flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={`Message ${otherPseudonym || otherPersona.display_name} anonymously...`}
              disabled={sending}
              maxLength={5000}
              className="flex-1 rounded-xl bg-[#1C1923] border border-[#2D283B] px-3.5 py-2 text-xs sm:text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
            />
            <Button
              type="submit"
              disabled={!inputText.trim() || sending}
              className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold h-9 px-3.5 text-xs gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{sending ? "..." : "Send"}</span>
            </Button>
          </form>
        )}
      </div>

      <ReportDialog
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
        targetType="CONVERSATION"
        targetId={conversationId || otherPersona.id}
        targetAuthor={otherPseudonym || otherPersona.display_name}
      />

      <BlockDialog
        isOpen={blockOpen}
        onClose={() => setBlockOpen(false)}
        personaDisplayName={otherPseudonym || otherPersona.display_name}
        personaId={otherPersona.id}
        onBlocked={handleConfirmBlock}
      />
    </>
  );
}
