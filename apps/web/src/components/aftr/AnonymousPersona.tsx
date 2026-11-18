"use client";

import React from "react";
import { EyeOff } from "lucide-react";

export interface PersonaDisplayData {
  id: string;
  display_name: string;
  avatar_seed: string;
  bio?: string;
  declared_campus?: string | null;
  interests?: string[];
  is_active?: boolean;
}

interface AnonymousPersonaProps {
  persona: PersonaDisplayData;
  size?: "sm" | "md" | "lg";
  showCampus?: boolean;
  showStatus?: boolean;
  showBio?: boolean;
  className?: string;
}

// Generate deterministic pleasing dark gradients based on avatar seed string
function getAvatarGradient(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const gradients = [
    "from-purple-900 to-indigo-950",
    "from-indigo-900 to-slate-900",
    "from-violet-800 to-purple-950",
    "from-fuchsia-900 to-indigo-950",
    "from-slate-800 to-purple-950",
    "from-purple-950 to-pink-950",
  ];
  const idx = Math.abs(hash) % gradients.length;
  return gradients[idx];
}

export function AnonymousPersona({
  persona,
  size = "md",
  showCampus = true,
  showStatus = true,
  className = "",
}: AnonymousPersonaProps) {
  const gradient = getAvatarGradient(persona.avatar_seed || persona.display_name);

  const sizeClasses = {
    sm: "w-7 h-7 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-14 h-14 text-base",
  };

  const nameSizeClasses = {
    sm: "text-xs font-semibold",
    md: "text-sm font-semibold",
    lg: "text-base font-bold",
  };

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Avatar Container */}
      <div className="relative">
        <div
          className={`${sizeClasses[size]} rounded-full bg-gradient-to-br ${gradient} border border-[#2D283B] flex items-center justify-center text-[#DCA7E8] font-bold shadow-inner select-none`}
          aria-label={`Anonymous persona ${persona.display_name}`}
        >
          {persona.display_name.slice(0, 2).toUpperCase()}
        </div>
        {showStatus && persona.is_active && (
          <span
            className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#62C49A] ring-2 ring-[#111016]"
            title="Active now"
          />
        )}
      </div>

      {/* Info Container */}
      <div className="flex flex-col">
        <div className="flex items-center gap-1.5">
          <span className={`text-[#F6F1FA] ${nameSizeClasses[size]}`}>
            {persona.display_name}
          </span>
          <span title="Pseudonymous Persona — zero real identity link">
            <EyeOff className="w-3 h-3 text-[#A49BAF]/70" />
          </span>
        </div>

        {showCampus && (
          <div className="flex items-center gap-1 text-[11px] text-[#A49BAF]">
            {persona.declared_campus ? (
              <span className="truncate max-w-[150px] sm:max-w-[200px]">
                {persona.declared_campus}
              </span>
            ) : (
              <span className="italic text-[#A49BAF]/60">Affiliation undeclared</span>
            )}
            <span className="text-[10px] text-[#A49BAF]/50">• self-declared</span>
          </div>
        )}
      </div>
    </div>
  );
}
