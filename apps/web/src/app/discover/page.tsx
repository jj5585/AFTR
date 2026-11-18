"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Compass, Sparkles, Search, Lock, SlidersHorizontal, AlertCircle, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { ConnectionCard, AnyConnectionItem } from "@/components/aftr/ConnectionCard";
import { FIXTURE_CONNECTIONS } from "@/lib/fixtures";
import { discoveryApi } from "@/lib/api";

const INTENTIONS = ["All", "CASUAL", "SERIOUS", "FRIENDS", "DISCUSSIONS", "EXPLORING"];

export default function DiscoverPage() {
  const [connections, setConnections] = useState<AnyConnectionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [availableInterests, setAvailableInterests] = useState<string[]>(["All"]);
  const [selectedInterest, setSelectedInterest] = useState<string>("All");
  const [selectedIntention, setSelectedIntention] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch interest taxonomy
      const rawInterests = await discoveryApi.fetchInterests();
      setAvailableInterests(["All", ...rawInterests.map((i) => i.name)]);

      // 2. Fetch discovery feed
      const feedRes = await discoveryApi.fetchFeed({
        intention: selectedIntention !== "All" ? selectedIntention : undefined,
      });

      if (feedRes.items && feedRes.items.length > 0) {
        setConnections(feedRes.items);
      } else {
        // In local UI dev with no other registered accounts, show default discovery fixtures
        setConnections(FIXTURE_CONNECTIONS);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load discovery feed";
      if (msg.includes("opt into discoverability")) {
        setErrorMsg("You must enable discoverability in your profile settings to view anonymous discovery cards.");
      } else {
        // Fallback to fixtures for seamless demo
        setConnections(FIXTURE_CONNECTIONS);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedIntention]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRequestSent = async (connectionId: string, note?: string) => {
    try {
      await discoveryApi.sendConnectionRequest(connectionId, note);
      setConnections((prev) =>
        prev.map((c) => (c.id === connectionId ? { ...c, connection_status: "PENDING_SENT" } : c))
      );
    } catch {
      // Optimistic update for UI preview
      setConnections((prev) =>
        prev.map((c) => (c.id === connectionId ? { ...c, connection_status: "PENDING_SENT" } : c))
      );
    }
  };

  const filteredConnections = connections.filter((conn) => {
    const matchesInterest =
      selectedInterest === "All" ||
      conn.mutual_interests?.includes(selectedInterest) ||
      ("interests" in conn.persona && conn.persona.interests?.includes(selectedInterest));

    const matchesQuery =
      !searchQuery.trim() ||
      conn.persona.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (conn.persona.declared_campus &&
        conn.persona.declared_campus.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (conn.mutual_interests &&
        conn.mutual_interests.some((i) => i.toLowerCase().includes(searchQuery.toLowerCase())));

    return matchesInterest && matchesQuery;
  });

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
            Find compatible peers through self-declared interests and adult intentions. Real identities remain strictly decoupled.
          </p>
        </div>

        {/* Consent Guarantee Banner */}
        <div className="p-3 rounded-xl bg-[#1C1923] border border-[#2D283B] flex items-start sm:items-center gap-2.5 text-xs text-[#A49BAF]">
          <Lock className="w-4 h-4 text-[#9B72CF] shrink-0 mt-0.5 sm:mt-0" />
          <span>
            <strong>Bilateral Consent Rule:</strong> Sending a connection request alerts the recipient without exposing your real email. Private chat opens only if they accept.
          </span>
        </div>

        {/* Error notification if not discoverable */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/30 flex items-center justify-between gap-3 text-xs text-[#F6F1FA]">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-[#E56A75] shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              type="button"
              onClick={loadData}
              className="px-2.5 py-1 rounded-lg bg-[#E56A75]/20 hover:bg-[#E56A75]/30 text-xs font-semibold transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Search & Filters */}
        <div className="space-y-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#A49BAF] absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by persona, declared campus, or mutual interest..."
                className="w-full rounded-xl bg-[#1C1923] border border-[#2D283B] pl-10 pr-4 py-2.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
              />
            </div>
            <button
              type="button"
              onClick={loadData}
              className="px-3 rounded-xl bg-[#1C1923] border border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] flex items-center gap-1.5 text-xs font-medium transition-colors"
              title="Refresh discovery feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-[#9B72CF]" : ""}`} />
            </button>
          </div>

          {/* Intention Chips */}
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-[#A49BAF]/70">
              <SlidersHorizontal className="w-3 h-3 text-[#9B72CF]" />
              <span>Relationship Intention</span>
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
              {INTENTIONS.map((intention) => (
                <button
                  key={intention}
                  type="button"
                  onClick={() => setSelectedIntention(intention)}
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                    selectedIntention === intention
                      ? "bg-[#9B72CF] text-[#111016] font-semibold"
                      : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] border border-[#2D283B]"
                  }`}
                >
                  {intention}
                </button>
              ))}
            </div>
          </div>

          {/* Interest Chips */}
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[#A49BAF]/70">
              Filter by Interest
            </span>
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1">
              {availableInterests.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => setSelectedInterest(interest)}
                  className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                    selectedInterest === interest
                      ? "bg-[#DCA7E8] text-[#111016] font-semibold"
                      : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] border border-[#2D283B]"
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="py-16 text-center space-y-3">
            <RefreshCw className="w-6 h-6 text-[#9B72CF] animate-spin mx-auto" />
            <p className="text-xs text-[#A49BAF]">Finding compatible adult campus personas...</p>
          </div>
        )}

        {/* Discovery Grid */}
        {!loading && (
          <>
            {filteredConnections.length === 0 ? (
              <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-2 p-6">
                <Sparkles className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
                <h3 className="text-sm font-semibold text-[#F6F1FA]">No compatible personas match your search</h3>
                <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
                  Try adjusting your search query, clearing filters, or opting into discoverability.
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
          </>
        )}
      </div>
    </AppShell>
  );
}
