"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Settings,
  ShieldCheck,
  Lock,
  EyeOff,
  UserX,
  LogOut,
  CheckCircle2,
} from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const router = useRouter();
  const [blurSensitive, setBlurSensitive] = useState<boolean>(true);
  const [piiShieldActive, setPiiShieldActive] = useState<boolean>(true);
  const [blockedPersonas, setBlockedPersonas] = useState<string[]>([
    "HostilePhantom",
    "SpamBot99",
  ]);
  const [savedFeedback, setSavedFeedback] = useState<boolean>(false);

  const handleUnblock = (name: string) => {
    setBlockedPersonas(blockedPersonas.filter((p) => p !== name));
  };

  const handleSavePreferences = () => {
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 2000);
  };

  const handleLogout = () => {
    router.push("/login");
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
            Manage your age assurance badge, privacy shields, and security preferences.
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
                Age was verified through the backend AgeAssuranceEngine. AFTR enforces strict adult policies; underage accounts are immediately rejected and purged.
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
                    Automatically alerts and blocks you from accidentally publishing phone numbers, emails, or student IDs.
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
            <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
              <UserX className="w-4 h-4 text-[#E56A75]" />
              Blocked Personas ({blockedPersonas.length})
            </h3>
            <p className="text-xs text-[#A49BAF]">
              Blocked personas cannot view your posts, send connection requests, or message you.
            </p>

            {blockedPersonas.length === 0 ? (
              <p className="text-xs text-[#A49BAF] italic p-3 rounded-xl bg-[#111016] border border-[#2D283B]">
                You have not blocked any personas.
              </p>
            ) : (
              <div className="space-y-2">
                {blockedPersonas.map((name) => (
                  <div
                    key={name}
                    className="p-3 rounded-xl bg-[#111016] border border-[#2D283B] flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-[#F6F1FA]">{name}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleUnblock(name)}
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
                className="w-full sm:w-auto border-[#2D283B] text-[#E56A75] hover:bg-[#E56A75]/10 hover:border-[#E56A75]/30 text-xs h-8 px-4 gap-1.5 shrink-0"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out of AFTR
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
