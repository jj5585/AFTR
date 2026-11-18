import re
from typing import Tuple, List, Optional
from pydantic import BaseModel


class ModerationResult(BaseModel):
    is_allowed: bool
    status: str  # "PUBLISHED", "PENDING_REVIEW", "REJECTED"
    flagged_reasons: List[str] = []
    rejection_message: Optional[str] = None


class ContentModerationEngine:
    """
    Automated pre-publication content moderation engine.
    Enforces AFTR community standards:
    - Anti-Doxxing: Prevents phone numbers, emails, student/roll IDs, and social handles.
    - Safety: Flags severe harassment, threats, or underage references.
    """

    # Anti-doxxing regex patterns
    PII_PATTERNS = [
        (
            re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE),
            "Email address detected",
        ),
        (
            re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
            "Phone number detected",
        ),
        (
            re.compile(r"\b(?:student\s*id|roll\s*no|reg\s*no|id\s*#|matric\s*no)\s*[:#-]?\s*\w+", re.IGNORECASE),
            "Student / College ID number detected",
        ),
        (
            re.compile(r"@[a-zA-Z0-9_]{3,24}"),
            "Social media handle (@handle) detected",
        ),
    ]

    # Severe violation patterns requiring immediate rejection or hold
    SEVERE_PATTERNS = [
        (
            re.compile(r"\b(?:kill\s*yourself|kys|die\s*in\s*a\s*fire|bomb\s*threat)\b", re.IGNORECASE),
            "Threats of violence or severe self-harm",
        ),
        (
            re.compile(r"\b(?:underage|minor\s*dating|high\s*schooler|jailbait)\b", re.IGNORECASE),
            "Potential underage activity violation",
        ),
    ]

    @classmethod
    def evaluate_text(cls, text: str) -> ModerationResult:
        if not text or not text.strip():
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=["Empty content"],
                rejection_message="Content cannot be empty.",
            )

        flagged: List[str] = []

        # 1. Check PII patterns (Strict privacy protection)
        for pattern, reason in cls.PII_PATTERNS:
            if pattern.search(text):
                flagged.append(reason)

        if flagged:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=flagged,
                rejection_message=(
                    "Privacy Shield: Personal contact info, real names, or student identifiers "
                    f"were detected ({', '.join(flagged)}). Anonymity is strictly enforced."
                ),
            )

        # 2. Check Severe patterns
        severe_flags: List[str] = []
        for pattern, reason in cls.SEVERE_PATTERNS:
            if pattern.search(text):
                severe_flags.append(reason)

        if severe_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=severe_flags,
                rejection_message=(
                    "Content policy violation: Text contains prohibited expressions "
                    f"({', '.join(severe_flags)})."
                ),
            )

        # 3. Clean and approved
        return ModerationResult(
            is_allowed=True,
            status="PUBLISHED",
            flagged_reasons=[],
            rejection_message=None,
        )
