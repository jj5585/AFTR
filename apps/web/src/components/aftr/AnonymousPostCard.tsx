"use client";

import React, { useState } from "react";
import Link from "next/link";
import { MessageSquare, MoreHorizontal, ShieldAlert, Flag, Eye, EyeOff } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { AnonymousPersona } from "./AnonymousPersona";
import { ReactionBar } from "./ReactionBar";
import { ReportDialog } from "./ReportDialog";
import { BlockDialog } from "./BlockDialog";
import { FixturePost } from "@/lib/fixtures";

interface AnonymousPostCardProps {
  post: FixturePost;
  onPostUpdated?: (post: FixturePost) => void;
  className?: string;
}

export function AnonymousPostCard({
  post,
  className = "",
}: AnonymousPostCardProps) {
  const [showSensitive, setShowSensitive] = useState<boolean>(!post.is_sensitive);
  const [showMenu, setShowMenu] = useState<boolean>(false);
  const [reportOpen, setReportOpen] = useState<boolean>(false);
  const [blockOpen, setBlockOpen] = useState<boolean>(false);

  const formatTimeAgo = (dateStr: string) => {
    try {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      if (diffMins < 60) return `${Math.max(1, diffMins)}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return "recently";
    }
  };

  const getTagBadgeColor = (tag: string) => {
    switch (tag) {
      case "secret-crushes":
        return "bg-pink-500/10 text-pink-300 border-pink-500/30";
      case "mental-health":
        return "bg-teal-500/10 text-teal-300 border-teal-500/30";
      case "unfiltered":
        return "bg-amber-500/10 text-amber-300 border-amber-500/30";
      case "campus-life":
        return "bg-purple-500/10 text-purple-300 border-purple-500/30";
      case "dating":
        return "bg-rose-500/10 text-rose-300 border-rose-500/30";
      default:
        return "bg-[#9B72CF]/10 text-[#DCA7E8] border-[#9B72CF]/30";
    }
  };

  return (
    <>
      <Card
        className={`bg-[#1C1923] border-[#2D283B] rounded-2xl transition-all duration-200 hover:border-[#9B72CF]/40 shadow-sm ${className}`}
      >
        <CardContent className="p-4 sm:p-5 space-y-3.5">
          {/* Header: Persona + Tag + Menu */}
          <div className="flex items-center justify-between gap-2">
            <AnonymousPersona persona={post.persona} size="md" />

            <div className="flex items-center gap-2">
              <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${getTagBadgeColor(post.tag)}`}>
                #{post.tag}
              </span>
              <span className="text-[11px] text-[#A49BAF]">
                {formatTimeAgo(post.created_at)}
              </span>

              {/* Overflow Menu */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowMenu(!showMenu)}
                  className="p-1 rounded-md text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] transition-colors"
                  aria-label="Post options"
                >
                  <MoreHorizontal className="w-4 h-4" />
                </button>

                {showMenu && (
                  <div className="absolute right-0 mt-1 w-36 bg-[#111016] border border-[#2D283B] rounded-xl shadow-xl z-20 py-1 text-xs">
                    <button
                      type="button"
                      onClick={() => {
                        setShowMenu(false);
                        setReportOpen(true);
                      }}
                      className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#A49BAF] hover:text-[#E56A75] hover:bg-[#1C1923]"
                    >
                      <Flag className="w-3.5 h-3.5" />
                      Report Post
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowMenu(false);
                        setBlockOpen(true);
                      }}
                      className="w-full text-left px-3 py-1.5 flex items-center gap-2 text-[#A49BAF] hover:text-[#E56A75] hover:bg-[#1C1923]"
                    >
                      <ShieldAlert className="w-3.5 h-3.5" />
                      Block Persona
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Content with sensitive blur support */}
          {post.is_sensitive && !showSensitive ? (
            <div className="relative rounded-xl p-6 bg-[#111016]/80 border border-[#2D283B] text-center space-y-2 backdrop-blur-md">
              <EyeOff className="w-6 h-6 text-[#A49BAF] mx-auto" />
              <p className="text-xs font-medium text-[#F6F1FA]">
                Sensitive / Adult Discussion Content
              </p>
              <p className="text-[11px] text-[#A49BAF]">
                This post was marked sensitive by the author.
              </p>
              <button
                type="button"
                onClick={() => setShowSensitive(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs rounded-full bg-[#9B72CF]/20 text-[#DCA7E8] hover:bg-[#9B72CF]/30 transition-colors"
              >
                <Eye className="w-3.5 h-3.5" />
                Reveal Confession
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <Link href={`/post/${post.id}`}>
                <p className="text-sm sm:text-base leading-relaxed text-[#F6F1FA] whitespace-pre-line hover:text-[#F6F1FA]/90 transition-colors cursor-pointer">
                  {post.content}
                </p>
              </Link>
              {post.is_sensitive && (
                <button
                  type="button"
                  onClick={() => setShowSensitive(false)}
                  className="text-[10px] text-[#A49BAF] hover:text-[#F6F1FA] underline block"
                >
                  Hide sensitive content again
                </button>
              )}
            </div>
          )}

          {/* Footer: Reactions + Comments Link */}
          <div className="pt-2 flex items-center justify-between border-t border-[#2D283B]/60 gap-2">
            <ReactionBar
              initialUpvotes={post.upvotes_count}
              initialReactions={post.reactions}
              userHasReacted={post.user_has_reacted}
            />

            <Link
              href={`/post/${post.id}`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B] transition-colors"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{post.comments_count}</span>
            </Link>
          </div>
        </CardContent>
      </Card>

      <ReportDialog
        isOpen={reportOpen}
        onClose={() => setReportOpen(false)}
        targetType="POST"
        targetId={post.id}
        targetAuthor={post.persona.display_name}
      />

      <BlockDialog
        isOpen={blockOpen}
        onClose={() => setBlockOpen(false)}
        personaDisplayName={post.persona.display_name}
        personaId={post.persona.id}
      />
    </>
  );
}
