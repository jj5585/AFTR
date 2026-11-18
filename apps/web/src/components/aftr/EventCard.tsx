"use client";

import React, { useState } from "react";
import { Calendar, MapPin, Users, Check, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FixtureEvent } from "@/lib/fixtures";

interface EventCardProps {
  event: FixtureEvent;
  onRsvpChange?: (eventId: string, attending: boolean) => void;
  className?: string;
}

export function EventCard({
  event,
  onRsvpChange,
  className = "",
}: EventCardProps) {
  const [isAttending, setIsAttending] = useState<boolean>(!!event.is_attending);
  const [attendeesCount, setAttendeesCount] = useState<number>(event.attendees_count);

  const toggleRsvp = () => {
    const nextState = !isAttending;
    setIsAttending(nextState);
    setAttendeesCount((c) => (nextState ? c + 1 : Math.max(0, c - 1)));
    onRsvpChange?.(event.id, nextState);
  };

  const formatEventDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className={`bg-[#1C1923] border-[#2D283B] rounded-2xl transition-all duration-200 hover:border-[#9B72CF]/40 ${className}`}>
      <CardContent className="p-4 sm:p-5 space-y-3.5">
        {/* Campus & Time */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30">
            {event.campus_name || "All Campuses"}
          </span>

          <div className="flex items-center gap-1.5 text-xs text-[#A49BAF]">
            <Calendar className="w-3.5 h-3.5 text-[#9B72CF]" />
            <span>{formatEventDate(event.event_time)}</span>
          </div>
        </div>

        {/* Title & Description */}
        <div className="space-y-1">
          <h3 className="text-base font-bold text-[#F6F1FA] leading-snug">
            {event.title}
          </h3>
          <p className="text-xs text-[#A49BAF] leading-relaxed">
            {event.description}
          </p>
        </div>

        {/* Venue (General Landmark - strictly no live GPS) */}
        <div className="flex items-center gap-2 text-xs text-[#A49BAF] p-2.5 rounded-xl bg-[#111016] border border-[#2D283B]">
          <MapPin className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
          <span className="text-[#F6F1FA] font-medium truncate">
            {event.location_name}
          </span>
          <span className="text-[10px] text-[#A49BAF]/60 ml-auto shrink-0">
            (No GPS / Landmark only)
          </span>
        </div>

        {/* Attendees & RSVP */}
        <div className="flex items-center justify-between pt-2 border-t border-[#2D283B]">
          <div className="flex items-center gap-1.5 text-xs text-[#A49BAF]">
            <Users className="w-3.5 h-3.5 text-[#9B72CF]" />
            <span>
              <strong className="text-[#F6F1FA]">{attendeesCount}</strong>
              {event.max_attendees ? ` / ${event.max_attendees}` : ""} attending
            </span>
          </div>

          <Button
            type="button"
            size="sm"
            onClick={toggleRsvp}
            className={`text-xs h-8 px-3.5 gap-1.5 font-semibold transition-all ${
              isAttending
                ? "bg-[#62C49A]/20 text-[#62C49A] hover:bg-[#62C49A]/30 border border-[#62C49A]/40"
                : "bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016]"
            }`}
          >
            {isAttending ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>Attending (Anonymous)</span>
              </>
            ) : (
              <>
                <Plus className="w-3.5 h-3.5" />
                <span>RSVP Anonymously</span>
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
