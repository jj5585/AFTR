"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, MessageSquare, Flag, ShieldAlert, MoreHorizontal, EyeOff, Eye } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { ReactionBar } from "@/components/aftr/ReactionBar";
import { CommentList } from "@/components/aftr/CommentList";
import { ReportDialog } from "@/components/aftr/ReportDialog";
import { BlockDialog } from "@/components/aftr/BlockDialog";
import { FIXTURE_POSTS, FIXTURE_COMMENTS, CURRENT_USER_PERSONA, FixtureComment } from "@/lib/fixtures";

export default function PostDetailPage() {
  const params = useParams();
  const postId = params.id as string;

  const post = FIXTURE_POSTS.find((p) => p.id === postId) || FIXTURE_POSTS[0];

  const [comments, setComments] = useState<FixtureComment[]>(
    FIXTURE_COMMENTS.filter((c) => c.post_id === post.id)
  );
  const [showSensitive, setShowSensitive] = useState<boolean>(!post.is_sensitive);
  const [reportOpen, setReportOpen] = useState<boolean>(false);
  const [blockOpen, setBlockOpen] = useState<boolean>(false);
  const [showMenu, setShowMenu] = useState<boolean>(false);

  const handleAddComment = (content: string, parentId?: string) => {
    if (parentId) {
      setComments((prev) =>
        prev.map((c) => {
          if (c.id === parentId) {
            const newReply: FixtureComment = {
              id: `c-rep-${Date.now()}`,
              post_id: post.id,
              persona: CURRENT_USER_PERSONA,
              content,
              created_at: new Date().toISOString(),
              is_op: false,
            };
            return {
              ...c,
              replies: [...(c.replies || []), newReply],
            };
          }
          return c;
        })
      );
    } else {
      const newComment: FixtureComment = {
        id: `c-${Date.now()}`,
        post_id: post.id,
        persona: CURRENT_USER_PERSONA,
        content,
        created_at: new Date().toISOString(),
        is_op: false,
        replies: [],
      };
      setComments((prev) => [newComment, ...prev]);
    }
  };

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

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Back Link */}
        <div className="flex items-center justify-between">
          <Link
            href="/feed"
            className="inline-flex items-center gap-1.5 text-xs text-[#A49BAF] hover:text-[#F6F1FA] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Feed</span>
          </Link>

          <span className="text-[11px] font-mono text-[#A49BAF]">
            ID: {post.id}
          </span>
        </div>

        {/* Post Card */}
        <div className="p-5 sm:p-6 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-4 shadow-sm">
          {/* Post Header */}
          <div className="flex items-center justify-between gap-2">
            <AnonymousPersona persona={post.persona} size="md" />

            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30 font-medium">
                #{post.tag}
              </span>
              <span className="text-xs text-[#A49BAF]">
                {formatTimeAgo(post.created_at)}
              </span>

              {/* Overflow Menu */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowMenu(!showMenu)}
                  className="p-1 rounded-md text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B]"
                  aria-label="Post actions"
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

          {/* Post Content */}
          {post.is_sensitive && !showSensitive ? (
            <div className="rounded-xl p-6 bg-[#111016] border border-[#2D283B] text-center space-y-2">
              <EyeOff className="w-6 h-6 text-[#A49BAF] mx-auto" />
              <p className="text-xs font-medium text-[#F6F1FA]">Sensitive Content Hidden</p>
              <button
                type="button"
                onClick={() => setShowSensitive(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1 text-xs rounded-full bg-[#9B72CF]/20 text-[#DCA7E8]"
              >
                <Eye className="w-3.5 h-3.5" />
                Reveal
              </button>
            </div>
          ) : (
            <p className="text-sm sm:text-base leading-relaxed text-[#F6F1FA] whitespace-pre-line">
              {post.content}
            </p>
          )}

          {/* Reactions */}
          <div className="pt-3 border-t border-[#2D283B] flex items-center justify-between">
            <ReactionBar
              initialUpvotes={post.upvotes_count}
              initialReactions={post.reactions}
              userHasReacted={post.user_has_reacted}
            />

            <div className="flex items-center gap-1.5 text-xs text-[#A49BAF]">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{comments.length} comments</span>
            </div>
          </div>
        </div>

        {/* Comment Thread */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-[#F6F1FA] uppercase tracking-wider flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-[#9B72CF]" />
            Anonymous Discussion ({comments.length})
          </h2>

          <CommentList
            comments={comments}
            opPersonaId={post.persona.id}
            onAddComment={handleAddComment}
          />
        </div>
      </div>

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
    </AppShell>
  );
}
