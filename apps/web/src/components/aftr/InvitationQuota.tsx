"use client";

import React, { useState } from "react";
import { KeyRound, ShieldCheck, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FixtureInvitation } from "@/lib/fixtures";

interface InvitationQuotaProps {
  invitations: FixtureInvitation[];
  maxQuota?: number;
  onGenerateInvite?: (targetEmail: string) => void;
  className?: string;
}

export function InvitationQuota({
  invitations,
  maxQuota = 3,
  onGenerateInvite,
  className = "",
}: InvitationQuotaProps) {
  const [showGenerateModal, setShowGenerateModal] = useState<boolean>(false);
  const [targetEmail, setTargetEmail] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  const usedCount = invitations.length;
  const remainingCount = Math.max(0, maxQuota - usedCount);

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetEmail.trim()) return;
    setIsGenerating(true);
    setTimeout(() => {
      onGenerateInvite?.(targetEmail.trim());
      setIsGenerating(false);
      setTargetEmail("");
      setShowGenerateModal(false);
    }, 600);
  };

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl shadow-sm ${className}`}>
      <CardContent className="p-4 sm:p-5 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-[#9B72CF]" />
            <h3 className="text-sm font-bold text-[#F6F1FA]">Invitation Quota</h3>
          </div>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#9B72CF]/20 text-[#DCA7E8] border border-[#9B72CF]/30">
            {remainingCount} / {maxQuota} Available
          </span>
        </div>

        {/* 3 Slots Visual Indicator */}
        <div className="grid grid-cols-3 gap-2">
          {Array.from({ length: maxQuota }).map((_, index) => {
            const inv = invitations[index];
            let statusColor = "bg-[#111016] border-[#2D283B] text-[#A49BAF]";
            let label = `Slot ${index + 1}: Available`;

            if (inv) {
              if (inv.status === "ACTIVE") {
                statusColor = "bg-[#62C49A]/15 border-[#62C49A]/50 text-[#62C49A]";
                label = `Slot ${index + 1}: Active`;
              } else if (inv.status === "REDEEMED") {
                statusColor = "bg-[#9B72CF]/15 border-[#9B72CF]/50 text-[#DCA7E8]";
                label = `Slot ${index + 1}: Claimed`;
              } else {
                statusColor = "bg-[#E56A75]/15 border-[#E56A75]/40 text-[#E56A75]";
                label = `Slot ${index + 1}: ${inv.status}`;
              }
            }

            return (
              <div
                key={index}
                title={label}
                className={`p-2.5 rounded-xl border text-center flex flex-col items-center justify-center space-y-1 transition-all ${statusColor}`}
              >
                <span className="text-[10px] font-bold uppercase tracking-wider">
                  Slot #{index + 1}
                </span>
                <span className="text-xs font-medium truncate max-w-full">
                  {inv ? inv.status : "Empty"}
                </span>
              </div>
            );
          })}
        </div>

        {/* Product Rules Explanation */}
        <div className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] text-[11px] text-[#A49BAF] space-y-1 leading-relaxed">
          <p className="font-semibold text-[#F6F1FA] flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-[#62C49A]" />
            Strict AFTR Invitation Protocol:
          </p>
          <ul className="list-disc list-inside space-y-0.5 pl-1">
            <li>Every eligible member receives strictly 3 invitations.</li>
            <li>Tokens expire 72 hours from generation.</li>
            <li>Single-use only and cryptographically bound to recipient email.</li>
            <li>Slots do not replenish after expiration or redemption.</li>
          </ul>
        </div>

        {/* Generate Trigger */}
        {remainingCount > 0 && !showGenerateModal && (
          <Button
            type="button"
            size="sm"
            onClick={() => setShowGenerateModal(true)}
            className="w-full bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-9 gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Issue New Single-Use Invitation
          </Button>
        )}

        {/* Inline Generate Form */}
        {showGenerateModal && (
          <form onSubmit={handleGenerate} className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-[#F6F1FA]">
                Recipient Email to Bind
              </label>
              <input
                type="email"
                required
                value={targetEmail}
                onChange={(e) => setTargetEmail(e.target.value)}
                placeholder="friend@example.com (any email, no .edu required)"
                className="w-full rounded-lg bg-[#1C1923] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
              />
              <p className="text-[10px] text-[#A49BAF]">
                College email is never required. Any valid adult email is accepted.
              </p>
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowGenerateModal(false)}
                className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={isGenerating || !targetEmail.trim()}
                className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
              >
                {isGenerating ? "Issuing..." : "Issue Invitation (72h)"}
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
