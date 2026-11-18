"use client";

import React, { useState } from "react";
import { Calendar, MapPin, Users, Check, Plus, Star, Ban, Flag, AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AnonymousPersona } from "@/components/aftr/AnonymousPersona";
import { ReportDialog } from "@/components/aftr/ReportDialog";
import { LiveEventItem } from "@/lib/api";
import { FixtureEvent } from "@/lib/fixtures";

export interface EventCardProps {
  event: LiveEventItem | FixtureEvent;
  onRsvpChange?: (eventId: string, status: "GOING" | "INTERESTED" | "NONE") => Promise<void> | void;
  onCancelEvent?: (eventId: string) => Promise<void> | void;
  className?: string;
}

export function EventCard({
  event,
  onRsvpChange,
  onCancelEvent,
  className = "",
}: EventCardProps) {
  const isLive = "is_cancelled" in event;
  const isCancelled = isLive ? (event as LiveEventItem).is_cancelled : false;
  const isOrganizer = isLive ? (event as LiveEventItem).is_organizer : false;
  const maxAttendees = isLive ? (event as LiveEventItem).max_attendees : undefined;
  const initialRsvp = isLive
    ? ((event as LiveEventItem).user_rsvp_status as "GOING" | "INTERESTED" | null)
    : (event as FixtureEvent).is_attending
    ? "GOING"
    : null;

  const [rsvpStatus, setRsvpStatus] = useState<"GOING" | "INTERESTED" | null>(initialRsvp);
  const [attendeesCount, setAttendeesCount] = useState<number>(event.attendees_count);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isReporting, setIsReporting] = useState<boolean>(false);
  const [confirmCancel, setConfirmCancel] = useState<boolean>(false);

  const isFull = typeof maxAttendees === "number" && maxAttendees > 0 && attendeesCount >= maxAttendees;

  const handleRsvp = async (newStatus: "GOING" | "INTERESTED" | "NONE") => {
    if (isSubmitting || isCancelled) return;
    setIsSubmitting(true);
    try {
      const prev = rsvpStatus;
      if (newStatus === "NONE") {
        setRsvpStatus(null);
        if (prev === "GOING") {
          setAttendeesCount((c) => Math.max(0, c - 1));
        }
      } else if (newStatus === "GOING") {
        setRsvpStatus("GOING");
        if (prev !== "GOING") {
          setAttendeesCount((c) => c + 1);
        }
      } else if (newStatus === "INTERESTED") {
        setRsvpStatus("INTERESTED");
        if (prev === "GOING") {
          setAttendeesCount((c) => Math.max(0, c - 1));
        }
      }
      await onRsvpChange?.(event.id, newStatus);
    } catch {
      // Revert if error
      setRsvpStatus(initialRsvp);
      setAttendeesCount(event.attendees_count);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelClick = async () => {
    if (!confirmCancel) {
      setConfirmCancel(true);
      return;
    }
    setIsSubmitting(true);
    try {
      await onCancelEvent?.(event.id);
      setConfirmCancel(false);
    } finally {
      setIsSubmitting(false);
    }
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
    <>
      <Card
        className={`bg-[#1C1923] border-[#2D283B] rounded-2xl transition-all duration-200 hover:border-[#9B72CF]/40 ${
          isCancelled ? "opacity-75 border-[#E56A75]/30 bg-[#16141d]" : ""
        } ${className}`}
      >
        <CardContent className="p-4 sm:p-5 space-y-3.5">
          {/* Status & Campus Banner */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-[#9B72CF]/15 text-[#DCA7E8] border border-[#9B72CF]/30">
                {event.campus_name || "All Campuses"}
              </span>

              {isCancelled && (
                <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E56A75]/20 text-[#E56A75] border border-[#E56A75]/40 flex items-center gap-1">
                  <Ban className="w-3 h-3" />
                  CANCELLED BY ORGANIZER
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 text-xs text-[#A49BAF]">
                <Calendar className="w-3.5 h-3.5 text-[#9B72CF]" />
                <span>{formatEventDate(event.event_time)}</span>
              </div>

              <button
                type="button"
                onClick={() => setIsReporting(true)}
                title="Report gathering"
                className="text-[#A49BAF]/60 hover:text-[#E56A75] transition-colors p-1"
              >
                <Flag className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Organizer Info if live */}
          {"creator_persona" in event && event.creator_persona && (
            <div className="flex items-center gap-2 pt-0.5">
              <span className="text-[11px] text-[#A49BAF]">Hosted by:</span>
              <AnonymousPersona persona={event.creator_persona} size="sm" showBio={false} />
            </div>
          )}

          {/* Title & Description */}
          <div className="space-y-1">
            <h3
              className={`text-base font-bold leading-snug ${
                isCancelled ? "line-through text-[#A49BAF]" : "text-[#F6F1FA]"
              }`}
            >
              {event.title}
            </h3>
            <p className="text-xs text-[#A49BAF] leading-relaxed">
              {event.description}
            </p>
          </div>

          {/* Public Venue Landmark (Strictly No GPS / No Private Residence) */}
          <div className="flex items-center gap-2 text-xs text-[#A49BAF] p-2.5 rounded-xl bg-[#111016] border border-[#2D283B]">
            <MapPin className="w-3.5 h-3.5 text-[#9B72CF] shrink-0" />
            <span className="text-[#F6F1FA] font-medium truncate">
              {event.location_name}
            </span>
            <span className="text-[10px] text-[#62C49A] ml-auto shrink-0 bg-[#62C49A]/10 px-2 py-0.5 rounded border border-[#62C49A]/20">
              Public Venue • No GPS
            </span>
          </div>

          {/* Attendees, Capacity & RSVP Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-[#2D283B] flex-wrap gap-2">
            <div className="flex items-center gap-2 text-xs text-[#A49BAF]">
              <Users className="w-3.5 h-3.5 text-[#9B72CF]" />
              <span>
                <strong className="text-[#F6F1FA]">{attendeesCount}</strong>
                {maxAttendees ? ` / ${maxAttendees}` : ""} attending
              </span>

              {isFull && !isCancelled && rsvpStatus !== "GOING" && (
                <span className="text-[10px] text-[#E56A75] bg-[#E56A75]/15 px-2 py-0.5 rounded font-medium border border-[#E56A75]/30 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  At Capacity
                </span>
              )}
            </div>

            {/* RSVP / Organizer Controls */}
            <div className="flex items-center gap-2">
              {isCancelled ? (
                <span className="text-xs text-[#A49BAF] italic">
                  Gathering cancelled
                </span>
              ) : (
                <>
                  {/* Going Button */}
                  {rsvpStatus === "GOING" ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={isSubmitting}
                      onClick={() => handleRsvp("NONE")}
                      className="text-xs h-8 px-3 gap-1.5 font-semibold bg-[#62C49A]/20 text-[#62C49A] hover:bg-[#62C49A]/30 border border-[#62C49A]/40 transition-all"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Attending (Anonymous)</span>
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      size="sm"
                      disabled={isSubmitting || isFull}
                      onClick={() => handleRsvp("GOING")}
                      className="text-xs h-8 px-3 gap-1.5 font-semibold bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] transition-all disabled:opacity-50"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{isFull ? "Full" : "RSVP Going"}</span>
                    </Button>
                  )}

                  {/* Interested Button */}
                  {rsvpStatus === "INTERESTED" ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={isSubmitting}
                      onClick={() => handleRsvp("NONE")}
                      className="text-xs h-8 px-2.5 gap-1 font-semibold bg-[#DCA7E8]/20 text-[#DCA7E8] hover:bg-[#DCA7E8]/30 border border-[#DCA7E8]/40"
                    >
                      <Star className="w-3.5 h-3.5 fill-[#DCA7E8]" />
                      <span>Interested</span>
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={isSubmitting}
                      onClick={() => handleRsvp("INTERESTED")}
                      className="text-xs h-8 px-2.5 gap-1 border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA] hover:border-[#9B72CF]"
                    >
                      <Star className="w-3.5 h-3.5" />
                      <span>Interested</span>
                    </Button>
                  )}

                  {/* Organizer Cancellation Action */}
                  {isOrganizer && (
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      disabled={isSubmitting}
                      onClick={handleCancelClick}
                      className={`text-xs h-8 px-2.5 gap-1 bg-[#E56A75]/20 hover:bg-[#E56A75]/30 text-[#E56A75] border border-[#E56A75]/40 transition-all ${
                        confirmCancel ? "ring-2 ring-[#E56A75] font-bold" : ""
                      }`}
                    >
                      <Ban className="w-3.5 h-3.5" />
                      <span>{confirmCancel ? "Confirm Cancel?" : "Cancel Meetup"}</span>
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <ReportDialog
        isOpen={isReporting}
        onClose={() => setIsReporting(false)}
        targetType="EVENT"
        targetId={event.id}
        targetAuthor={"creator_persona" in event ? event.creator_persona?.display_name : undefined}
      />
    </>
  );
}
