"use client";

import React, { useState } from "react";
import { UserPlus, Sparkles, Check, Lock, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { FixtureConnection } from "@/lib/fixtures";

interface ConnectionCardProps {
  connection: FixtureConnection;
  onRequestSent?: (connectionId: string) => void;
  className?: string;
}

export function ConnectionCard({
  connection,
  onRequestSent,
  className = "",
}: ConnectionCardProps) {
  const [status, setStatus] = useState<FixtureConnection["status"]>(connection.status);
  const [sending, setSending] = useState<boolean>(false);

  const handleSendRequest = () => {
    setSending(true);
    setTimeout(() => {
      setSending(false);
      setStatus("PENDING");
      onRequestSent?.(connection.id);
    }, 400);
  };

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl transition-all duration-200 hover:border-[#9B72CF]/40 ${className}`}>
      <CardContent className="p-5 space-y-4">
        {/* Header: Persona + Compatibility Score */}
        <div className="flex items-start justify-between gap-3">
          <AnonymousPersona persona={connection.persona} size="md" />

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#9B72CF]/15 border border-[#9B72CF]/40 text-[#DCA7E8] text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 fill-[#DCA7E8]/50" />
            <span>{connection.compatibility_score}% Match</span>
          </div>
        </div>

        {/* Bio snippet if available */}
        {connection.persona.bio && (
          <p className="text-xs text-[#A49BAF] leading-relaxed line-clamp-2">
            &ldquo;{connection.persona.bio}&rdquo;
          </p>
        )}

        {/* Mutual Interests */}
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-[#A49BAF]/70 tracking-wider">
            Shared Adult Interests & Vibes
          </span>
          <div className="flex flex-wrap gap-1.5">
            {connection.mutual_interests.map((interest) => (
              <span
                key={interest}
                className="text-[11px] px-2 py-0.5 rounded-md bg-[#111016] text-[#F6F1FA] border border-[#2D283B]"
              >
                {interest}
              </span>
            ))}
          </div>
        </div>

        {/* Consent-Based Rule Note */}
        <div className="p-2.5 rounded-lg bg-[#111016]/60 border border-[#2D283B]/60 flex items-center gap-2 text-[11px] text-[#A49BAF]">
          <Lock className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
          <span>Requires mutual consent before direct chat unlocks.</span>
        </div>

        {/* Action Button */}
        <div>
          {status === "NONE" && (
            <Button
              type="button"
              size="sm"
              onClick={handleSendRequest}
              disabled={sending}
              className="w-full bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-9 gap-1.5"
            >
              <UserPlus className="w-4 h-4" />
              {sending ? "Sending..." : "Request Anonymous Connection"}
            </Button>
          )}

          {status === "PENDING" && (
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

          {status === "ACCEPTED" && (
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
      </CardContent>
    </Card>
  );
}
