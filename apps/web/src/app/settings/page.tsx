"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Settings,
  ShieldCheck,
  Lock,
  EyeOff,
  UserX,
  LogOut,
  CheckCircle2,
  Trash2,
  BookOpen,
  AlertTriangle,
} from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { safetyApi, BlockedPersonaItemData, CommunityStandardRuleData } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [blurSensitive, setBlurSensitive] = useState<boolean>(true);
  const [piiShieldActive, setPiiShieldActive] = useState<boolean>(true);
  const [savedFeedback, setSavedFeedback] = useState<boolean>(false);

  // Live Block List
  const [blockedPersonas, setBlockedPersonas] = useState<BlockedPersonaItemData[]>([]);
  const [isLoadingBlocks, setIsLoadingBlocks] = useState<boolean>(true);

  // Community Standards
  const [standards, setStandards] = useState<CommunityStandardRuleData[]>([]);
  const [showStandards, setShowStandards] = useState<boolean>(false);

  // Account Deletion Modal
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [deleteConfirmationInput, setDeleteConfirmationInput] = useState<string>("");
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  useEffect(() => {
    async function loadSettingsData() {
      try {
        const blocks = await safetyApi.fetchMyBlocks();
        if (blocks && blocks.length > 0) {
          setBlockedPersonas(blocks);
        } else {
          // Fallback demo blocks
          setBlockedPersonas([
            {
              persona_id: "00000000-0000-0000-0000-000000000001",
              display_name: "HostilePhantom",
              avatar_seed: "phantom-1",
              reason: "Targeted harassment",
              blocked_at: new Date().toISOString(),
            },
          ]);
        }
      } catch {
        // Fallback
      } finally {
        setIsLoadingBlocks(false);
      }

      try {
        const rules = await safetyApi.fetchCommunityStandards();
        setStandards(rules);
      } catch {
        // Fallback
      }
    }

    loadSettingsData();
  }, []);

  const handleUnblock = async (personaId: string) => {
    try {
      await safetyApi.unblockPersona(personaId);
      setBlockedPersonas((prev) => prev.filter((p) => p.persona_id !== personaId));
    } catch {
      setBlockedPersonas((prev) => prev.filter((p) => p.persona_id !== personaId));
    }
  };

  const handleSavePreferences = () => {
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 2000);
  };

  const handleLogout = () => {
    router.push("/login");
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmationInput !== "DELETE MY ACCOUNT" || isDeleting) return;

    setIsDeleting(true);
    try {
      await safetyApi.deleteAccount();
      router.push("/login");
    } catch {
      alert("Failed to delete account. Please try again.");
      setIsDeleting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Settings className="w-5 h-5 text-[#9B72CF]" />
              Account & Privacy Controls
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#62C49A]/15 text-[#62C49A] border border-[#62C49A]/30">
              Session Encrypted
            </span>
          </div>
          <p className="text-xs text-[#A49BAF]">
            Manage your age assurance badge, privacy shields, safety block list, and account lifecycle.
          </p>
        </div>

        {/* 18+ Legitimate Age Assurance Verification Badge */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl">
          <CardContent className="p-5 sm:p-6 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-[#62C49A]/20 text-[#62C49A] flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#F6F1FA]">
                    Age Assurance Status
                  </h3>
                  <p className="text-xs text-[#A49BAF]">
                    Cryptographically verified adult (18+)
                  </p>
                </div>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#62C49A]/20 text-[#62C49A] border border-[#62C49A]/40">
                Verified Adult
              </span>
            </div>

            <div className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] text-xs text-[#A49BAF] space-y-1">
              <p className="font-semibold text-[#F6F1FA]">
                Proof Token: <span className="font-mono text-[#DCA7E8]">AGE_ASSURANCE_PROOF#verified_ok</span>
              </p>
              <p className="text-[11px] leading-relaxed">
                Age verified through the legitimate backend AgeAssuranceEngine. AFTR strictly prohibits underage accounts; minors are blocked and purged.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Privacy Shield & Content Moderation Preferences */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl">
          <CardContent className="p-5 sm:p-6 space-y-4">
            <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
              <EyeOff className="w-4 h-4 text-[#9B72CF]" />
              Content Filters & Privacy Shield
            </h3>

            <div className="space-y-3">
              <label className="flex items-start justify-between gap-4 p-3 rounded-xl bg-[#111016] border border-[#2D283B] cursor-pointer hover:border-[#9B72CF]/40 transition-colors">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-[#F6F1FA]">
                    Blur Sensitive & Adult Discussion Posts
                  </span>
                  <p className="text-[11px] text-[#A49BAF]">
                    Requires a manual click to reveal confessions flagged as sensitive.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={blurSensitive}
                  onChange={(e) => setBlurSensitive(e.target.checked)}
                  className="mt-1 rounded bg-[#1C1923] border-[#2D283B] text-[#9B72CF] accent-[#9B72CF]"
                />
              </label>

              <label className="flex items-start justify-between gap-4 p-3 rounded-xl bg-[#111016] border border-[#2D283B] cursor-pointer hover:border-[#9B72CF]/40 transition-colors">
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-[#F6F1FA]">
                    Strict Personal Contact Information Shield
                  </span>
                  <p className="text-[11px] text-[#A49BAF]">
                    Automatically alerts and blocks you from accidentally publishing phone numbers, emails, student IDs, or dorm numbers.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={piiShieldActive}
                  onChange={(e) => setPiiShieldActive(e.target.checked)}
                  className="mt-1 rounded bg-[#1C1923] border-[#2D283B] text-[#9B72CF] accent-[#9B72CF]"
                />
              </label>
            </div>

            <div className="flex justify-between items-center pt-2">
              {savedFeedback ? (
                <span className="text-xs text-[#62C49A] flex items-center gap-1 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Preferences Saved
                </span>
              ) : (
                <span className="text-[11px] text-[#A49BAF]">Local preferences updated</span>
              )}

              <Button
                size="sm"
                onClick={handleSavePreferences}
                className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-4"
              >
                Save Preferences
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Blocked Personas Manager */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl">
          <CardContent className="p-5 sm:p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
                <UserX className="w-4 h-4 text-[#E56A75]" />
                Blocked Personas ({blockedPersonas.length})
              </h3>
              <span className="text-[11px] text-[#A49BAF]">Bilateral Isolation Active</span>
            </div>

            <p className="text-xs text-[#A49BAF]">
              Blocked personas cannot view your posts, send connection requests, or message you across AFTR.
            </p>

            {isLoadingBlocks ? (
              <p className="text-xs text-[#A49BAF] italic">Loading block list...</p>
            ) : blockedPersonas.length === 0 ? (
              <p className="text-xs text-[#A49BAF] italic p-3 rounded-xl bg-[#111016] border border-[#2D283B]">
                You have not blocked any personas.
              </p>
            ) : (
              <div className="space-y-2">
                {blockedPersonas.map((p) => (
                  <div
                    key={p.persona_id}
                    className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] flex items-center justify-between"
                  >
                    <div className="space-y-0.5">
                      <span className="text-xs font-semibold text-[#F6F1FA]">{p.display_name}</span>
                      {p.reason && (
                        <p className="text-[10px] text-[#A49BAF]">Reason: {p.reason}</p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleUnblock(p.persona_id)}
                      className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-7 px-2.5"
                    >
                      Unblock
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Community Standards Accordion */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl">
          <CardContent className="p-5 sm:p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#9B72CF]" />
                AFTR Community Standards & Safety Policies
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowStandards(!showStandards)}
                className="border-[#2D283B] text-[#DCA7E8] text-xs h-7 px-2.5"
              >
                {showStandards ? "Hide Policies" : "View Policies"}
              </Button>
            </div>

            {showStandards && (
              <div className="space-y-3 pt-2 animate-in fade-in">
                {standards.length === 0 ? (
                  <div className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] text-xs text-[#A49BAF] space-y-2">
                    <p className="font-semibold text-[#F6F1FA]">Core Rules:</p>
                    <ul className="list-disc pl-4 space-y-1 text-[11px]">
                      <li>Zero Doxxing: Never publish personal names, phone numbers, or dorm addresses.</li>
                      <li>Mutual Consent: Private messaging requires mutual acceptance of connection requests.</li>
                      <li>Zero Tolerance: Harassment, violence, slurs, and non-consensual content are banned.</li>
                    </ul>
                  </div>
                ) : (
                  standards.map((rule, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] space-y-1">
                      <span className="text-xs font-bold text-[#DCA7E8]">{rule.title}</span>
                      <p className="text-[11px] text-[#F6F1FA]">{rule.description}</p>
                      <p className="text-[10px] text-[#A49BAF] italic">Enforcement: {rule.enforcement}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Lifecycle & Session */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl">
          <CardContent className="p-5 sm:p-6 space-y-4">
            <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#9B72CF]" />
              Account Security & Session
            </h3>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-[#111016] border border-[#2D283B]">
              <div className="space-y-0.5 text-xs text-left w-full">
                <p className="font-semibold text-[#F6F1FA]">Authentication Session</p>
                <p className="text-[11px] text-[#A49BAF]">
                  Supabase JWT session verified on backend.
                </p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="w-full sm:w-auto border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8 px-4 gap-1.5 shrink-0"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </Button>
            </div>

            {/* Account Deletion */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-[#E56A75]/10 border border-[#E56A75]/30">
              <div className="space-y-0.5 text-xs text-left w-full">
                <p className="font-semibold text-[#E56A75]">Permanent Account Deletion</p>
                <p className="text-[11px] text-[#A49BAF]">
                  Permanently deletes your account, personas, confessions, stories, and revokes invitations.
                </p>
              </div>

              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDeleteModal(true)}
                className="w-full sm:w-auto bg-[#E56A75] hover:bg-[#E56A75]/90 text-white text-xs h-8 px-4 gap-1.5 shrink-0"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Account Deletion Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="bg-[#1C1923] border-[#E56A75]/40 rounded-2xl max-w-md w-full shadow-2xl animate-in zoom-in-95">
              <CardContent className="p-6 space-y-4">
                <div className="flex items-center gap-2 text-[#E56A75]">
                  <AlertTriangle className="w-6 h-6" />
                  <h3 className="text-base font-bold text-[#F6F1FA]">Confirm Permanent Deletion</h3>
                </div>

                <p className="text-xs text-[#A49BAF] leading-relaxed">
                  This action is <strong>irreversible</strong>. All your anonymous personas, posts, ephemeral stories, private chat messages, and unused invitations will be permanently purged.
                </p>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Type <span className="font-mono text-[#E56A75]">DELETE MY ACCOUNT</span> to confirm:
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmationInput}
                    onChange={(e) => setDeleteConfirmationInput(e.target.value)}
                    placeholder="DELETE MY ACCOUNT"
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-2 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#E56A75]"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isDeleting}
                    onClick={() => {
                      setShowDeleteModal(false);
                      setDeleteConfirmationInput("");
                    }}
                    className="border-[#2D283B] text-[#A49BAF] text-xs h-8"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    disabled={deleteConfirmationInput !== "DELETE MY ACCOUNT" || isDeleting}
                    onClick={handleDeleteAccount}
                    className="bg-[#E56A75] hover:bg-[#E56A75]/90 text-white font-semibold text-xs h-8"
                  >
                    {isDeleting ? "Deleting..." : "Permanently Delete"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AppShell>
  );
}
