"use client";

import React, { useState, useMemo } from "react";
import { ShieldAlert, Send, EyeOff, CheckCircle2, MessageSquare, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AnonymousPersona } from "./AnonymousPersona";
import { CATEGORIES, CURRENT_USER_PERSONA, FixturePost } from "@/lib/fixtures";
import { socialApi } from "@/lib/api";

interface PostComposerProps {
  onPostCreated?: (newPost: Partial<FixturePost>) => void;
  className?: string;
  defaultCategory?: string;
}

// Regex patterns to protect anonymous users against accidental doxxing
const PII_PATTERNS = [
  {
    regex: /[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/,
    name: "Email address",
  },
  {
    regex: /(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/,
    name: "Phone number",
  },
  {
    regex: /\b(?:student\s*id|roll\s*no|reg\s*no|id\s*#|matric\s*no)\s*[:#-]?\s*\w+/i,
    name: "Student / College ID number",
  },
  {
    regex: /@([a-zA-Z0-9_]{3,24})/,
    name: "Social media handle (@handle)",
  },
];

export function PostComposer({
  onPostCreated,
  className = "",
  defaultCategory = "secret-crushes",
}: PostComposerProps) {
  const [content, setContent] = useState<string>("");
  const [tag, setTag] = useState<string>(defaultCategory);
  const [postType, setPostType] = useState<"CONFESSION" | "DISCUSSION">("CONFESSION");
  const [isSensitive, setIsSensitive] = useState<boolean>(false);
  const [allowComments, setAllowComments] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [published, setPublished] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const MAX_CHARS = 1000;

  // Real-time PII detector
  const detectedPII = useMemo(() => {
    if (!content) return [];
    const detected: string[] = [];
    for (const pattern of PII_PATTERNS) {
      if (pattern.regex.test(content)) {
        detected.push(pattern.name);
      }
    }
    return detected;
  }, [content]);

  const hasPII = detectedPII.length > 0;
  const isOverLimit = content.length > MAX_CHARS;
  const canSubmit = content.trim().length >= 10 && !hasPII && !isOverLimit && !submitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      const created = await socialApi.createPost({
        content: content.trim(),
        tag: tag === "all" ? "campus-life" : tag,
        post_type: postType,
        is_sensitive: isSensitive,
        allow_comments: allowComments,
      });

      onPostCreated?.(created);
      setPublished(true);
      setContent("");
      setTimeout(() => setPublished(false), 2500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to publish post";
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl shadow-sm ${className}`}>
      <CardContent className="p-4 sm:p-5 space-y-4">
        {published ? (
          <div className="py-6 text-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-[#62C49A]/20 text-[#62C49A] flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-semibold text-[#F6F1FA]">Confession Published</h4>
            <p className="text-xs text-[#A49BAF]">
              Your confession is now live in the anonymous campus feed.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Header: Persona + Type Toggle */}
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <AnonymousPersona persona={CURRENT_USER_PERSONA} size="sm" />

              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#111016] border border-[#2D283B] text-xs">
                <button
                  type="button"
                  onClick={() => setPostType("CONFESSION")}
                  className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                    postType === "CONFESSION"
                      ? "bg-[#9B72CF] text-[#111016] font-semibold"
                      : "text-[#A49BAF] hover:text-[#F6F1FA]"
                  }`}
                >
                  Confession
                </button>
                <button
                  type="button"
                  onClick={() => setPostType("DISCUSSION")}
                  className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                    postType === "DISCUSSION"
                      ? "bg-[#9B72CF] text-[#111016] font-semibold"
                      : "text-[#A49BAF] hover:text-[#F6F1FA]"
                  }`}
                >
                  Discussion
                </button>
              </div>
            </div>

            {/* Content Input Area */}
            <div className="space-y-1.5">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What's your unfiltered anonymous confession or topic? (Minimum 10 characters)..."
                rows={4}
                className="w-full rounded-xl bg-[#111016] border border-[#2D283B] p-3 text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF] transition-colors resize-none"
              />

              <div className="flex justify-between items-center text-[11px] text-[#A49BAF] px-1">
                <span>
                  {content.length < 10 && content.length > 0 && (
                    <span className="text-amber-400">At least 10 characters required</span>
                  )}
                </span>
                <span className={isOverLimit ? "text-[#E56A75] font-bold" : ""}>
                  {content.length}/{MAX_CHARS}
                </span>
              </div>
            </div>

            {/* Real-time PII Alert Warning */}
            {hasPII && (
              <div className="p-3 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/40 flex items-start gap-2.5 text-xs">
                <ShieldAlert className="w-5 h-5 text-[#E56A75] shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-semibold text-[#E56A75]">
                    Privacy Shield Warning: Potential Personal Identifier Detected
                  </p>
                  <p className="text-[#F6F1FA]/80">
                    Detected: <strong className="text-white">{detectedPII.join(", ")}</strong>. AFTR strictly prohibits personal contact info, real names, or student identifiers to protect your identity. Please remove them to post.
                  </p>
                </div>
              </div>
            )}

            {/* Error Banner */}
            {errorMsg && (
              <div className="p-3 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/40 flex items-start gap-2.5 text-xs text-[#E56A75]">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Category and Sensitive Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-[#2D283B] flex-wrap">
              {/* Category Picker */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#A49BAF]">Tag:</span>
                <select
                  value={tag}
                  onChange={(e) => setTag(e.target.value)}
                  className="rounded-lg bg-[#111016] border border-[#2D283B] px-2.5 py-1 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
                >
                  {CATEGORIES.filter((c) => c.id !== "all").map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      #{cat.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sensitive Toggle */}
              <label className="flex items-center gap-1.5 cursor-pointer text-xs text-[#A49BAF] select-none hover:text-[#F6F1FA]">
                <input
                  type="checkbox"
                  checked={isSensitive}
                  onChange={(e) => setIsSensitive(e.target.checked)}
                  className="rounded bg-[#111016] border-[#2D283B] text-[#9B72CF] focus:ring-0 accent-[#9B72CF]"
                />
                <EyeOff className="w-3.5 h-3.5 text-[#DCA7E8]" />
                <span>Sensitive</span>
              </label>

              {/* Allow Comments Toggle (Product Rule: Users can disable comments) */}
              <label className="flex items-center gap-1.5 cursor-pointer text-xs text-[#A49BAF] select-none hover:text-[#F6F1FA]">
                <input
                  type="checkbox"
                  checked={allowComments}
                  onChange={(e) => setAllowComments(e.target.checked)}
                  className="rounded bg-[#111016] border-[#2D283B] text-[#9B72CF] focus:ring-0 accent-[#9B72CF]"
                />
                <MessageSquare className="w-3.5 h-3.5 text-[#9B72CF]" />
                <span>Allow comments</span>
              </label>

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={!canSubmit}
                className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-9 px-4 gap-1.5 self-end sm:self-auto"
              >
                <Send className="w-3.5 h-3.5" />
                {submitting ? "Publishing..." : "Post Anonymously"}
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
