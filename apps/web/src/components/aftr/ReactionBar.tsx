"use client";

import React, { useState } from "react";
import { ArrowBigUp, Heart, Sparkles, Flame } from "lucide-react";

interface ReactionBarProps {
  initialUpvotes?: number;
  initialReactions?: {
    upvotes: number;
    flames: number;
    hearts: number;
    insightful: number;
  };
  userHasReacted?: boolean;
  onReact?: (type: "upvote" | "flame" | "heart" | "insightful") => void;
  className?: string;
}

export function ReactionBar({
  initialUpvotes = 0,
  initialReactions,
  userHasReacted = false,
  onReact,
  className = "",
}: ReactionBarProps) {
  const [upvotes, setUpvotes] = useState(
    initialReactions?.upvotes ?? initialUpvotes
  );
  const [flames, setFlames] = useState(initialReactions?.flames ?? 0);
  const [hearts, setHearts] = useState(initialReactions?.hearts ?? 0);
  const [insightful, setInsightful] = useState(initialReactions?.insightful ?? 0);

  const [activeReaction, setActiveReaction] = useState<string | null>(
    userHasReacted ? "upvote" : null
  );

  const toggleReaction = (type: "upvote" | "flame" | "heart" | "insightful") => {
    if (activeReaction === type) {
      setActiveReaction(null);
      if (type === "upvote") setUpvotes((v) => Math.max(0, v - 1));
      if (type === "flame") setFlames((v) => Math.max(0, v - 1));
      if (type === "heart") setHearts((v) => Math.max(0, v - 1));
      if (type === "insightful") setInsightful((v) => Math.max(0, v - 1));
    } else {
      if (activeReaction === "upvote") setUpvotes((v) => Math.max(0, v - 1));
      if (activeReaction === "flame") setFlames((v) => Math.max(0, v - 1));
      if (activeReaction === "heart") setHearts((v) => Math.max(0, v - 1));
      if (activeReaction === "insightful") setInsightful((v) => Math.max(0, v - 1));

      setActiveReaction(type);
      if (type === "upvote") setUpvotes((v) => v + 1);
      if (type === "flame") setFlames((v) => v + 1);
      if (type === "heart") setHearts((v) => v + 1);
      if (type === "insightful") setInsightful((v) => v + 1);
    }
    onReact?.(type);
  };

  return (
    <div className={`flex items-center gap-1.5 sm:gap-2 flex-wrap ${className}`}>
      {/* Upvote */}
      <button
        type="button"
        onClick={() => toggleReaction("upvote")}
        aria-pressed={activeReaction === "upvote"}
        aria-label="Upvote confession"
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all ${
          activeReaction === "upvote"
            ? "bg-[#9B72CF]/20 text-[#DCA7E8] border border-[#9B72CF]/50 shadow-sm"
            : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B]"
        }`}
      >
        <ArrowBigUp
          className={`w-4 h-4 transition-transform ${
            activeReaction === "upvote" ? "fill-[#DCA7E8] scale-110" : ""
          }`}
        />
        <span>{upvotes}</span>
      </button>

      {/* Flame / Spicy */}
      <button
        type="button"
        onClick={() => toggleReaction("flame")}
        aria-pressed={activeReaction === "flame"}
        aria-label="Spicy reaction"
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all ${
          activeReaction === "flame"
            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
            : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B]"
        }`}
      >
        <Flame
          className={`w-3.5 h-3.5 transition-transform ${
            activeReaction === "flame" ? "fill-amber-400 scale-110" : ""
          }`}
        />
        <span>{flames}</span>
      </button>

      {/* Relatable / Heart */}
      <button
        type="button"
        onClick={() => toggleReaction("heart")}
        aria-pressed={activeReaction === "heart"}
        aria-label="Relatable reaction"
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all ${
          activeReaction === "heart"
            ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
            : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B]"
        }`}
      >
        <Heart
          className={`w-3.5 h-3.5 transition-transform ${
            activeReaction === "heart" ? "fill-rose-400 scale-110" : ""
          }`}
        />
        <span>{hearts}</span>
      </button>

      {/* Insightful */}
      <button
        type="button"
        onClick={() => toggleReaction("insightful")}
        aria-pressed={activeReaction === "insightful"}
        aria-label="Insightful reaction"
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-all ${
          activeReaction === "insightful"
            ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40"
            : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B]"
        }`}
      >
        <Sparkles
          className={`w-3.5 h-3.5 transition-transform ${
            activeReaction === "insightful" ? "fill-indigo-300 scale-110" : ""
          }`}
        />
        <span>{insightful}</span>
      </button>
    </div>
  );
}
