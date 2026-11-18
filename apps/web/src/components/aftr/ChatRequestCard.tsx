"use client";

import React, { useState } from "react";
import { Check, X, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { BlockDialog } from "./BlockDialog";
import { ReportDialog } from "./ReportDialog";
import { FixtureChatRequest } from "@/lib/fixtures";

interface ChatRequestCardProps {
  request: FixtureChatRequest;
  onAccept?: (requestId: string) => void;
  onDecline?: (requestId: string) => void;
  className?: string;
}

export function ChatRequestCard({
  request,
  onAccept,
  onDecline,
  className = "",
}: ChatRequestCardProps) {
  const [status, setStatus] = useState<"PENDING" | "ACCEPTED" | "DECLINED">("PENDING");
  const [blockOpen, setBlockOpen] = useState<boolean>(false);
  const [reportOpen, setReportOpen] = useState<boolean>(false);

  const handleAccept = () => {
    setStatus("ACCEPTED");
    onAccept?.(request.id);
  };

  const handleDecline = () => {
    setStatus("DECLINED");
    onDecline?.(request.id);
  };

  if (status !== "PENDING") {
    return (
      <div className="p-4 rounded-xl bg-[#111016]/60 border border-[#2D283B] text-xs text-[#A49BAF] flex items-center justify-between">
        <span>
          {status === "ACCEPTED"
            ? `Connected with ${request.sender_persona.display_name}. Chat unlocked.`
            : `Request from ${request.sender_persona.display_name} declined.`}
        </span>
        <span className={status === "ACCEPTED" ? "text-[#62C49A] font-semibold" : ""}>
          {status}
        </span>
      </div>
    );
  }

  return (
    <>
      <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl ${className}`}>
        <CardContent className="p-4 sm:p-5 space-y-3.5">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <AnonymousPersona persona={request.sender_persona} size="md" />

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#9B72CF]/15 border border-[#9B72CF]/40 text-[#DCA7E8] text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 fill-[#DCA7E8]/50" />
              <span>{request.compatibility_score}%</span>
            </div>
          </div>

          {/* Note */}
          {request.preview_note && (
            <div className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] text-xs text-[#F6F1FA] italic">
              &ldquo;{request.preview_note}&rdquo;
            </div>
          )}

          {/* Shared Interests */}
          <div className="flex flex-wrap gap-1.5">
            {request.mutual_interests.map((interest) => (
              <span
                key={interest}
                className="text-[11px] px-2 py-0.5 rounded-md bg-[#111016] text-[#A49BAF] border border-[#2D283B]"
              >
                {interest}
              </span>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-[#2D283B] gap-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setReportOpen(true)}
                className="text-[11px] text-[#A49BAF] hover:text-[#E56A75] transition-colors"
              >
                Report
              </button>
              <span className="text-[#A49BAF]/30">•</span>
              <button
                type="button"
                onClick={() => setBlockOpen(true)}
                className="text-[11px] text-[#A49BAF] hover:text-[#E56A75] transition-colors"
              >
                Block
              </button>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleDecline}
                className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8 px-3"
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Decline
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={handleAccept}
                className="bg-[#62C49A] hover:bg-[#62C49A]/90 text-[#111016] font-semibold text-xs h-8 px-3.5"
              >
                <Check className="w-3.5 h-3.5 mr-1" />
                Accept & Chat
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <ReportDialog
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
        targetType="PERSONA"
        targetId={request.sender_persona.id}
        targetAuthor={request.sender_persona.display_name}
      />

      <BlockDialog
        isOpen={blockOpen}
        onClose={() => setBlockOpen(false)}
        personaDisplayName={request.sender_persona.display_name}
        personaId={request.sender_persona.id}
      />
    </>
  );
}
