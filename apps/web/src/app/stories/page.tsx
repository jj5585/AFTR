"use client";

import React, { useState } from "react";
import { Sparkles, Clock, Plus } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FIXTURE_STORIES, CURRENT_USER_PERSONA, FixtureStory } from "@/lib/fixtures";

const GRADIENT_OPTIONS = [
  "from-purple-900/50 via-indigo-950/60 to-background",
  "from-pink-950/50 via-purple-950/60 to-background",
  "from-blue-950/50 via-slate-950/60 to-background",
  "from-emerald-950/50 via-teal-950/60 to-background",
  "from-amber-950/50 via-orange-950/60 to-background",
];

export default function StoriesPage() {
  const [stories, setStories] = useState<FixtureStory[]>(FIXTURE_STORIES);
  const [showComposer, setShowComposer] = useState<boolean>(false);
  const [content, setContent] = useState<string>("");
  const [selectedGradient, setSelectedGradient] = useState<string>(GRADIENT_OPTIONS[0]);

  const handlePostStory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    const newStory: FixtureStory = {
      id: `story-${Date.now()}`,
      persona: CURRENT_USER_PERSONA,
      content: content.trim(),
      gradient_theme: selectedGradient,
      expires_in_hours: 24,
      created_at: new Date().toISOString(),
    };

    setStories([newStory, ...stories]);
    setContent("");
    setShowComposer(false);
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
            onClick={() => setShowComposer(!showComposer)}
            className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-3 gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{showComposer ? "Cancel" : "New Story"}</span>
          </Button>
        </div>

        {/* Ephemeral Notice */}
        <div className="p-3 rounded-xl bg-[#1C1923] border border-[#2D283B] flex items-center gap-2 text-xs text-[#A49BAF]">
          <Clock className="w-4 h-4 text-[#9B72CF] shrink-0" />
          <span>
            <strong>Ephemeral Guarantee:</strong> Stories are not indexed or permanently saved. When the 24-hour timer elapses, they vanish completely.
          </span>
        </div>

        {/* Story Composer */}
        {showComposer && (
          <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl animate-in fade-in duration-200">
            <CardContent className="p-4 sm:p-5 space-y-4">
              <form onSubmit={handlePostStory} className="space-y-4">
                <div className="flex items-center justify-between">
                  <AnonymousPersona persona={CURRENT_USER_PERSONA} size="sm" />
                  <span className="text-[11px] font-mono text-[#DCA7E8]">
                    Expires in 24 Hours
                  </span>
                </div>

                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Share a momentary late-night thought, mood, or spontaneous observation..."
                  rows={3}
                  maxLength={280}
                  className="w-full rounded-xl bg-[#111016] border border-[#2D283B] p-3 text-xs sm:text-sm text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF] resize-none"
                />

                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-[#A49BAF]">Atmosphere:</span>
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

                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-[#A49BAF]">
                      {content.length}/280
                    </span>
                    <Button
                      type="submit"
                      disabled={!content.trim()}
                      className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
                    >
                      Post Story (24h)
                    </Button>
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Stories List */}
        <div className="space-y-4">
          {stories.map((story) => (
            <div
              key={story.id}
              className={`p-5 rounded-2xl bg-gradient-to-br ${story.gradient_theme} border border-[#2D283B] space-y-4 relative overflow-hidden shadow-sm`}
            >
              <div className="flex items-center justify-between gap-2">
                <AnonymousPersona persona={story.persona} size="sm" />

                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#111016]/70 border border-[#2D283B] text-[10px] text-[#DCA7E8]">
                  <Clock className="w-3 h-3 text-[#9B72CF]" />
                  <span>{story.expires_in_hours}h left</span>
                </div>
              </div>

              <p className="text-sm sm:text-base font-medium text-[#F6F1FA] leading-relaxed">
                &ldquo;{story.content}&rdquo;
              </p>

              <div className="flex items-center justify-between text-[11px] text-[#A49BAF] pt-2 border-t border-[#2D283B]/40">
                <span className="italic">Self-destructs on expiry</span>
                <span className="text-[#62C49A]">Ephemeral</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
