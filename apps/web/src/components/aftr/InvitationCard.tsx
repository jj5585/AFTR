"use client";

import React, { useState } from "react";
import { Copy, Check, Clock, Trash2, Mail } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FixtureInvitation } from "@/lib/fixtures";

interface InvitationCardProps {
  invitation: FixtureInvitation;
  onRevoke?: (invitationId: string) => void;
  className?: string;
}

export function InvitationCard({
  invitation,
  onRevoke,
  className = "",
}: InvitationCardProps) {
  const [copied, setCopied] = useState<boolean>(false);
  const [status, setStatus] = useState<FixtureInvitation["status"]>(invitation.status);

  const inviteUrl = `https://aftr.app/invite/${invitation.token}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRevoke = () => {
    setStatus("REVOKED");
    onRevoke?.(invitation.id);
  };

  const formatHoursRemaining = (expiresAtStr: string) => {
    try {
      const diffMs = new Date(expiresAtStr).getTime() - Date.now();
      if (diffMs <= 0) return "Expired";
      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      return `${hours}h remaining`;
    } catch {
      return "72h window";
    }
  };

  const getStatusBadge = (s: FixtureInvitation["status"]) => {
    switch (s) {
      case "ACTIVE":
        return <Badge className="bg-[#62C49A]/20 text-[#62C49A] border-[#62C49A]/40 text-[10px]">Active</Badge>;
      case "REDEEMED":
        return <Badge className="bg-[#9B72CF]/20 text-[#DCA7E8] border-[#9B72CF]/40 text-[10px]">Redeemed</Badge>;
      case "EXPIRED":
        return <Badge className="bg-[#A49BAF]/20 text-[#A49BAF] border-[#A49BAF]/40 text-[10px]">Expired</Badge>;
      case "REVOKED":
        return <Badge className="bg-[#E56A75]/20 text-[#E56A75] border-[#E56A75]/40 text-[10px]">Revoked</Badge>;
    }
  };

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl ${className}`}>
      <CardContent className="p-4 sm:p-5 space-y-3.5">
        {/* Top: Status & Token */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold text-[#F6F1FA]">
              {invitation.token}
            </span>
            {getStatusBadge(status)}
          </div>

          <div className="flex items-center gap-1 text-[11px] text-[#A49BAF]">
            <Clock className="w-3.5 h-3.5" />
            <span>{formatHoursRemaining(invitation.expires_at)}</span>
          </div>
        </div>

        {/* Bound Email Indicator */}
        <div className="flex items-center gap-2 text-xs text-[#A49BAF] p-2.5 rounded-xl bg-[#111016] border border-[#2D283B]">
          <Mail className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
          <span>Cryptographically bound to:</span>
          <span className="font-mono font-medium text-[#F6F1FA]">
            {invitation.bound_email_masked}
          </span>
        </div>

        {/* Redeemed Note */}
        {invitation.redeemed_by_persona && (
          <p className="text-[11px] text-[#62C49A]">
            Successfully redeemed by anonymous persona: <strong>{invitation.redeemed_by_persona}</strong>
          </p>
        )}

        {/* Action Controls */}
        {status === "ACTIVE" && (
          <div className="flex items-center gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="flex-1 border-[#2D283B] text-[#F6F1FA] hover:bg-[#2D283B] text-xs h-8 gap-1.5"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-[#62C49A]" />
                  <span>Link Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-[#9B72CF]" />
                  <span>Copy Invite Link</span>
                </>
              )}
            </Button>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRevoke}
              className="border-[#2D283B] text-[#E56A75] hover:bg-[#E56A75]/10 hover:border-[#E56A75]/30 text-xs h-8 px-2.5"
              title="Revoke invitation"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
