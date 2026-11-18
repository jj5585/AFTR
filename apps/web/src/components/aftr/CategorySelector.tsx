"use client";

import React from "react";
import { CATEGORIES } from "@/lib/fixtures";

interface CategorySelectorProps {
  selectedCategory: string;
  onSelectCategory: (categoryId: string) => void;
  className?: string;
}

export function CategorySelector({
  selectedCategory,
  onSelectCategory,
  className = "",
}: CategorySelectorProps) {
  return (
    <div className={`w-full overflow-x-auto scrollbar-none py-1 ${className}`}>
      <div className="flex items-center gap-2 min-w-max pb-1">
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelectCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-150 ${
                isSelected
                  ? "bg-gradient-to-r from-[#9B72CF] to-[#DCA7E8] text-[#111016] font-semibold shadow-md shadow-[#9B72CF]/20 ring-1 ring-[#DCA7E8]"
                  : "bg-[#1C1923] text-[#A49BAF] hover:text-[#F6F1FA] hover:bg-[#2D283B] border border-[#2D283B]"
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
