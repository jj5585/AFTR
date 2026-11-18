"use client";

import React, { useState } from "react";
import { Send, CornerDownRight, MessageSquare, Flag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "./AnonymousPersona";
import { ReportDialog } from "./ReportDialog";
import { FixtureComment, CURRENT_USER_PERSONA } from "@/lib/fixtures";

interface CommentListProps {
  comments: FixtureComment[];
  opPersonaId?: string;
  onAddComment?: (content: string, parentId?: string) => void;
  className?: string;
}

export function CommentList({
  comments,
  opPersonaId,
  onAddComment,
  className = "",
}: CommentListProps) {
  const [newComment, setNewComment] = useState<string>("");
  const [replyingToId, setReplyingToId] = useState<string | null>(null);
  const [replyText, setReplyText] = useState<string>("");
  const [reportTargetId, setReportTargetId] = useState<string | null>(null);

  const handleTopLevelSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    onAddComment?.(newComment.trim());
    setNewComment("");
  };

  const handleReplySubmit = (parentId: string) => {
    if (!replyText.trim()) return;
    onAddComment?.(replyText.trim(), parentId);
    setReplyText("");
    setReplyingToId(null);
  };

  const formatTimeAgo = (dateStr: string) => {
    try {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      if (diffMins < 60) return `${Math.max(1, diffMins)}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      return `${diffHours}h ago`;
    } catch {
      return "just now";
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top level comment input */}
      <form onSubmit={handleTopLevelSubmit} className="space-y-2">
        <div className="flex items-start gap-2.5">
          <AnonymousPersona persona={CURRENT_USER_PERSONA} size="sm" showCampus={false} />
          <div className="flex-1 relative">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Reply anonymously to this confession..."
              rows={2}
              className="w-full rounded-xl bg-[#111016] border border-[#2D283B] p-3 text-xs sm:text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF] resize-none"
            />
            <div className="flex justify-between items-center mt-1 px-1">
              <span className="text-[10px] text-[#A49BAF]/70">
                Encrypted & pseudonymous
              </span>
              <Button
                type="submit"
                size="sm"
                disabled={!newComment.trim()}
                className="h-7 text-xs bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold gap-1"
              >
                <Send className="w-3 h-3" />
                Reply
              </Button>
            </div>
          </div>
        </div>
      </form>

      {/* Comment List */}
      {comments.length === 0 ? (
        <div className="text-center py-8 rounded-xl bg-[#111016]/40 border border-[#2D283B]/40 space-y-2">
          <MessageSquare className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
          <p className="text-xs font-medium text-[#F6F1FA]">No comments yet</p>
          <p className="text-[11px] text-[#A49BAF]">
            Break the silence. Share your perspective anonymously.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => {
            const isOp = comment.is_op || (opPersonaId && comment.persona.id === opPersonaId);
            return (
              <div
                key={comment.id}
                className="p-3.5 rounded-xl bg-[#111016]/80 border border-[#2D283B] space-y-2.5"
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AnonymousPersona persona={comment.persona} size="sm" showCampus={false} />
                    {isOp && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#9B72CF]/20 text-[#DCA7E8] border border-[#9B72CF]/40">
                        OP
                      </span>
                    )}
                    <span className="text-[11px] text-[#A49BAF]">
                      {formatTimeAgo(comment.created_at)}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setReportTargetId(comment.id)}
                    className="text-[#A49BAF]/60 hover:text-[#E56A75] transition-colors p-1"
                    title="Report comment"
                  >
                    <Flag className="w-3 h-3" />
                  </button>
                </div>

                {/* Comment Body */}
                <p className="text-xs sm:text-sm text-[#F6F1FA] pl-9">
                  {comment.content}
                </p>

                {/* Action: Reply */}
                <div className="pl-9">
                  <button
                    type="button"
                    onClick={() =>
                      setReplyingToId(replyingToId === comment.id ? null : comment.id)
                    }
                    className="text-[11px] text-[#A49BAF] hover:text-[#DCA7E8] inline-flex items-center gap-1 transition-colors"
                  >
                    <CornerDownRight className="w-3 h-3" />
                    {replyingToId === comment.id ? "Cancel" : "Reply"}
                  </button>
                </div>

                {/* Nested Reply Input */}
                {replyingToId === comment.id && (
                  <div className="pl-9 pt-2 space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder={`Reply to ${comment.persona.display_name}...`}
                        className="flex-1 rounded-lg bg-[#1C1923] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleReplySubmit(comment.id);
                        }}
                      />
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => handleReplySubmit(comment.id)}
                        disabled={!replyText.trim()}
                        className="h-8 text-xs bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold"
                      >
                        Reply
                      </Button>
                    </div>
                  </div>
                )}

                {/* Nested Replies List */}
                {comment.replies && comment.replies.length > 0 && (
                  <div className="pl-6 sm:pl-9 pt-2 space-y-2.5 border-l-2 border-[#2D283B] ml-3.5">
                    {comment.replies.map((reply) => {
                      const replyIsOp =
                        reply.is_op || (opPersonaId && reply.persona.id === opPersonaId);
                      return (
                        <div key={reply.id} className="space-y-1">
                          <div className="flex items-center gap-2">
                            <AnonymousPersona persona={reply.persona} size="sm" showCampus={false} />
                            {replyIsOp && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#9B72CF]/20 text-[#DCA7E8] border border-[#9B72CF]/40">
                                OP
                              </span>
                            )}
                            <span className="text-[10px] text-[#A49BAF]">
                              {formatTimeAgo(reply.created_at)}
                            </span>
                          </div>
                          <p className="text-xs text-[#F6F1FA] pl-9">
                            {reply.content}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {reportTargetId && (
        <ReportDialog
          isOpen={!!reportTargetId}
          onClose={() => setReportTargetId(null)}
          targetType="COMMENT"
          targetId={reportTargetId}
        />
      )}
    </div>
  );
}
