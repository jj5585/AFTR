"use client";

import React, { useState } from "react";
import { Calendar, Plus, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/navigation/AppShell";
import { EventCard } from "@/components/aftr/EventCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FIXTURE_EVENTS, FixtureEvent } from "@/lib/fixtures";

export default function EventsPage() {
  const [events, setEvents] = useState<FixtureEvent[]>(FIXTURE_EVENTS);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [title, setTitle] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [locationName, setLocationName] = useState<string>("");
  const campusName = "Bay Area University";

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !locationName.trim()) return;

    const newEv: FixtureEvent = {
      id: `ev-${Date.now()}`,
      title: title.trim(),
      description: description.trim(),
      campus_name: campusName,
      location_name: locationName.trim(),
      event_time: new Date(Date.now() + 86400000 * 2).toISOString(),
      attendees_count: 1,
      is_attending: true,
    };

    setEvents([newEv, ...events]);
    setTitle("");
    setDescription("");
    setLocationName("");
    setShowCreateModal(false);
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
              Informal, open gatherings organized by pseudonymous adult campus peers.
            </p>
          </div>

          <Button
            size="sm"
            onClick={() => setShowCreateModal(!showCreateModal)}
            className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8 px-3 gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{showCreateModal ? "Cancel" : "Post Event"}</span>
          </Button>
        </div>

        {/* Location Privacy Rule */}
        <div className="p-3.5 rounded-2xl bg-[#1C1923] border border-[#2D283B] flex items-start gap-2.5 text-xs text-[#A49BAF]">
          <ShieldCheck className="w-4 h-4 text-[#62C49A] shrink-0 mt-0.5" />
          <span>
            <strong>Location Privacy Policy:</strong> Only public campus landmarks and general descriptions are permitted. GPS coordinates and live location sharing are strictly prohibited to prevent physical tracking.
          </span>
        </div>

        {/* Event Creation Form */}
        {showCreateModal && (
          <Card className="bg-[#1C1923] border-[#2D283B] rounded-2xl animate-in fade-in duration-200">
            <CardContent className="p-4 sm:p-5 space-y-3.5">
              <h3 className="text-sm font-bold text-[#F6F1FA]">
                Host a Campus Gathering
              </h3>

              <form onSubmit={handleCreateEvent} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Event Title
                  </label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Midnight Rooftop Astronomy & Lo-Fi"
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Venue Landmark (No GPS)
                  </label>
                  <input
                    type="text"
                    required
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    placeholder="e.g. Physics Observatory Open Deck / North Courtyard"
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] px-3 py-1.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-[#F6F1FA]">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What should people know? (e.g. bring a warm mug, chill ambient conversation)"
                    rows={2}
                    className="w-full rounded-lg bg-[#111016] border border-[#2D283B] p-2.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-1">
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
                    className="bg-[#9B72CF] hover:bg-[#9B72CF]/90 text-[#111016] font-semibold text-xs h-8"
                  >
                    Publish Gathering
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Events Grid */}
        <div className="space-y-4">
          {events.map((ev) => (
            <EventCard key={ev.id} event={ev} />
          ))}
        </div>
      </div>
    </AppShell>
  );
}
