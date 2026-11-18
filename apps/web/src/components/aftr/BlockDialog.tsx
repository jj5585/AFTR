"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ShieldAlert, CheckCircle2 } from "lucide-react";
import { socialApi } from "@/lib/api";

interface BlockDialogProps {
  isOpen: boolean;
  onClose: () => void;
  personaDisplayName: string;
  personaId: string;
  onBlocked?: (personaId: string) => void;
}

export function BlockDialog({
  isOpen,
  onClose,
  personaDisplayName,
  personaId,
  onBlocked,
}: BlockDialogProps) {
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [blocked, setBlocked] = useState<boolean>(false);

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      await socialApi.blockPersona(personaId);
      onBlocked?.(personaId);
    } catch {
      // Handled
    } finally {
      setSubmitting(false);
      setBlocked(true);
      setTimeout(() => {
        setBlocked(false);
        onClose();
      }, 1400);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Block ${personaDisplayName}?`}
    >
      {blocked ? (
        <div className="py-6 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#E56A75]/20 text-[#E56A75] flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-[#F6F1FA]">Persona Blocked</h3>
          <p className="text-xs text-[#A49BAF] max-w-xs mx-auto">
            {personaDisplayName} has been blocked. Their content is now invisible to you and they cannot contact you.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3 rounded-lg bg-[#E56A75]/10 border border-[#E56A75]/30 text-xs text-[#F6F1FA]">
            <ShieldAlert className="w-5 h-5 text-[#E56A75] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold text-[#E56A75]">What happens when you block:</p>
              <ul className="list-disc list-inside space-y-1 text-[#A49BAF]">
                <li>You will no longer see confessions, posts, or stories from {personaDisplayName}.</li>
                <li>They will be unable to send connection requests or chat messages.</li>
                <li>They will NOT be notified that you blocked them.</li>
              </ul>
            </div>
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
              type="button"
              size="sm"
              onClick={handleConfirm}
              disabled={submitting}
              className="bg-[#E56A75] hover:bg-[#E56A75]/90 text-white font-medium"
            >
              {submitting ? "Blocking..." : "Block Persona"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
