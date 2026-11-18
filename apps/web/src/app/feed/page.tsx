"use client";

import React, { useState } from "react";
import { PlusCircle, Flame, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { CategorySelector } from "@/components/aftr/CategorySelector";
import { AnonymousPostCard } from "@/components/aftr/AnonymousPostCard";
import { SafetyNotice } from "@/components/aftr/SafetyNotice";
import { PostComposer } from "@/components/aftr/PostComposer";
import { Button } from "@/components/ui/button";
import { FIXTURE_POSTS, FixturePost } from "@/lib/fixtures";

export default function FeedPage() {
  const [posts, setPosts] = useState<FixturePost[]>(FIXTURE_POSTS);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [showInlineComposer, setShowInlineComposer] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const filteredPosts = posts.filter((post) => {
    if (selectedCategory === "all") return true;
    return post.tag === selectedCategory;
  });

  const handlePostCreated = (newPost: Partial<FixturePost>) => {
    setPosts([newPost as FixturePost, ...posts]);
    setShowInlineComposer(false);
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 500);
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-5">
        {/* Safety Charter Banner */}
        <SafetyNotice />

        {/* Feed Header */}
        <div className="flex items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Flame className="w-5 h-5 text-[#9B72CF]" />
              Campus Confessions & Discussions
            </h1>
            <p className="text-xs text-[#A49BAF]">
              Real adult campus thoughts. Protected by pseudonymous isolation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] text-xs h-8 px-2.5"
              aria-label="Refresh feed"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
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

        {/* Category Pills Bar */}
        <div className="sticky top-14 lg:top-0 z-20 bg-[#111016]/95 backdrop-blur py-2 -mx-1 px-1 border-b border-[#2D283B]/60">
          <CategorySelector
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
          />
        </div>

        {/* Posts Feed */}
        {filteredPosts.length === 0 ? (
          <div className="py-16 text-center rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 p-6">
            <Flame className="w-8 h-8 text-[#A49BAF]/40 mx-auto" />
            <h3 className="text-sm font-semibold text-[#F6F1FA]">No confessions in this category yet</h3>
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
            {filteredPosts.map((post) => (
              <AnonymousPostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
