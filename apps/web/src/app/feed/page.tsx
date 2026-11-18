"use client";

import React, { useState, useEffect, useCallback } from "react";
import { PlusCircle, Flame, Clock, RefreshCw, Building2, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { CategorySelector } from "@/components/aftr/CategorySelector";
import { AnonymousPostCard } from "@/components/aftr/AnonymousPostCard";
import { SafetyNotice } from "@/components/aftr/SafetyNotice";
import { PostComposer } from "@/components/aftr/PostComposer";
import { Button } from "@/components/ui/button";
import { FIXTURE_POSTS, FixturePost } from "@/lib/fixtures";
import { socialApi } from "@/lib/api";

const CAMPUS_OPTIONS = [
  "All Campuses",
  "Bay Area University",
  "West Coast College",
  "Metro Campus",
  "Pacific Arts Institute",
];

export default function FeedPage() {
  const [posts, setPosts] = useState<FixturePost[]>(FIXTURE_POSTS);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedCampus, setSelectedCampus] = useState<string>("All Campuses");
  const [sortOrder, setSortOrder] = useState<"latest" | "trending">("latest");
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [showInlineComposer, setShowInlineComposer] = useState<boolean>(false);

  const loadFeed = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await socialApi.fetchFeed({
        category: selectedCategory === "all" ? undefined : selectedCategory,
        campus: selectedCampus === "All Campuses" ? undefined : selectedCampus,
        sort: sortOrder,
        limit: 15,
      });
      setPosts(res.items);
      setNextCursor(res.next_cursor || null);
      setHasMore(res.has_more);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory, selectedCampus, sortOrder]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const handleLoadMore = async () => {
    if (!nextCursor || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const res = await socialApi.fetchFeed({
        category: selectedCategory === "all" ? undefined : selectedCategory,
        campus: selectedCampus === "All Campuses" ? undefined : selectedCampus,
        sort: sortOrder,
        cursor: nextCursor,
        limit: 15,
      });
      setPosts((prev) => [...prev, ...res.items]);
      setNextCursor(res.next_cursor || null);
      setHasMore(res.has_more);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handlePostCreated = (newPost: Partial<FixturePost>) => {
    setPosts([newPost as FixturePost, ...posts]);
    setShowInlineComposer(false);
  };

  const handlePostDeleted = (deletedPostId: string) => {
    setPosts((prev) => prev.filter((p) => p.id !== deletedPostId));
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-5">
        {/* Safety Charter Banner */}
        <SafetyNotice />

        {/* Feed Header */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div>
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Flame className="w-5 h-5 text-[#9B72CF]" />
              Campus Confessions & Discussions
            </h1>
            <p className="text-xs text-[#A49BAF]">
              Unfiltered adult thoughts. Completely decoupled from real identities.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadFeed}
              disabled={isLoading}
              className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8 px-2.5"
              aria-label="Refresh feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
            <Button
              size="sm"
              onClick={() => setShowInlineComposer(!showInlineComposer)}
              className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-3 gap-1.5"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>{showInlineComposer ? "Close" : "Confess"}</span>
            </Button>
          </div>
        </div>

        {/* Inline Composer (Toggled) */}
        {showInlineComposer && (
          <div className="animate-in fade-in slide-in-from-top-2 duration-200">
            <PostComposer onPostCreated={handlePostCreated} />
          </div>
        )}

        {/* Filter Controls: Campus Affiliation & Sort Order */}
        <div className="flex items-center justify-between gap-3 flex-wrap p-2.5 rounded-xl bg-[#1C1923] border border-[#2D283B] text-xs">
          {/* Optional Campus Affiliation Filter */}
          <div className="flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
            <span className="text-[#A49BAF] text-[11px]">Campus:</span>
            <select
              value={selectedCampus}
              onChange={(e) => setSelectedCampus(e.target.value)}
              className="rounded-lg bg-[#111016] border border-[#2D283B] px-2 py-1 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
            >
              {CAMPUS_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Selector: Latest vs Trending */}
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-[#111016] border border-[#2D283B]">
            <button
              type="button"
              onClick={() => setSortOrder("latest")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                sortOrder === "latest"
                  ? "bg-[#9B72CF] text-[#111016] font-semibold"
                  : "text-[#A49BAF] hover:text-[#F6F1FA]"
              }`}
            >
              <Clock className="w-3 h-3" />
              Latest
            </button>
            <button
              type="button"
              onClick={() => setSortOrder("trending")}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                sortOrder === "trending"
                  ? "bg-[#9B72CF] text-[#111016] font-semibold"
                  : "text-[#A49BAF] hover:text-[#F6F1FA]"
              }`}
            >
              <TrendingUp className="w-3 h-3" />
              Trending
            </button>
          </div>
        </div>

        {/* Category Pills Bar */}
        <div className="sticky top-14 lg:top-0 z-20 bg-[#111016]/95 backdrop-blur py-2 -mx-1 px-1 border-b border-[#2D283B]/60">
          <CategorySelector
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        </div>

        {/* Posts Feed */}
        {isLoading && posts.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <RefreshCw className="w-6 h-6 text-[#9B72CF] animate-spin mx-auto" />
            <p className="text-xs text-[#A49BAF]">Decrypting anonymous confessions...</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 p-6">
            <Flame className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
            <h3 className="text-sm font-semibold text-[#F6F1FA]">No confessions in this feed</h3>
            <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
              Be the first to speak anonymously and break the campus ice.
            </p>
            <Button
              size="sm"
              onClick={() => setShowInlineComposer(true)}
              className="bg-[#9B72CF] text-[#111016] font-semibold text-xs h-8"
            >
              Share First Confession
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <AnonymousPostCard
                key={post.id}
                post={post}
                onPostUpdated={handlePostCreated}
                onPostDeleted={handlePostDeleted}
              />
            ))}

            {/* Keyset Cursor Pagination Trigger */}
            {hasMore && (
              <div className="pt-4 text-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  className="border-[#2D283B] text-[#DCA7E8] hover:text-[#F6F1FA] hover:bg-[#1C1923] text-xs h-9 px-6 rounded-xl"
                >
                  {isLoadingMore ? "Loading more confessions..." : "Load Older Confessions (Keyset Cursor)"}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
