"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Shield, MoreVertical, Flag, ShieldAlert, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { ReportDialog } from "./ReportDialog";
import { BlockDialog } from "./BlockDialog";
import { FixturePersona, FixtureMessage, CURRENT_USER_PERSONA } from "@/lib/fixtures";

interface ConversationWindowProps {
  otherPersona: FixturePersona;
  initialMessages: FixtureMessage[];
  onSendMessage?: (content: string) => void;
  className?: string;
}

export function ConversationWindow({
  otherPersona,
  initialMessages,
  onSendMessage,
  className = "",
}: ConversationWindowProps) {
  const [messages, setMessages] = useState<FixtureMessage[]>(initialMessages);
  const [inputText, setInputText] = useState<string>("");
  const [showMenu, setShowMenu] = useState<boolean>(false);
  const [reportOpen, setReportOpen] = useState<boolean>(false);
  const [blockOpen, setBlockOpen] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMsg: FixtureMessage = {
      id: `msg-${Date.now()}`,
      conversation_id: "conv-active",
      sender_persona_id: CURRENT_USER_PERSONA.id,
      content: inputText.trim(),
      created_at: new Date().toISOString(),
      is_own: true,
    };

    setMessages((prev) => [...prev, newMsg]);
    onSendMessage?.(inputText.trim());
    setInputText("");
  };

  const formatMsgTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <>
      <div
        className={`flex flex-col h-[600px] max-h-[80vh] bg-[#1C1923] border border-[#2D283B] rounded-2xl overflow-hidden shadow-lg ${className}`}
      >
        {/* Conversation Header */}
        <div className="p-4 border-b border-[#2D283B] flex items-center justify-between bg-[#111016]/60 backdrop-blur">
          <AnonymousPersona persona={otherPersona} size="md" />

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
                <div className="absolute right-0 mt-1 w-36 bg-[#111016] border border-[#2D283B] rounded-xl shadow-xl z-20 py-1 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      setShowMenu(false);
                      setReportOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#A49BAF] hover:text-[#E56A75] hover:bg-[#1C1923]"
                  >
                    <Flag className="w-3.5 h-3.5" />
                    Report Chat
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowMenu(false);
                      setBlockOpen(true);
                    }}
                    className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#A49BAF] hover:text-[#E56A75] hover:bg-[#1C1923]"
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Block Persona
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Consent & Safety Banner */}
        <div className="px-4 py-2 bg-[#9B72CF]/10 border-b border-[#2D283B] flex items-center gap-2 text-[11px] text-[#DCA7E8]">
          <Lock className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
          <span>
            Consent verified. All communications are pseudonymous and end-to-end isolated from real identities.
          </span>
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
              const isOwn = msg.is_own ?? (msg.sender_persona_id === CURRENT_USER_PERSONA.id);
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isOwn ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                      isOwn
                        ? "bg-gradient-to-r from-[#9B72CF] to-[#805ad5] text-white rounded-br-none shadow-sm"
                        : "bg-[#262230] text-[#F6F1FA] border border-[#2D283B] rounded-bl-none"
                    }`}
                  >
                    <p>{msg.content}</p>
                  </div>
                  <span className="text-[10px] text-[#A49BAF]/60 px-1 mt-1">
                    {formatMsgTime(msg.created_at)}
                  </span>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input Footer */}
        <form
          onSubmit={handleSend}
          className="p-3 border-t border-[#2D283B] bg-[#111016] flex items-center gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={`Message ${otherPersona.display_name} anonymously...`}
            className="flex-1 rounded-xl bg-[#1C1923] border border-[#2D283B] px-3.5 py-2 text-xs sm:text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
          />
          <Button
            type="submit"
            disabled={!inputText.trim()}
            className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold h-9 px-3.5 text-xs gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </form>
      </div>

      <ReportDialog
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
        targetType="PERSONA"
        targetId={otherPersona.id}
        targetAuthor={otherPersona.display_name}
      />

      <BlockDialog
        isOpen={blockOpen}
        onClose={() => setBlockOpen(false)}
        personaDisplayName={otherPersona.display_name}
        personaId={otherPersona.id}
      />
    </>
  );
}
