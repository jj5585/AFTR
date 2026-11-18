"use client";

import React, { useState } from "react";
import { UserPlus, Sparkles, Check, Lock, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { FixturePersona } from "@/lib/fixtures";

export interface AnyConnectionItem {
  id: string;
  persona: FixturePersona | {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
    bio?: string;
    interests?: string[];
    is_active?: boolean;
  };
  compatibility_score: number;
  mutual_interests: string[];
  relationship_intention?: string | null;
  status?: string;
  connection_status?: string;
}

interface ConnectionCardProps {
  connection: AnyConnectionItem;
  onRequestSent?: (connectionId: string, note?: string) => Promise<void> | void;
  className?: string;
}

export function ConnectionCard({
  connection,
  onRequestSent,
  className = "",
}: ConnectionCardProps) {
  const initialStatus = connection.connection_status || connection.status || "NONE";
  const [status, setStatus] = useState<string>(initialStatus);
  const [sending, setSending] = useState<boolean>(false);
  const [showNoteInput, setShowNoteInput] = useState<boolean>(false);
  const [introNote, setIntroNote] = useState<string>("");

  const normalizedPersona: FixturePersona = {
    id: connection.persona.id,
    display_name: connection.persona.display_name,
    avatar_seed: connection.persona.avatar_seed,
    declared_campus: connection.persona.declared_campus || undefined,
    bio: "bio" in connection.persona ? connection.persona.bio : undefined,
    interests: "interests" in connection.persona ? connection.persona.interests : undefined,
    is_active: connection.persona.is_active ?? true,
  };

  const handleSendRequest = async () => {
    setSending(true);
    try {
      if (onRequestSent) {
        await onRequestSent(connection.id, introNote.trim() || undefined);
      }
      setStatus("PENDING");
      setShowNoteInput(false);
    } catch {
      // Keep state
    } finally {
      setSending(false);
    }
  };

  const isPending = status === "PENDING" || status === "PENDING_SENT";
  const isAccepted = status === "ACCEPTED";

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl transition-all duration-200 hover:border-[#9B72CF]/40 ${className}`}>
      <CardContent className="p-5 space-y-4">
        {/* Header: Persona + Compatibility Score */}
        <div className="flex items-start justify-between gap-3">
          <AnonymousPersona persona={normalizedPersona} size="md" />

          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#9B72CF]/15 border border-[#9B72CF]/40 text-[#DCA7E8] text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 fill-[#DCA7E8]/50" />
              <span>{Math.round(connection.compatibility_score)}% Match</span>
            </div>
            {connection.relationship_intention && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[#111016] text-[#A49BAF] border border-[#2D283B]">
                {connection.relationship_intention}
              </span>
            )}
          </div>
        </div>

        {/* Bio snippet if available */}
        {"bio" in connection.persona && connection.persona.bio && (
          <p className="text-xs text-[#A49BAF] leading-relaxed line-clamp-2">
            &ldquo;{connection.persona.bio}&rdquo;
          </p>
        )}

        {/* Mutual Interests */}
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-[#A49BAF]/70 tracking-wider">
            Shared Interests & Vibes
          </span>
          <div className="flex flex-wrap gap-1.5">
            {connection.mutual_interests && connection.mutual_interests.length > 0 ? (
              connection.mutual_interests.map((interest) => (
                <span
                  key={interest}
                  className="text-[11px] px-2 py-0.5 rounded-md bg-[#111016] text-[#F6F1FA] border border-[#2D283B]"
                >
                  {interest}
                </span>
              ))
            ) : (
              <span className="text-[11px] text-[#A49BAF]/60 italic">Open campus connection</span>
            )}
          </div>
        </div>

        {/* Consent-Based Rule Note */}
        <div className="p-2.5 rounded-lg bg-[#111016]/60 border border-[#2D283B]/60 flex items-center gap-2 text-[11px] text-[#A49BAF]">
          <Lock className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
          <span>Requires mutual consent before direct chat unlocks.</span>
        </div>

        {/* Optional intro note composer */}
        {showNoteInput && (
          <div className="space-y-2 pt-1">
            <input
              type="text"
              value={introNote}
              onChange={(e) => setIntroNote(e.target.value)}
              placeholder="Add a polite intro note (optional)..."
              maxLength={255}
              className="w-full text-xs rounded-xl bg-[#111016] border border-[#2D283B] px-3 py-2 text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
            />
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                onClick={handleSendRequest}
                disabled={sending}
                className="flex-1 bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
              >
                {sending ? "Sending..." : "Confirm & Send"}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setShowNoteInput(false)}
                className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Action Button */}
        {!showNoteInput && (
          <div>
            {!isPending && !isAccepted && (
              <Button
                type="button"
                size="sm"
                onClick={() => setShowNoteInput(true)}
                className="w-full bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-9 gap-1.5"
              >
                <UserPlus className="w-4 h-4" />
                Request Anonymous Connection
              </Button>
            )}

            {isPending && (
              <Button
                type="button"
                size="sm"
                disabled
                className="w-full bg-[#111016] border border-[#2D283B] text-[#A49BAF] text-xs h-9 gap-1.5 cursor-not-allowed"
              >
                <Check className="w-4 h-4 text-[#62C49A]" />
                Connection Request Pending
              </Button>
            )}

            {isAccepted && (
              <Button
                type="button"
                size="sm"
                disabled
                className="w-full bg-[#62C49A]/20 text-[#62C49A] border border-[#62C49A]/40 text-xs h-9 gap-1.5"
              >
                <ShieldCheck className="w-4 h-4" />
                Connected
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
