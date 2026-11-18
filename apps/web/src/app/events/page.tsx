"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Calendar,
  Plus,
  ShieldCheck,
  MapPin,
  Users,
  AlertTriangle,
  School,
  Clock,
} from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { EventCard } from "@/components/aftr/EventCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { eventsApi, LiveEventItem } from "@/lib/api";
import { FIXTURE_EVENTS, FixtureEvent } from "@/lib/fixtures";

export default function EventsPage() {
  const [events, setEvents] = useState<LiveEventItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeCampus, setActiveCampus] = useState<string>("all");
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Form state
  const [title, setTitle] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [locationName, setLocationName] = useState<string>("");
  const [eventTime, setEventTime] = useState<string>("");
  const [maxAttendees, setMaxAttendees] = useState<string>("");
  const [campusName, setCampusName] = useState<string>("Bay Area University");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadEvents = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await eventsApi.fetchEvents({
        campus: activeCampus,
      });

      if (res.items && res.items.length > 0) {
        setEvents(res.items);
      } else {
        // Fallback transformed fixtures
        const transformed: LiveEventItem[] = FIXTURE_EVENTS.map((f: FixtureEvent, idx: number) => ({
          id: f.id,
          creator_persona: {
            id: `creator-${f.id}`,
            display_name: `Anonymous Organizer #${idx + 1}`,
            avatar_seed: `org-${idx}`,
            declared_campus: f.campus_name,
          },
          title: f.title,
          description: f.description,
          location_name: f.location_name,
          event_time: f.event_time,
          campus_name: f.campus_name,
          max_attendees: 20 + idx * 10,
          attendees_count: f.attendees_count,
          interested_count: 3 + idx,
          user_rsvp_status: f.is_attending ? "GOING" : null,
          is_cancelled: false,
          is_organizer: idx === 0,
          created_at: new Date().toISOString(),
        }));
        setEvents(transformed);
      }
    } catch {
      // Fallback
      const transformed: LiveEventItem[] = FIXTURE_EVENTS.map((f: FixtureEvent, idx: number) => ({
        id: f.id,
        creator_persona: {
          id: `creator-${f.id}`,
          display_name: `Anonymous Organizer #${idx + 1}`,
          avatar_seed: `org-${idx}`,
          declared_campus: f.campus_name,
        },
        title: f.title,
        description: f.description,
        location_name: f.location_name,
        event_time: f.event_time,
        campus_name: f.campus_name,
        max_attendees: 30,
        attendees_count: f.attendees_count,
        interested_count: 2,
        user_rsvp_status: f.is_attending ? "GOING" : null,
        is_cancelled: false,
        is_organizer: idx === 0,
        created_at: new Date().toISOString(),
      }));
      setEvents(transformed);
    } finally {
      setIsLoading(false);
    }
  }, [activeCampus]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // Set default event time to tomorrow at 8:00 PM
  useEffect(() => {
    const tomorrow = new Date(Date.now() + 86400000);
    tomorrow.setHours(20, 0, 0, 0);
    const localIso = tomorrow.toISOString().slice(0, 16);
    setEventTime(localIso);
  }, []);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !locationName.trim() || !description.trim() || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const parsedTime = new Date(eventTime);
      if (isNaN(parsedTime.getTime()) || parsedTime.getTime() <= Date.now()) {
        throw new Error("Event date and time must be set in the future.");
      }

      const parsedMax = maxAttendees.trim() ? parseInt(maxAttendees, 10) : undefined;
      if (parsedMax !== undefined && (isNaN(parsedMax) || parsedMax < 2 || parsedMax > 500)) {
        throw new Error("Max capacity must be between 2 and 500 attendees.");
      }

      const created = await eventsApi.createEvent({
        title: title.trim(),
        description: description.trim(),
        location_name: locationName.trim(),
        event_time: parsedTime.toISOString(),
        max_attendees: parsedMax,
        campus_name: campusName.trim() || undefined,
      });

      setEvents([created, ...events]);
      setTitle("");
      setDescription("");
      setLocationName("");
      setMaxAttendees("");
      setShowCreateModal(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to publish campus gathering.";
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRsvpChange = async (eventId: string, newStatus: "GOING" | "INTERESTED" | "NONE") => {
    try {
      if (newStatus === "NONE") {
        await eventsApi.withdrawRsvp(eventId);
      } else {
        await eventsApi.rsvpEvent(eventId, newStatus);
      }
      setEvents((prev) =>
        prev.map((ev) =>
          ev.id === eventId
            ? {
                ...ev,
                user_rsvp_status: newStatus === "NONE" ? null : newStatus,
              }
            : ev
        )
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not update RSVP";
      alert(msg);
    }
  };

  const handleCancelEvent = async (eventId: string) => {
    try {
      await eventsApi.cancelEvent(eventId);
      setEvents((prev) =>
        prev.map((ev) => (ev.id === eventId ? { ...ev, is_cancelled: true } : ev))
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not cancel gathering";
      alert(msg);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-xl font-black text-[#F6F1FA] flex items-center gap-2">
              <Calendar className="w-5 h-5 text-[#9B72CF]" />
              Public Campus Gatherings
            </h1>
            <p className="text-xs text-[#A49BAF]">
              Open, pseudonymous group meetups organized by verified adult campus peers.
            </p>
          </div>

          <Button
            size="sm"
            onClick={() => {
              setShowCreateModal(!showCreateModal);
              setFormError(null);
            }}
            className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-3 gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{showCreateModal ? "Close" : "Post Meetup"}</span>
          </Button>
        </div>

        {/* Location Privacy & Venue Policy */}
        <div className="p-3.5 rounded-2xl bg-[#1C1923] border border-[#2D283B] flex items-start gap-2.5 text-xs text-[#A49BAF]">
          <ShieldCheck className="w-4 h-4 text-[#62C49A] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-[#F6F1FA]">Venue Safety & Privacy Policy:</span>
            <p>
              Only named <strong>public campus landmarks and commercial venues</strong> are permitted. Live GPS coordinates and private residential addresses (dorm rooms, apartments, private houses) are strictly blocked by the AFTR Privacy Shield to prevent physical tracking and private doxxing.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveCampus("all")}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                activeCampus === "all"
                  ? "bg-[#9B72CF] text-[#111016] font-semibold"
                  : "bg-[#1C1923] border border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA]"
              }`}
            >
              All Gatherings
            </button>
            <button
              onClick={() => setActiveCampus("campus")}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all flex items-center gap-1 ${
                activeCampus !== "all"
                  ? "bg-[#DCA7E8]/20 border border-[#DCA7E8]/50 text-[#DCA7E8] font-semibold"
                  : "bg-[#1C1923] border border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA]"
              }`}
            >
              <School className="w-3 h-3" />
              <span>My Campus</span>
            </button>
          </div>

          <span className="text-[11px] text-[#A49BAF]">
            {events.length} active {events.length === 1 ? "gathering" : "gatherings"}
          </span>
        </div>

        {/* Event Creation Form */}
        {showCreateModal && (
          <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl animate-in fade-in duration-200">
            <CardContent className="p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-[#F6F1FA] flex items-center gap-2">
                  <Users className="w-4 h-4 text-[#9B72CF]" />
                  Host a Public Campus Gathering
                </h3>
                <span className="text-[10px] text-[#62C49A] bg-[#62C49A]/10 border border-[#62C49A]/20 px-2 py-0.5 rounded">
                  Public Venue Only
                </span>
              </div>

              {formError && (
                <div className="p-3 rounded-xl bg-[#E56A75]/15 border border-[#E56A75]/40 text-xs text-[#E56A75] flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{formError}</span>
                </div>
              )}

              <form onSubmit={handleCreateEvent} className="space-y-3.5">
                {/* Title */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Event Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Midnight Rooftop Astronomy & Lo-Fi Session"
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-2 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                  />
                </div>

                {/* Venue Landmark */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-[#F6F1FA] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#9B72CF]" />
                      Named Public Venue / Campus Landmark *
                    </label>
                    <span className="text-[10px] text-[#A49BAF]/70">
                      No coordinates or private addresses
                    </span>
                  </div>
                  <input
                    type="text"
                    required
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    placeholder="e.g. Physics Observatory Public Deck or The Old Oak Tavern Patio"
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-2 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                  />
                </div>

                {/* Description */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Description & Vibe *
                  </label>
                  <textarea
                    required
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What should people know? (e.g. dress warm, bring binoculars or cozy drinks, informal peer meetup)"
                    rows={2}
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] p-2.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF] resize-none"
                  />
                </div>

                {/* Date & Time, Capacity, Campus Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-[#F6F1FA] flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-[#9B72CF]" />
                      Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={eventTime}
                      onChange={(e) => setEventTime(e.target.value)}
                      className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-2.5 py-1.5 text-xs text-[#F6F1FA] focus:outline-none focus:border-[#9B72CF]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-[#F6F1FA]">
                      Max Capacity
                    </label>
                    <input
                      type="number"
                      min={2}
                      max={500}
                      value={maxAttendees}
                      onChange={(e) => setMaxAttendees(e.target.value)}
                      placeholder="Optional (e.g. 20)"
                      className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-2.5 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-[#F6F1FA]">
                      Campus Community
                    </label>
                    <input
                      type="text"
                      value={campusName}
                      onChange={(e) => setCampusName(e.target.value)}
                      placeholder="Campus name"
                      className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-2.5 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                    />
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="flex justify-end gap-2 pt-2 border-t border-[#2D283B]">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowCreateModal(false)}
                    className="border-[#2D283B] text-[#A49BAF] text-xs h-8"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isSubmitting}
                    className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
                  >
                    {isSubmitting ? "Publishing..." : "Publish Meetup"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Events Grid */}
        {isLoading ? (
          <div className="py-12 text-center text-xs text-[#A49BAF] space-y-2">
            <div className="w-6 h-6 border-2 border-[#9B72CF] border-t-transparent rounded-full animate-spin mx-auto" />
            <p>Loading upcoming gatherings...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="py-12 text-center text-xs text-[#A49BAF] border border-dashed border-[#2D283B] rounded-2xl p-6">
            <Calendar className="w-8 h-8 text-[#9B72CF]/60 mx-auto mb-2" />
            <p className="text-sm font-semibold text-[#F6F1FA]">No upcoming gatherings found</p>
            <p className="mt-1">Organize the first public meetup for your peers!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((ev) => (
              <EventCard
                key={ev.id}
                event={ev}
                onRsvpChange={handleRsvpChange}
                onCancelEvent={handleCancelEvent}
              />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
