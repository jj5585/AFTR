"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  EyeOff,
  Shield,
  KeyRound,
  Lock,
  ArrowRight,
  Flame,
  MessageCircle,
  Users,
  CheckCircle2,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface HealthData {
  status: string;
  app: string;
  environment: string;
  timestamp_utc: string;
  services: {
    api: string;
    database: string;
    redis: string;
  };
}

export default function LandingPage() {
  const [health, setHealth] = useState<HealthData | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/health`);
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      // Keep health null on failure
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return (
    <div className="min-h-screen bg-[#111016] text-[#F6F1FA] flex flex-col selection:bg-[#9B72CF]/30 selection:text-[#DCA7E8]">
      {/* Top Header */}
      <header className="sticky top-0 z-50 w-full border-b border-[#2D283B] bg-[#111016]/90 backdrop-blur">
        <div className="container max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <EyeOff className="w-6 h-6 text-[#9B72CF]" />
            <span className="font-black text-2xl tracking-widest text-[#F6F1FA]">
              AFTR
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30 px-2.5 py-0.5 rounded-full">
              18+ Adult Network
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-xs font-semibold text-[#A49BAF] hover:text-[#F6F1FA] px-3 py-1.5 transition-colors"
            >
              Sign In
            </Link>
            <Link href="/invite">
              <Button
                size="sm"
                className="bg-gradient-to-r from-[#9B72CF] to-[#DCA7E8] text-[#111016] font-bold text-xs h-9 px-4 rounded-xl shadow-md shadow-[#9B72CF]/20"
              >
                Redeem Invite
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container max-w-5xl mx-auto px-4 py-16 sm:py-24 flex flex-col items-center text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1C1923] border border-[#2D283B] text-xs text-[#DCA7E8]">
          <KeyRound className="w-3.5 h-3.5 text-[#9B72CF]" />
          <span>Strictly Invitation-Only & 18+ Assured</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-[#F6F1FA] max-w-3xl leading-[1.1]">
          Meet without <span className="bg-gradient-to-r from-[#9B72CF] via-[#DCA7E8] to-[#9B72CF] bg-clip-text text-transparent">revealing</span>.
        </h1>

        <p className="text-[#A49BAF] text-base sm:text-lg max-w-2xl leading-relaxed">
          The private, anonymous social network for adult campus communities. Share unfiltered confessions, discover compatible minds, and connect through consent-based private chats.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2 w-full sm:w-auto">
          <Link href="/invite" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto h-12 px-8 bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-bold text-sm rounded-xl gap-2 shadow-lg shadow-[#9B72CF]/25">
              <span>Enter Invitation Code</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link href="/feed" className="w-full sm:w-auto">
            <Button
              variant="outline"
              className="w-full sm:w-auto h-12 px-8 border-[#2D283B] bg-[#1C1923] hover:bg-[#2D283B] text-[#F6F1FA] font-semibold text-sm rounded-xl gap-2"
            >
              <EyeOff className="w-4 h-4 text-[#DCA7E8]" />
              <span>Explore Public Feed</span>
            </Button>
          </Link>
        </div>

        {/* Trust Points */}
        <div className="pt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs text-[#A49BAF] max-w-3xl w-full border-t border-[#2D283B]/60">
          <div className="flex items-center justify-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-[#9B72CF]" />
            <span>Zero College Tracking</span>
          </div>
          <div className="flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#62C49A]" />
            <span>Cryptographic Proof 18+</span>
          </div>
          <div className="flex items-center justify-center gap-1.5">
            <KeyRound className="w-3.5 h-3.5 text-[#DCA7E8]" />
            <span>3 Single-Use Invites</span>
          </div>
          <div className="flex items-center justify-center gap-1.5">
            <EyeOff className="w-3.5 h-3.5 text-[#9B72CF]" />
            <span>Automated PII Shield</span>
          </div>
        </div>
      </section>

      {/* Feature Showcase Grid */}
      <section className="container max-w-6xl mx-auto px-4 py-12 space-y-12">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#F6F1FA]">
            Built For Honest Vulnerability
          </h2>
          <p className="text-xs sm:text-sm text-[#A49BAF]">
            Designed from the ground up to prevent performative social pressure.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Pillar 1 */}
          <div className="p-6 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 relative overflow-hidden group hover:border-[#9B72CF]/50 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-[#9B72CF]/20 text-[#DCA7E8] flex items-center justify-center">
              <Flame className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-[#F6F1FA]">
              Anonymous Confessions
            </h3>
            <p className="text-xs text-[#A49BAF] leading-relaxed">
              Publish secret crushes, mental health struggles, and unfiltered adult talks. Real-time privacy shields prevent accidental phone or roll number leaks.
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="p-6 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 relative overflow-hidden group hover:border-[#9B72CF]/50 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-[#62C49A]/20 text-[#62C49A] flex items-center justify-center">
              <MessageCircle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-[#F6F1FA]">
              Consent-Based Direct Chats
            </h3>
            <p className="text-xs text-[#A49BAF] leading-relaxed">
              No creepy unsolicited messages. Direct 1-on-1 chats remain permanently locked until both parties explicitly review compatibility and accept the request.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="p-6 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 relative overflow-hidden group hover:border-[#9B72CF]/50 transition-colors">
            <div className="w-10 h-10 rounded-xl bg-[#DCA7E8]/20 text-[#DCA7E8] flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-[#F6F1FA]">
              Campus Gatherings & Stories
            </h3>
            <p className="text-xs text-[#A49BAF] leading-relaxed">
              Discover spontaneous campus meetups with zero GPS surveillance. Share 24-hour ephemeral stories that self-destruct cleanly after expiry.
            </p>
          </div>
        </div>
      </section>

      {/* Backend Verification Bar (Footer) */}
      <footer className="mt-auto border-t border-[#2D283B] bg-[#111016] py-8">
        <div className="container max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#A49BAF]">
          <div className="flex items-center gap-2">
            <EyeOff className="w-4 h-4 text-[#9B72CF]" />
            <span>AFTR. Strictly 18+. Meets without revealing.</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-[#9B72CF]" />
              <span>Backend Status:</span>
              {health?.services.api === "healthy" ? (
                <span className="text-[#62C49A] font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Online
                </span>
              ) : (
                <span className="text-[#A49BAF]">Checking...</span>
              )}
            </div>
            <Link href="/admin" className="hover:text-[#F6F1FA] underline">
              Admin & Moderation
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
