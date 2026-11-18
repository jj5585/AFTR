"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Flame,
  Compass,
  PlusCircle,
  Sparkles,
  Calendar,
  MessageCircle,
  User,
  Settings,
  ShieldAlert,
  EyeOff,
  KeyRound,
  Menu,
  X,
  Lock,
} from "lucide-react";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { CURRENT_USER_PERSONA, FIXTURE_EVENTS, FIXTURE_INVITATIONS } from "@/lib/fixtures";

interface AppShellProps {
  children: React.ReactNode;
  showRightPanel?: boolean;
}

const NAV_ITEMS = [
  { href: "/feed", label: "Feed", icon: Flame },
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/create", label: "Create", icon: PlusCircle, highlight: true },
  { href: "/stories", label: "Stories", icon: Sparkles },
  { href: "/events", label: "Events", icon: Calendar },
  { href: "/chats", label: "Chats", icon: MessageCircle, badge: 1 },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: ShieldAlert },
];

const MOBILE_BOTTOM_NAV = [
  { href: "/feed", label: "Feed", icon: Flame },
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/create", label: "Post", icon: PlusCircle, isCreate: true },
  { href: "/stories", label: "Stories", icon: Sparkles },
  { href: "/chats", label: "Chats", icon: MessageCircle, badge: 1 },
  { href: "/profile", label: "Profile", icon: User },
];

export function AppShell({ children, showRightPanel = true }: AppShellProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const activeInvitations = FIXTURE_INVITATIONS.filter((i) => i.status === "ACTIVE").length;

  return (
    <div className="min-h-screen bg-[#111016] text-[#F6F1FA] flex flex-col">
      {/* Mobile Top Header */}
      <header className="lg:hidden sticky top-0 z-40 w-full h-14 border-b border-[#2D283B] bg-[#111016]/95 backdrop-blur px-4 flex items-center justify-between">
        <Link href="/feed" className="flex items-center gap-2">
          <EyeOff className="w-5 h-5 text-[#9B72CF]" />
          <span className="font-extrabold text-lg tracking-widest text-[#F6F1FA]">AFTR</span>
          <span className="text-[10px] font-semibold uppercase tracking-wider bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30 px-2 py-0.5 rounded-full">
            18+
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <Link
            href="/profile"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#1C1923] border border-[#2D283B] text-[11px] text-[#A49BAF]"
          >
            <KeyRound className="w-3 h-3 text-[#9B72CF]" />
            <span>{activeInvitations}/3 Invites</span>
          </Link>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded-lg text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#1C1923]"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Slide-down Full Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-x-0 top-14 bottom-16 z-30 bg-[#111016] border-b border-[#2D283B] p-4 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-1">
            <div className="p-3 mb-3 rounded-xl bg-[#1C1923] border border-[#2D283B]">
              <AnonymousPersona persona={CURRENT_USER_PERSONA} size="md" />
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[#9B72CF] text-[#111016] font-semibold"
                      : "text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#1C1923]"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="w-5 h-5 rounded-full bg-[#E56A75] text-white text-[10px] flex items-center justify-center font-bold">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          <div className="pt-4 border-t border-[#2D283B] text-xs text-[#A49BAF] space-y-2">
            <div className="flex items-center justify-between">
              <span>AFTR Protocol</span>
              <span className="text-[#62C49A]">18+ Verified</span>
            </div>
            <p className="text-[11px] text-[#A49BAF]/70">
              Meet without revealing. Campus affiliation self-declared.
            </p>
          </div>
        </div>
      )}

      {/* Main Framework Grid */}
      <div className="flex-1 container max-w-7xl mx-auto px-0 sm:px-4 flex gap-6">
        {/* DESKTOP LEFT SIDEBAR */}
        <aside className="hidden lg:flex flex-col w-64 shrink-0 py-6 sticky top-0 h-screen justify-between border-r border-[#2D283B]/40 pr-4">
          <div className="space-y-6">
            {/* Logo */}
            <div className="space-y-1 px-3">
              <Link href="/feed" className="flex items-center gap-2">
                <EyeOff className="w-6 h-6 text-[#9B72CF]" />
                <span className="font-black text-2xl tracking-widest text-[#F6F1FA]">
                  AFTR
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30 px-2 py-0.5 rounded-full">
                  18+
                </span>
              </Link>
              <p className="text-[11px] text-[#A49BAF] tracking-tight">
                Meet without revealing.
              </p>
            </div>

            {/* Navigation Links */}
            <nav className="space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? "bg-[#9B72CF] text-[#111016] font-semibold shadow-md shadow-[#9B72CF]/20"
                        : "text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#1C1923]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="w-5 h-5 rounded-full bg-[#E56A75] text-white text-[10px] flex items-center justify-center font-bold">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer: Quota Card + Current Persona */}
          <div className="space-y-3 pt-4 border-t border-[#2D283B]">
            {/* Invitation Quota Mini Card */}
            <Link
              href="/profile"
              className="block p-3 rounded-xl bg-[#1C1923] border border-[#2D283B] hover:border-[#9B72CF]/40 transition-colors"
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-[#F6F1FA] flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5 text-[#9B72CF]" />
                  Invitations
                </span>
                <span className="text-[11px] text-[#DCA7E8] font-mono">
                  {activeInvitations}/3 Left
                </span>
              </div>
              <p className="text-[10px] text-[#A49BAF]">
                Single-use 72h codes. Bound to recipient.
              </p>
            </Link>

            {/* User Persona */}
            <div className="p-2.5 rounded-xl bg-[#1C1923]/60 border border-[#2D283B]/60">
              <AnonymousPersona persona={CURRENT_USER_PERSONA} size="sm" />
            </div>
          </div>
        </aside>

        {/* CENTER MAIN FEED AREA */}
        <main className="flex-1 py-4 sm:py-6 px-3 sm:px-4 min-w-0 pb-20 lg:pb-6">
          {children}
        </main>

        {/* DESKTOP RIGHT DISCOVERY PANEL */}
        {showRightPanel && (
          <aside className="hidden xl:flex flex-col w-80 shrink-0 py-6 sticky top-0 h-screen overflow-y-auto space-y-5 border-l border-[#2D283B]/40 pl-5">
            {/* Trending Campus Topics */}
            <div className="p-4 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3">
              <h4 className="text-xs font-bold text-[#F6F1FA] uppercase tracking-wider flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-[#9B72CF]" />
                Trending Confessions
              </h4>
              <div className="space-y-2 text-xs">
                <Link
                  href="/feed?category=secret-crushes"
                  className="block p-2 rounded-lg bg-[#111016] border border-[#2D283B] hover:border-[#9B72CF]/40 transition-colors"
                >
                  <p className="font-semibold text-[#F6F1FA]">#secret-crushes</p>
                  <p className="text-[10px] text-[#A49BAF]">54 new unfiltered posts today</p>
                </Link>
                <Link
                  href="/feed?category=mental-health"
                  className="block p-2 rounded-lg bg-[#111016] border border-[#2D283B] hover:border-[#9B72CF]/40 transition-colors"
                >
                  <p className="font-semibold text-[#F6F1FA]">#mental-health</p>
                  <p className="text-[10px] text-[#A49BAF]">89 confessions on midterm burnout</p>
                </Link>
                <Link
                  href="/feed?category=unfiltered"
                  className="block p-2 rounded-lg bg-[#111016] border border-[#2D283B] hover:border-[#9B72CF]/40 transition-colors"
                >
                  <p className="font-semibold text-[#F6F1FA]">#unfiltered</p>
                  <p className="text-[10px] text-[#A49BAF]">Adult discussion & intimacy</p>
                </Link>
              </div>
            </div>

            {/* Upcoming Gatherings */}
            <div className="p-4 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-[#F6F1FA] uppercase tracking-wider flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-[#9B72CF]" />
                  Campus Gatherings
                </h4>
                <Link href="/events" className="text-[10px] text-[#DCA7E8] hover:underline">
                  View All
                </Link>
              </div>
              <div className="space-y-2">
                {FIXTURE_EVENTS.slice(0, 2).map((ev) => (
                  <div key={ev.id} className="p-2.5 rounded-xl bg-[#111016] border border-[#2D283B] space-y-1">
                    <p className="text-xs font-semibold text-[#F6F1FA] line-clamp-1">{ev.title}</p>
                    <p className="text-[10px] text-[#A49BAF]">{ev.location_name}</p>
                    <p className="text-[10px] text-[#62C49A]">{ev.attendees_count} attending anonymously</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Privacy Shield Pillar Note */}
            <div className="p-3.5 rounded-2xl bg-[#9B72CF]/10 border border-[#9B72CF]/30 space-y-1.5 text-xs text-[#A49BAF]">
              <p className="font-semibold text-[#F6F1FA] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#9B72CF]" />
                Zero Surveillance Guarantee
              </p>
              <p className="text-[11px] leading-relaxed">
                AFTR never verifies or requires university credentials. Affiliation is completely self-declared and adult status is verified cryptographically.
              </p>
            </div>
          </aside>
        )}
      </div>

      {/* MOBILE BOTTOM NAVIGATION BAR */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 h-16 bg-[#111016]/95 backdrop-blur border-t border-[#2D283B] px-2 flex items-center justify-around">
        {MOBILE_BOTTOM_NAV.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          if (item.isCreate) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className="w-11 h-11 rounded-full bg-gradient-to-tr from-[#9B72CF] to-[#DCA7E8] text-[#111016] flex items-center justify-center shadow-lg shadow-[#9B72CF]/30 -mt-5 ring-4 ring-[#111016]"
                aria-label="Create Post"
              >
                <PlusCircle className="w-6 h-6" />
              </Link>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center w-12 py-1 relative text-[10px] transition-colors ${
                isActive ? "text-[#DCA7E8] font-bold" : "text-[#A49BAF] hover:text-[#F6F1FA]"
              }`}
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span>{item.label}</span>
              {item.badge && (
                <span className="absolute top-1 right-2 w-2 h-2 rounded-full bg-[#E56A75]" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
