"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { PlusCircle, ShieldCheck, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { AppShell } from "@/components/navigation/AppShell";
import { PostComposer } from "@/components/aftr/PostComposer";

export default function CreatePostPage() {
  const router = useRouter();

  const handlePostCreated = () => {
    // Navigate back to feed after posting
    setTimeout(() => {
      router.push("/feed");
    }, 1200);
  };

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Navigation Back */}
        <div className="flex items-center gap-2">
          <Link
            href="/feed"
            className="inline-flex items-center gap-1.5 text-xs text-[#A49BAF] hover:text-[#F6F1FA] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Feed</span>
          </Link>
        </div>

        {/* Page Title */}
        <div className="space-y-1">
          <h1 className="text-xl sm:text-2xl font-black text-[#F6F1FA] flex items-center gap-2">
            <PlusCircle className="w-6 h-6 text-[#9B72CF]" />
            Compose Anonymous Confession
          </h1>
          <p className="text-xs text-[#A49BAF]">
            Share your honest thoughts, crushes, or adult questions. Real identity is isolated by design.
          </p>
        </div>

        {/* The Full Post Composer */}
        <PostComposer onPostCreated={handlePostCreated} />

        {/* Community Guidelines Card */}
        <div className="p-4 rounded-2xl bg-[#1C1923] border border-[#2D283B] space-y-3 text-xs text-[#A49BAF]">
          <h3 className="font-bold text-[#F6F1FA] flex items-center gap-1.5 text-xs">
            <ShieldCheck className="w-4 h-4 text-[#62C49A]" />
            Publishing Guardrails & Anonymity Rules
          </h3>
          <ul className="list-disc list-inside space-y-1 pl-1">
            <li>Never include phone numbers, email addresses, or social media handles.</li>
            <li>Do not name individuals by their real names or student ID numbers.</li>
            <li>Adult discussions must be marked sensitive to allow community members to opt in.</li>
            <li>Zero tolerance for harassment, doxxing, non-consensual content, or threats.</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
