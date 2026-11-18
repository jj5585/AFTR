"use client";

import React, { useState } from "react";
import { User, KeyRound, Tag, Edit3, Building2 } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { InvitationQuota } from "@/components/aftr/InvitationQuota";
import { InvitationCard } from "@/components/aftr/InvitationCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CURRENT_USER_PERSONA, FIXTURE_INVITATIONS, FixtureInvitation, FixturePersona } from "@/lib/fixtures";

export default function ProfilePage() {
  const [persona, setPersona] = useState<FixturePersona>(CURRENT_USER_PERSONA);
  const [invitations, setInvitations] = useState<FixtureInvitation[]>(FIXTURE_INVITATIONS);
  const [isEditingCampus, setIsEditingCampus] = useState<boolean>(false);
  const [campusInput, setCampusInput] = useState<string>(persona.declared_campus || "");
  const [bioInput, setBioInput] = useState<string>(persona.bio || "");
  const [isEditingBio, setIsEditingBio] = useState<boolean>(false);

  const handleSaveCampus = () => {
    setPersona({ ...persona, declared_campus: campusInput.trim() || undefined });
    setIsEditingCampus(false);
  };

  const handleSaveBio = () => {
    setPersona({ ...persona, bio: bioInput.trim() });
    setIsEditingBio(false);
  };

  const handleGenerateInvite = (targetEmail: string) => {
    const newInv: FixtureInvitation = {
      id: `inv-${Date.now()}`,
      token: `aftr-${Math.random().toString(36).substring(2, 6)}-${Math.random().toString(36).substring(2, 6)}`,
      bound_email_masked: `${targetEmail.slice(0, 2)}***@${targetEmail.split("@")[1]}`,
      status: "ACTIVE",
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
    };
    setInvitations([...invitations, newInv]);
  };

  const handleRevokeInvite = (invId: string) => {
    setInvitations((prev) =>
      prev.map((i) => (i.id === invId ? { ...i, status: "REVOKED" } : i))
    );
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <User className="w-5 h-5 text-[#9B72CF]" />
              Anonymous Identity & Quota
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#62C49A]/15 text-[#62C49A] border border-[#62C49A]/30">
              18+ Assured Member
            </span>
          </div>
          <p className="text-xs text-[#A49BAF]">
            Manage your pseudonymous persona, self-declared campus affiliation, and allocated invitations.
          </p>
        </div>

        {/* Persona Profile Card */}
        <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl shadow-sm">
          <CardContent className="p-5 sm:p-6 space-y-5">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <AnonymousPersona persona={persona} size="lg" />

              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono px-2 py-1 rounded-md bg-[#111016] border border-[#2D283B] text-[#A49BAF]">
                  Seed: {persona.avatar_seed}
                </span>
              </div>
            </div>

            {/* Bio Section */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[#111016] border border-[#2D283B]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#F6F1FA]">Anonymous Bio</span>
                <button
                  type="button"
                  onClick={() => setIsEditingBio(!isEditingBio)}
                  className="text-[11px] text-[#9B72CF] hover:text-[#DCA7E8] inline-flex items-center gap-1"
                >
                  <Edit3 className="w-3 h-3" />
                  {isEditingBio ? "Cancel" : "Edit Bio"}
                </button>
              </div>

              {isEditingBio ? (
                <div className="space-y-2">
                  <textarea
                    value={bioInput}
                    onChange={(e) => setBioInput(e.target.value)}
                    rows={2}
                    className="w-full rounded-lg bg-[#1C1923] border border-[#2D283B] p-2 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
                  />
                  <Button
                    size="sm"
                    onClick={handleSaveBio}
                    className="bg-[#9B72CF] text-[#111016] font-semibold text-xs h-7 px-3"
                  >
                    Save Bio
                  </Button>
                </div>
              ) : (
                <p className="text-xs text-[#A49BAF] leading-relaxed">
                  {persona.bio || "No bio set yet."}
                </p>
              )}
            </div>

            {/* Declared Campus Affiliation */}
            <div className="space-y-2 p-3.5 rounded-xl bg-[#111016] border border-[#2D283B]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-[#9B72CF]" />
                  <span className="text-xs font-semibold text-[#F6F1FA]">
                    Declared Campus Affiliation
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsEditingCampus(!isEditingCampus)}
                  className="text-[11px] text-[#9B72CF] hover:text-[#DCA7E8] inline-flex items-center gap-1"
                >
                  <Edit3 className="w-3 h-3" />
                  {isEditingCampus ? "Cancel" : "Change"}
                </button>
              </div>

              {isEditingCampus ? (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={campusInput}
                    onChange={(e) => setCampusInput(e.target.value)}
                    placeholder="e.g. Bay Area University or leave empty"
                    className="w-full rounded-lg bg-[#1C1923] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
                  />
                  <p className="text-[10px] text-[#A49BAF]">
                    Campus affiliation is 100% self-declared. We never demand .edu email or university verification.
                  </p>
                  <Button
                    size="sm"
                    onClick={handleSaveCampus}
                    className="bg-[#9B72CF] text-[#111016] font-semibold text-xs h-7 px-3"
                  >
                    Save Affiliation
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#F6F1FA] font-medium">
                    {persona.declared_campus || "Undeclared / Independent"}
                  </span>
                  <span className="text-[10px] text-[#A49BAF]">
                    Self-Declared (Zero Surveillance)
                  </span>
                </div>
              )}
            </div>

            {/* Interest Tags */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-[#F6F1FA] flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-[#9B72CF]" />
                Compatibility & Discussion Interests
              </span>
              <div className="flex flex-wrap gap-1.5">
                {persona.interests?.map((interest) => (
                  <span
                    key={interest}
                    className="text-xs px-2.5 py-1 rounded-lg bg-[#111016] text-[#DCA7E8] border border-[#2D283B]"
                  >
                    {interest}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Invitation Quota & Management Section */}
        <div className="space-y-4">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-[#F6F1FA] flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-[#9B72CF]" />
              Your Invitation Quota & Generated Tokens
            </h2>
            <p className="text-xs text-[#A49BAF]">
              Each member is issued exactly 3 single-use tokens valid for 72 hours.
            </p>
          </div>

          <InvitationQuota
            invitations={invitations}
            onGenerateInvite={handleGenerateInvite}
          />

          {/* List of User's Invitations */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#A49BAF]">
              Issued Invitations ({invitations.length})
            </h3>
            {invitations.map((inv) => (
              <InvitationCard
                key={inv.id}
                invitation={inv}
                onRevoke={handleRevokeInvite}
              />
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
