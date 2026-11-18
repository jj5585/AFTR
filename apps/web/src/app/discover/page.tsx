"use client";

import React, { useState } from "react";
import { Compass, Sparkles, Search, Lock } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { ConnectionCard } from "@/components/aftr/ConnectionCard";
import { FIXTURE_CONNECTIONS, FixtureConnection } from "@/lib/fixtures";

const ALL_INTERESTS = [
  "All",
  "Night Owl",
  "Philosophy",
  "Deep Conversations",
  "Psychology",
  "Lo-Fi",
  "Writing",
  "Synthesizers",
  "Art History",
];

export default function DiscoverPage() {
  const [connections, setConnections] = useState<FixtureConnection[]>(FIXTURE_CONNECTIONS);
  const [selectedInterest, setSelectedInterest] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const filteredConnections = connections.filter((conn) => {
    const matchesInterest =
      selectedInterest === "All" ||
      conn.mutual_interests.includes(selectedInterest) ||
      (conn.persona.interests && conn.persona.interests.includes(selectedInterest));

    const matchesQuery =
      !searchQuery.trim() ||
      conn.persona.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (conn.persona.declared_campus &&
        conn.persona.declared_campus.toLowerCase().includes(searchQuery.toLowerCase())) ||
      conn.mutual_interests.some((i) => i.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesInterest && matchesQuery;
  });

  const handleRequestSent = (connectionId: string) => {
    setConnections((prev) =>
      prev.map((c) => (c.id === connectionId ? { ...c, status: "PENDING" } : c))
    );
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Compass className="w-5 h-5 text-[#9B72CF]" />
              Anonymous Compatibility Discovery
            </h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30">
              Consent-Based Connections
            </span>
          </div>
          <p className="text-xs text-[#A49BAF]">
            Find compatible peers through self-declared interests and shared sensibilities. Real identities remain strictly decoupled.
          </p>
        </div>

        {/* Consent Guarantee Banner */}
        <div className="p-3 rounded-xl bg-[#1C1923] border border-[#2D283B] flex items-start sm:items-center gap-2.5 text-xs text-[#A49BAF]">
          <Lock className="w-4 h-4 text-[#9B72CF] shrink-0 mt-0.5 sm:mt-0" />
          <span>
            <strong>Bilateral Consent Rule:</strong> Sending a connection request alerts the recipient without exposing your real email. Private chat opens only if they accept.
          </span>
        </div>

        {/* Search & Filters */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 text-[#A49BAF] absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by persona, declared campus, or mutual interest..."
              className="w-full rounded-xl bg-[#1C1923] border border-[#2D283B] pl-10 pr-4 py-2.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
            />
          </div>

          {/* Interest Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
            {ALL_INTERESTS.map((interest) => (
              <button
                key={interest}
                type="button"
                onClick={() => setSelectedInterest(interest)}
                className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedInterest === interest
                    ? "bg-[#9B72CF] text-[#111016] font-semibold"
                    : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] border border-[#2D283B]"
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        {/* Discovery Grid */}
        {filteredConnections.length === 0 ? (
          <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-2 p-6">
            <Sparkles className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
            <h3 className="text-sm font-semibold text-[#F6F1FA]">No compatible personas match your search</h3>
            <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
              Try adjusting your search query or selecting a broader interest category.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredConnections.map((conn) => (
              <ConnectionCard
                key={conn.id}
                connection={conn}
                onRequestSent={handleRequestSent}
              />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
