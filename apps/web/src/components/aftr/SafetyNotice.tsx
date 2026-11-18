"use client";

import React, { useState } from "react";
import { ShieldCheck, X, EyeOff, Lock, UserCheck, Sparkles } from "lucide-react";

interface SafetyNoticeProps {
  className?: string;
}

export function SafetyNotice({ className = "" }: SafetyNoticeProps) {
  const [dismissed, setDismissed] = useState<boolean>(false);

  if (dismissed) return null;

  return (
    <div
      className={`relative p-4 rounded-2xl bg-gradient-to-r from-[#9B72CF]/15 via-[#1C1923] to-[#1C1923] border border-[#9B72CF]/30 shadow-md ${className}`}
    >
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="absolute top-3 right-3 text-[#A49BAF] hover:text-[#F6F1FA] p-1 rounded-md transition-colors"
        aria-label="Dismiss safety notice"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-[#9B72CF]/20 text-[#DCA7E8] flex items-center justify-center shrink-0 mt-0.5">
          <ShieldCheck className="w-5 h-5" />
        </div>

        <div className="space-y-1.5 pr-6">
          <h4 className="text-xs sm:text-sm font-bold text-[#F6F1FA] flex items-center gap-1.5">
            <span>AFTR Safety & Privacy Charter</span>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-[#62C49A]/20 text-[#62C49A] border border-[#62C49A]/30">
              18+ Assured
            </span>
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px] text-[#A49BAF]">
            <div className="flex items-center gap-1.5">
              <EyeOff className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
              <span>Identity separated from real email & auth</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
              <span>Private chats require mutual consent</span>
            </div>
            <div className="flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
              <span>Zero college email or student ID surveillance</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
              <span>Self-declared campus & single-use 72h invites</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
