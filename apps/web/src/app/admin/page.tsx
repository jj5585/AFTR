"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Activity,
  UserX,
  Trash2,
} from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FIXTURE_MODERATION_ITEMS,
  FIXTURE_AUDIT_LOGS,
  FixtureModerationItem,
  FixtureAuditLog,
} from "@/lib/fixtures";

export default function AdminPage() {
  const [items, setItems] = useState<FixtureModerationItem[]>(FIXTURE_MODERATION_ITEMS);
  const [auditLogs, setAuditLogs] = useState<FixtureAuditLog[]>(FIXTURE_AUDIT_LOGS);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const handleAction = (
    itemId: string,
    action: "DISMISS" | "TAKEDOWN" | "BAN"
  ) => {
    const item = items.find((i) => i.id === itemId);
    if (!item) return;

    // Remove or resolve item
    setItems(items.filter((i) => i.id !== itemId));

    // Append to audit log
    const newLog: FixtureAuditLog = {
      id: `log-${Date.now()}`,
      actor: "MODERATOR_SESSION",
      action: action === "TAKEDOWN" ? "CONTENT_REMOVED" : action === "BAN" ? "PERSONA_SUSPENDED" : "REPORT_DISMISSED",
      resource_type: item.target_type.toLowerCase(),
      resource_id: item.target_id,
      details: `Action ${action} executed for reason: ${item.reason}`,
      timestamp_utc: new Date().toISOString(),
    };
    setAuditLogs([newLog, ...auditLogs]);

    setActionNotice(`Successfully processed ${item.target_type} (${action}).`);
    setTimeout(() => setActionNotice(null), 3000);
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-[#E56A75]" />
              Safety Moderation & Audit Console
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#E56A75]/15 text-[#E56A75] border border-[#E56A75]/30">
              Admin & Moderator Level
            </span>
          </div>
          <p className="text-xs text-[#A49BAF]">
            Review flagged user reports, enforce community safety boundaries, and inspect cryptographic audit logs.
          </p>
        </div>

        {actionNotice && (
          <div className="p-3 rounded-xl bg-[#62C49A]/15 border border-[#62C49A]/40 text-xs text-[#62C49A] flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{actionNotice}</span>
          </div>
        )}

        {/* Section 1: Pending Moderation Queue */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#F6F1FA] uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Pending Review Queue ({items.length})
            </h2>
            <span className="text-[11px] text-[#A49BAF]">
              Pre-Public Beta Moderation Active
            </span>
          </div>

          {items.length === 0 ? (
            <div className="py-12 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] p-6 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-[#62C49A] mx-auto" />
              <h3 className="text-sm font-semibold text-[#F6F1FA]">Queue Clean</h3>
              <p className="text-xs text-[#A49BAF]">
                No pending content or persona flags requiring human intervention.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <Card key={item.id} className="bg-[#1C1923] border-[#2D283B] rounded-2xl shadow-sm">
                  <CardContent className="p-4 sm:p-5 space-y-3.5">
                    {/* Header: Type + Reason + Reported By */}
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-[#E56A75]/20 text-[#E56A75] border-[#E56A75]/40 text-[10px]">
                          {item.target_type} REPORT
                        </Badge>
                        <span className="text-xs font-bold text-[#F6F1FA]">
                          {item.reason}
                        </span>
                      </div>

                      <span className="text-[11px] text-[#A49BAF]">
                        Reported by: <strong className="text-[#DCA7E8]">{item.reporter_persona}</strong>
                      </span>
                    </div>

                    {/* Content Preview */}
                    <div className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] space-y-1">
                      <span className="text-[10px] uppercase font-bold text-[#A49BAF]/70">
                        Content Excerpt:
                      </span>
                      <p className="text-xs text-[#F6F1FA] font-mono leading-relaxed">
                        &ldquo;{item.content_preview}&rdquo;
                      </p>
                    </div>

                    {/* Reporter Details */}
                    {item.details && (
                      <p className="text-xs text-[#A49BAF]">
                        <strong className="text-[#F6F1FA]">Context:</strong> {item.details}
                      </p>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#2D283B]">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleAction(item.id, "DISMISS")}
                        className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8"
                      >
                        Dismiss
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => handleAction(item.id, "TAKEDOWN")}
                        className="bg-[#E56A75] hover:bg-[#E56A75]/90 text-white font-medium text-xs h-8 gap-1.5"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Take Down Content
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => handleAction(item.id, "BAN")}
                        className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 gap-1.5"
                      >
                        <UserX className="w-3.5 h-3.5" />
                        Suspend Persona
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Section 2: Audit Trail Stream */}
        <div className="space-y-3 pt-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-[#F6F1FA] uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#9B72CF]" />
              Immutable Audit Log Stream
            </h2>
            <span className="text-[11px] text-[#62C49A]">
              Append-Only Journal
            </span>
          </div>

          <div className="rounded-2xl bg-[#1C1923] border border-[#2D283B] overflow-hidden">
            <div className="divide-y divide-[#2D283B]">
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-3.5 sm:p-4 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-[#111016]/40 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[#DCA7E8]">
                        {log.action}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#111016] border border-[#2D283B] text-[#A49BAF]">
                        {log.resource_type}:{log.resource_id}
                      </span>
                      <span className="text-[10px] text-[#A49BAF]/70">
                        Actor: {log.actor}
                      </span>
                    </div>
                    <p className="text-[#A49BAF] text-[11px]">{log.details}</p>
                  </div>

                  <span className="text-[10px] font-mono text-[#A49BAF]/60 shrink-0">
                    {new Date(log.timestamp_utc).toLocaleTimeString()} UTC
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
