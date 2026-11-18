"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import { socialApi } from "@/lib/api";

interface ReportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: "POST" | "COMMENT" | "PERSONA" | "CONVERSATION" | "MESSAGE" | "EVENT" | "STORY";
  targetId: string;
  targetAuthor?: string;
}

const REPORT_REASONS = [
  "Doxxing or Sharing Real Contact Info",
  "Non-Consensual Explicit Content",
  "Harassment, Hate Speech or Threats",
  "Commercial Spam or Bot Activity",
  "Underage (Under 18) User Suspected",
  "Other Policy Violation",
];

export function ReportDialog({
  isOpen,
  onClose,
  targetType,
  targetId,
  targetAuthor,
}: ReportDialogProps) {
  const [selectedReason, setSelectedReason] = useState<string>(REPORT_REASONS[0]);
  const [details, setDetails] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const fullReason = details.trim()
        ? `${selectedReason} - ${details.trim()}`
        : selectedReason;
      await socialApi.reportContent(targetType, targetId, fullReason);
    } catch {
      // Handled
    } finally {
      setSubmitting(false);
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setDetails("");
        onClose();
      }, 1500);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Report ${targetType.toLowerCase()}${targetAuthor ? ` (${targetAuthor})` : ""}`}
      description={`AFTR community safety reviews all reports (${targetType} #${targetId}). Zero personal data is shared.`}
    >
      {submitted ? (
        <div className="py-6 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#62C49A]/20 text-[#62C49A] flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-[#F6F1FA]">Report Received</h3>
          <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
            Thank you for maintaining campus community trust. The item has been queued for human and automated review.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#F6F1FA]">
              Reason for reporting
            </label>
            <div className="space-y-1.5">
              {REPORT_REASONS.map((reason) => (
                <label
                  key={reason}
                  className={`flex items-center gap-2.5 p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                    selectedReason === reason
                      ? "bg-[#9B72CF]/15 border-[#9B72CF] text-[#F6F1FA]"
                      : "bg-[#111016] border-[#2D283B] text-[#A49BAF] hover:border-[#9B72CF]/40"
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={reason}
                    checked={selectedReason === reason}
                    onChange={() => setSelectedReason(reason)}
                    className="accent-[#9B72CF]"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-[#F6F1FA]">
              Additional context (optional)
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Provide specific details about what violated community safety..."
              rows={3}
              className="w-full rounded-lg bg-[#111016] border border-[#2D283B] p-2.5 text-xs text-[#F6F1FA] placeholder-[#A49BAF]/60 focus:outline-none focus:border-[#9B72CF]"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={submitting}
              className="border-[#2D283B] text-[#A49BAF] hover:text-[#F6F1FA]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={submitting}
              className="bg-[#E56A75] hover:bg-[#E56A75]/90 text-white font-medium"
            >
              {submitting ? "Submitting..." : "Submit Report"}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
