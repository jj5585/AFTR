"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  Clock,
  Plus,
  Heart,
  MessageCircle,
  Trash2,
  Flag,
  Globe,
  School,
  AlertTriangle,
  Send,
  Lock,
} from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { ReportDialog } from "@/components/aftr/ReportDialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { storiesApi, LiveStoryItem } from "@/lib/api";
import { FIXTURE_STORIES, CURRENT_USER_PERSONA, FixtureStory } from "@/lib/fixtures";

const CATEGORIES = [
  { id: "all", label: "All Stories" },
  { id: "night-thoughts", label: "Late Night" },
  { id: "campus-life", label: "Campus Life" },
  { id: "confessions", label: "Confessions" },
  { id: "dating", label: "Dating & Vibes" },
  { id: "creative", label: "Creative" },
];

const GRADIENT_OPTIONS = [
  "from-purple-900/60 via-indigo-950/70 to-[#111016]",
  "from-pink-950/60 via-purple-950/70 to-[#111016]",
  "from-blue-950/60 via-slate-950/70 to-[#111016]",
  "from-emerald-950/60 via-teal-950/70 to-[#111016]",
  "from-amber-950/60 via-orange-950/70 to-[#111016]",
];

interface StoryCommentItem {
  id: string;
  story_id: string;
  persona: {
    id: string;
    display_name: string;
    avatar_seed: string;
    declared_campus?: string | null;
  };
  content: string;
  is_author?: boolean;
  created_at: string;
}

export default function StoriesPage() {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [activeCampus, setActiveCampus] = useState<string>("all");
  const [stories, setStories] = useState<LiveStoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Composer state
  const [showComposer, setShowComposer] = useState<boolean>(false);
  const [content, setContent] = useState<string>("");
  const [category, setCategory] = useState<string>("night-thoughts");
  const [visibility, setVisibility] = useState<"PUBLIC" | "CAMPUS">("PUBLIC");
  const [allowComments, setAllowComments] = useState<boolean>(true);
  const [selectedGradient, setSelectedGradient] = useState<string>(GRADIENT_OPTIONS[0]);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [isPosting, setIsPosting] = useState<boolean>(false);

  // Interactive comments state
  const [expandedStoryId, setExpandedStoryId] = useState<string | null>(null);
  const [storyComments, setStoryComments] = useState<Record<string, StoryCommentItem[]>>({});
  const [newCommentText, setNewCommentText] = useState<string>("");
  const [isSubmittingComment, setIsSubmittingComment] = useState<boolean>(false);

  // Report state
  const [reportingStoryId, setReportingStoryId] = useState<string | null>(null);

  const loadStories = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await storiesApi.fetchStories({
        category: activeCategory,
        campus: activeCampus,
      });

      if (res.items && res.items.length > 0) {
        setStories(res.items);
      } else {
        // Fallback to transformed fixture stories if no live items
        const transformed: LiveStoryItem[] = FIXTURE_STORIES.map((f: FixtureStory, idx: number) => ({
          id: f.id,
          persona: f.persona,
          content: f.content,
          category: idx % 2 === 0 ? "night-thoughts" : "campus-life",
          allow_comments: true,
          visibility: "PUBLIC",
          campus_name: null,
          reactions_count: 5 + idx * 3,
          user_has_reacted: false,
          comments_count: 2,
          is_own: idx === 0,
          expires_at: new Date(Date.now() + 86400000 * 0.8).toISOString(),
          created_at: f.created_at,
        }));
        setStories(transformed);
      }
    } catch {
      // Fallback gracefully
      const fallback: LiveStoryItem[] = FIXTURE_STORIES.map((f: FixtureStory, idx: number) => ({
        id: f.id,
        persona: f.persona,
        content: f.content,
        category: "night-thoughts",
        allow_comments: true,
        visibility: "PUBLIC",
        campus_name: null,
        reactions_count: 3,
        user_has_reacted: false,
        comments_count: 1,
        is_own: idx === 0,
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        created_at: f.created_at,
      }));
      setStories(fallback);
    } finally {
      setIsLoading(false);
    }
  }, [activeCategory, activeCampus]);

  useEffect(() => {
    loadStories();
  }, [loadStories]);

  const handleCreateStory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || isPosting) return;

    setIsPosting(true);
    setComposerError(null);

    try {
      const newStory = await storiesApi.createStory({
        content: content.trim(),
        category,
        allow_comments: allowComments,
        visibility,
        campus_name: visibility === "CAMPUS" ? "Bay Area Campus" : undefined,
      });

      setStories([newStory, ...stories]);
      setContent("");
      setShowComposer(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Story submission blocked by Privacy Shield.";
      setComposerError(msg);
    } finally {
      setIsPosting(false);
    }
  };

  const handleReaction = async (storyId: string) => {
    const target = stories.find((s) => s.id === storyId);
    if (!target) return;

    const nextHasReacted = !target.user_has_reacted;
    const nextCount = nextHasReacted
      ? target.reactions_count + 1
      : Math.max(0, target.reactions_count - 1);

    // Optimistic update
    setStories((prev) =>
      prev.map((s) =>
        s.id === storyId
          ? { ...s, user_has_reacted: nextHasReacted, reactions_count: nextCount }
          : s
      )
    );

    try {
      await storiesApi.reactToStory(storyId);
    } catch {
      // Revert if error
      setStories((prev) =>
        prev.map((s) =>
          s.id === storyId
            ? { ...s, user_has_reacted: target.user_has_reacted, reactions_count: target.reactions_count }
            : s
        )
      );
    }
  };

  const handleToggleComments = async (storyId: string) => {
    if (expandedStoryId === storyId) {
      setExpandedStoryId(null);
      return;
    }
    setExpandedStoryId(storyId);

    if (!storyComments[storyId]) {
      try {
        const comments = await storiesApi.fetchStoryComments(storyId);
        setStoryComments((prev) => ({
          ...prev,
          [storyId]: comments as StoryCommentItem[],
        }));
      } catch {
        // Fallback default
        setStoryComments((prev) => ({
          ...prev,
          [storyId]: [],
        }));
      }
    }
  };

  const handleAddComment = async (e: React.FormEvent, storyId: string) => {
    e.preventDefault();
    if (!newCommentText.trim() || isSubmittingComment) return;

    setIsSubmittingComment(true);
    try {
      const created = (await storiesApi.addStoryComment(
        storyId,
        newCommentText.trim()
      )) as StoryCommentItem;

      setStoryComments((prev) => ({
        ...prev,
        [storyId]: [...(prev[storyId] || []), created],
      }));

      setStories((prev) =>
        prev.map((s) =>
          s.id === storyId ? { ...s, comments_count: s.comments_count + 1 } : s
        )
      );
      setNewCommentText("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add comment";
      alert(msg);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleDeleteStory = async (storyId: string) => {
    if (!confirm("Are you sure you want to permanently delete this anonymous story?")) {
      return;
    }

    try {
      await storiesApi.deleteStory(storyId);
      setStories((prev) => prev.filter((s) => s.id !== storyId));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not delete story";
      alert(msg);
    }
  };

  const getHoursRemaining = (expiresAtStr: string) => {
    try {
      const diffMs = new Date(expiresAtStr).getTime() - Date.now();
      const hours = Math.round(diffMs / (1000 * 60 * 60));
      return Math.max(1, hours);
    } catch {
      return 24;
    }
  };

  const getGradientForCategory = (cat: string) => {
    switch (cat) {
      case "night-thoughts":
        return GRADIENT_OPTIONS[0];
      case "dating":
        return GRADIENT_OPTIONS[1];
      case "campus-life":
        return GRADIENT_OPTIONS[2];
      case "creative":
        return GRADIENT_OPTIONS[3];
      case "confessions":
        return GRADIENT_OPTIONS[4];
      default:
        return GRADIENT_OPTIONS[0];
    }
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#9B72CF]" />
              24-Hour Ephemeral Stories
            </h1>
            <p className="text-xs text-[#A49BAF]">
              Transient thoughts and moods that permanently self-destruct after 24 hours.
            </p>
          </div>

          <Button
            size="sm"
            onClick={() => {
              setShowComposer(!showComposer);
              setComposerError(null);
            }}
            className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-3 gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{showComposer ? "Close" : "Post Story"}</span>
          </Button>
        </div>

        {/* Ephemeral Guarantee Notice */}
        <div className="p-3 rounded-xl bg-[#1C1923] border border-[#2D283B] flex items-center gap-2.5 text-xs text-[#A49BAF]">
          <Clock className="w-4 h-4 text-[#9B72CF] shrink-0" />
          <span>
            <strong>Ephemeral Guarantee:</strong> Stories are not permanently archived. When the 24-hour countdown elapses, they vanish from all campus feeds.
          </span>
        </div>

        {/* Categories Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all shrink-0 ${
                activeCategory === cat.id
                  ? "bg-[#9B72CF] text-[#111016] shadow-sm font-semibold"
                  : "bg-[#1C1923] border border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] hover:border-[#9B72CF]/50"
              }`}
            >
              {cat.label}
            </button>
          ))}

          <div className="h-4 w-[1px] bg-[#2D283B] mx-1 shrink-0" />

          {/* Campus Toggle */}
          <button
            onClick={() => setActiveCampus(activeCampus === "all" ? "campus" : "all")}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all flex items-center gap-1 shrink-0 ${
              activeCampus !== "all"
                ? "bg-[#DCA7E8]/20 border border-[#DCA7E8]/50 text-[#DCA7E8]"
                : "bg-[#1C1923] border border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA]"
            }`}
          >
            <School className="w-3 h-3" />
            <span>{activeCampus === "all" ? "Campus: All" : "Campus: Local"}</span>
          </button>
        </div>

        {/* Story Composer */}
        {showComposer && (
          <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl animate-in fade-in duration-200">
            <CardContent className="p-4 sm:p-5 space-y-4">
              <form onSubmit={handleCreateStory} className="space-y-4">
                <div className="flex items-center justify-between">
                  <AnonymousPersona persona={CURRENT_USER_PERSONA} size="sm" showBio={false} />
                  <span className="text-[11px] font-mono text-[#DCA7E8] bg-[#9B72CF]/15 px-2.5 py-0.5 rounded-full border border-[#9B72CF]/30">
                    Expires in 24 Hours
                  </span>
                </div>

                {composerError && (
                  <div className="p-3 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/40 text-xs text-[#E56A75] flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{composerError}</span>
                  </div>
                )}

                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Share a momentary late-night thought, mood, spontaneous observation, or confession..."
                  rows={3}
                  maxLength={280}
                  className="w-full rounded-xl bg-[#111016] border border-[#2D283B] p-3 text-xs sm:text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF] resize-none"
                />

                {/* Category & Visibility controls */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="text-[11px] font-medium text-[#A49BAF] block mb-1">
                      Category
                    </label>
                    <select
                      value={category}
                      onChange={(e) => {
                        setCategory(e.target.value);
                        setSelectedGradient(getGradientForCategory(e.target.value));
                      }}
                      className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-2.5 py-1.5 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
                    >
                      <option value="night-thoughts">Late Night Thoughts</option>
                      <option value="campus-life">Campus Life</option>
                      <option value="confessions">Confessions</option>
                      <option value="dating">Dating & Vibes</option>
                      <option value="creative">Creative & Poetry</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-medium text-[#A49BAF] block mb-1">
                      Audience Visibility
                    </label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setVisibility("PUBLIC")}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-medium border ${
                          visibility === "PUBLIC"
                            ? "bg-[#9B72CF]/20 border-[#9B72CF] text-[#F6F1FA]"
                            : "bg-[#111016] border-[#2D283B] text-[#A49BAF]"
                        }`}
                      >
                        <Globe className="w-3 h-3 text-[#9B72CF]" />
                        <span>Public</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setVisibility("CAMPUS")}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-xs font-medium border ${
                          visibility === "CAMPUS"
                            ? "bg-[#9B72CF]/20 border-[#9B72CF] text-[#F6F1FA]"
                            : "bg-[#111016] border-[#2D283B] text-[#A49BAF]"
                        }`}
                      >
                        <School className="w-3 h-3 text-[#DCA7E8]" />
                        <span>My Campus</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Comment switch & Atmosphere */}
                <div className="flex items-center justify-between flex-wrap gap-3 pt-2 border-t border-[#2D283B]">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-[#A49BAF]">
                    <input
                      type="checkbox"
                      checked={allowComments}
                      onChange={(e) => setAllowComments(e.target.checked)}
                      className="accent-[#9B72CF] rounded"
                    />
                    <span>Allow anonymous comments</span>
                  </label>

                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-[#A49BAF]">Aura:</span>
                    <div className="flex gap-1">
                      {GRADIENT_OPTIONS.map((grad, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setSelectedGradient(grad)}
                          className={`w-5 h-5 rounded-full bg-gradient-to-tr ${grad} border ${
                            selectedGradient === grad
                              ? "border-white ring-1 ring-[#9B72CF]"
                              : "border-[#2D283B]"
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#2D283B]">
                  <span className="text-[11px] text-[#A49BAF]">
                    {content.length}/280 characters
                  </span>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setShowComposer(false)}
                      className="border-[#2D283B] text-[#A49BAF] text-xs h-8"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      disabled={!content.trim() || isPosting}
                      className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
                    >
                      {isPosting ? "Posting..." : "Publish Story (24h)"}
                    </Button>
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Stories List */}
        {isLoading ? (
          <div className="py-12 text-center text-xs text-[#A49BAF] space-y-2">
            <div className="w-6 h-6 border-2 border-[#9B72CF] border-t-transparent rounded-full animate-spin mx-auto" />
            <p>Gathering fresh campus stories...</p>
          </div>
        ) : stories.length === 0 ? (
          <div className="py-12 text-center text-xs text-[#A49BAF] border border-dashed border-[#2D283B] rounded-2xl p-6">
            <Sparkles className="w-8 h-8 text-[#9B72CF]/60 mx-auto mb-2" />
            <p className="text-sm font-semibold text-[#F6F1FA]">No active stories in this category</p>
            <p className="mt-1">Be the first to share an ephemeral late-night thought with your peers.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {stories.map((story) => {
              const hoursLeft = getHoursRemaining(story.expires_at);
              const cardGradient = getGradientForCategory(story.category);
              const isExpanded = expandedStoryId === story.id;
              const commentsList = storyComments[story.id] || [];

              return (
                <div
                  key={story.id}
                  className={`p-5 rounded-2xl bg-gradient-to-br ${cardGradient} border border-[#2D283B] space-y-3.5 relative overflow-hidden shadow-sm`}
                >
                  {/* Top Bar: Persona, Visibility, Expiration & Actions */}
                  <div className="flex items-center justify-between gap-2">
                    <AnonymousPersona persona={story.persona} size="sm" showBio={false} />

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[#111016]/80 text-[#A49BAF] border border-[#2D283B]">
                        {story.category.replace("-", " ")}
                      </span>

                      <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#111016]/80 border border-[#2D283B] text-[11px] text-[#DCA7E8]">
                        <Clock className="w-3 h-3 text-[#9B72CF]" />
                        <span>{hoursLeft}h left</span>
                      </div>

                      {/* Author delete control */}
                      {story.is_own && (
                        <button
                          type="button"
                          onClick={() => handleDeleteStory(story.id)}
                          title="Delete my story"
                          className="text-[#A49BAF]/60 hover:text-[#E56A75] transition-colors p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}

                      {/* Community safety report */}
                      <button
                        type="button"
                        onClick={() => setReportingStoryId(story.id)}
                        title="Report story"
                        className="text-[#A49BAF]/60 hover:text-[#E56A75] transition-colors p-1"
                      >
                        <Flag className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Story Text */}
                  <p className="text-sm sm:text-base font-medium text-[#F6F1FA] leading-relaxed">
                    &ldquo;{story.content}&rdquo;
                  </p>

                  {/* Story Bottom Actions Bar */}
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-[#2D283B]/60">
                    <div className="flex items-center gap-3">
                      {/* Reaction Upvote Button */}
                      <button
                        type="button"
                        onClick={() => handleReaction(story.id)}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs transition-colors ${
                          story.user_has_reacted
                            ? "bg-[#9B72CF]/25 text-[#DCA7E8] font-semibold border border-[#9B72CF]/40"
                            : "bg-[#111016]/60 text-[#A49BAF] hover:text-[#F6F1FA] border border-[#2D283B]"
                        }`}
                      >
                        <Heart
                          className={`w-3.5 h-3.5 ${
                            story.user_has_reacted ? "fill-[#DCA7E8] text-[#DCA7E8]" : ""
                          }`}
                        />
                        <span>{story.reactions_count}</span>
                      </button>

                      {/* Comments Toggle Button */}
                      {story.allow_comments ? (
                        <button
                          type="button"
                          onClick={() => handleToggleComments(story.id)}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs transition-colors ${
                            isExpanded
                              ? "bg-[#1C1923] text-[#F6F1FA] border border-[#9B72CF]/40"
                              : "bg-[#111016]/60 text-[#A49BAF] hover:text-[#F6F1FA] border border-[#2D283B]"
                          }`}
                        >
                          <MessageCircle className="w-3.5 h-3.5 text-[#9B72CF]" />
                          <span>{story.comments_count}</span>
                        </button>
                      ) : (
                        <span className="flex items-center gap-1 text-[11px] text-[#A49BAF]/60 italic">
                          <Lock className="w-3 h-3" />
                          Comments off
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 text-[11px] text-[#A49BAF]">
                      {story.visibility === "CAMPUS" ? (
                        <span className="flex items-center gap-1 text-[#DCA7E8]">
                          <School className="w-3 h-3" />
                          Campus only
                        </span>
                      ) : (
                        <span className="text-[#62C49A] font-medium">Ephemeral</span>
                      )}
                    </div>
                  </div>

                  {/* Expanded Comments Accordion */}
                  {isExpanded && story.allow_comments && (
                    <div className="pt-3 border-t border-[#2D283B]/80 space-y-3 animate-in fade-in duration-150">
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {commentsList.length === 0 ? (
                          <p className="text-xs text-[#A49BAF] italic py-1">
                            No anonymous comments yet. Start the conversation!
                          </p>
                        ) : (
                          commentsList.map((c) => (
                            <div
                              key={c.id}
                              className="p-2.5 rounded-xl bg-[#111016]/80 border border-[#2D283B] space-y-1"
                            >
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="font-semibold text-[#DCA7E8]">
                                  {c.persona.display_name}
                                  {c.is_author && (
                                    <span className="ml-1 text-[10px] text-[#9B72CF] font-normal">
                                      (Author)
                                    </span>
                                  )}
                                </span>
                              </div>
                              <p className="text-xs text-[#F6F1FA]">{c.content}</p>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Add Comment Input */}
                      <form
                        onSubmit={(e) => handleAddComment(e, story.id)}
                        className="flex items-center gap-2"
                      >
                        <input
                          type="text"
                          value={newCommentText}
                          onChange={(e) => setNewCommentText(e.target.value)}
                          placeholder="Reply anonymously to this story..."
                          maxLength={200}
                          className="flex-1 rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                        />
                        <Button
                          type="submit"
                          size="sm"
                          disabled={!newCommentText.trim() || isSubmittingComment}
                          className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-7 px-2.5 gap-1"
                        >
                          <Send className="w-3 h-3" />
                          <span>Reply</span>
                        </Button>
                      </form>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {reportingStoryId && (
        <ReportDialog
          isOpen={!!reportingStoryId}
          onClose={() => setReportingStoryId(null)}
          targetType="STORY"
          targetId={reportingStoryId}
        />
      )}
    </AppShell>
  );
}
