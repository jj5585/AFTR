import re
from typing import List, Optional
from pydantic import BaseModel


class ModerationResult(BaseModel):
    is_allowed: bool
    status: str  # "PUBLISHED", "PENDING_REVIEW", "REJECTED"
    flagged_reasons: List[str] = []
    rejection_message: Optional[str] = None


class ContentModerationEngine:
    """
    Automated pre-publication content moderation engine.
    Enforces AFTR community standards and trust & safety policies:
    - Anti-Doxxing & Privacy: Prevents phone numbers, emails, student IDs, social handles, dorm numbers.
    - Anti-Spam: Prevents commercial crypto pumps, telegram/whatsapp links, cashapp solicitation, bot URLs.
    - Anti-Harassment & Hate Speech: Prevents targeted slurs, dehumanizing bullying, harassment.
    - Anti-Threats & Violence: Prevents violent threats, weapons, and self-harm encouragement.
    - Anti-Non-Consensual: Prevents revenge porn, non-consensual recordings, sextortion, blackmail.
    - Prohibited Sexual Content: Prevents underage references, commercial sex solicitation, and escort services.
    - Human Review Queuing: Holds borderline or suspicious content in PENDING_REVIEW prior to public publishing.
    """

    # 1. Anti-Doxxing & Personal Identifying Information (PII)
    DOXXING_PATTERNS = [
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
        (
            re.compile(r"\b(?:dorm\s*(?:room|hall)?\s*#?\d+|room\s*\d{2,4}[a-zA-Z]?|apt\s*#?\d+)\b", re.IGNORECASE),
            "Specific residential room or dorm identifier detected",
        ),
    ]

    # 2. Commercial Spam, Scams & Bot Promotion
    SPAM_PATTERNS = [
        (
            re.compile(r"\b(?:crypto\s*pump|free\s*bitcoin|guaranteed\s*roi|doubler\s*bot|invest\s*\$\d+)\b", re.IGNORECASE),
            "Commercial cryptocurrency or investment scam detected",
        ),
        (
            re.compile(r"\b(?:t\.me\/[a-zA-Z0-9_]+|join\s*my\s*telegram|whatsapp\s*me\s*at|dm\s*on\s*telegram)\b", re.IGNORECASE),
            "Off-platform redirect or messaging handle solicitation detected",
        ),
        (
            re.compile(r"\b(?:cashapp\s*\$[a-zA-Z0-9_]+|send\s*money\s*to\s*\$[a-zA-Z0-9_]+|venmo\s*me\s*@)\b", re.IGNORECASE),
            "Direct monetary or cash solicitation detected",
        ),
        (
            re.compile(r"\b(?:bit\.ly\/|tinyurl\.com\/|t\.co\/|cutt\.ly\/)[a-zA-Z0-9_-]+", re.IGNORECASE),
            "Shortened link or suspicious external URL detected",
        ),
    ]

    # 3. Harassment, Bullying & Hate Speech
    HARASSMENT_PATTERNS = [
        (
            re.compile(r"\b(?:you\s*are\s*worthless|nobody\s*loves\s*you|ugly\s*freak|go\s*drown)\b", re.IGNORECASE),
            "Targeted abusive harassment or dehumanizing bullying",
        ),
        (
            re.compile(r"\b(?:subhuman|scum\s*of\s*the\s*earth|faggot|nigger|kike|chink|tranny)\b", re.IGNORECASE),
            "Severe hate speech or prohibited slurs",
        ),
    ]

    # 4. Severe Violence, Threats & Self-Harm
    THREAT_PATTERNS = [
        (
            re.compile(r"\b(?:kill\s*yourself|kys|commit\s*suicide|slit\s*your\s*wrists|hang\s*yourself)\b", re.IGNORECASE),
            "Suicide encouragement or self-harm promotion",
        ),
        (
            re.compile(r"\b(?:i\s*will\s*kill\s*you|i\s*will\s*murder|bomb\s*threat|shoot\s*up\s*the|gonna\s*stab\s*you)\b", re.IGNORECASE),
            "Explicit threats of lethal violence or public endangerment",
        ),
    ]

    # 5. Non-Consensual Content, Revenge Porn & Sextortion
    NON_CONSENSUAL_PATTERNS = [
        (
            re.compile(r"\b(?:revenge\s*porn|leaked\s*her\s*nudes|leak\s*his\s*nudes|share\s*her\s*nudes)\b", re.IGNORECASE),
            "Non-consensual sharing of intimate imagery (revenge porn)",
        ),
        (
            re.compile(r"\b(?:hidden\s*cam|secretly\s*recorded\s*sex|voyeur\s*video|creepshot)\b", re.IGNORECASE),
            "Non-consensual recordings or voyeuristic sexual material",
        ),
        (
            re.compile(r"\b(?:pay\s*me\s*or\s*i\s*send\s*your\s*nudes|blackmail\s*with\s*nudes|sextortion)\b", re.IGNORECASE),
            "Sextortion or intimate blackmail threat",
        ),
    ]

    # 6. Prohibited Sexual Content & Minor Safety
    PROHIBITED_SEXUAL_PATTERNS = [
        (
            re.compile(r"\b(?:underage|minor\s*dating|high\s*schooler|jailbait|lolita|teen\s*hookup)\b", re.IGNORECASE),
            "Potential underage activity or minor exploitation violation",
        ),
        (
            re.compile(r"\b(?:escort\s*service|pay\s*for\s*sex|ppm\s*rate|hourly\s*escort|callgirl)\b", re.IGNORECASE),
            "Prohibited commercial sex, escorting, or paid sexual solicitation",
        ),
    ]

    # 7. Borderline / Questionable Content Requiring Human Review Queue
    HUMAN_REVIEW_PATTERNS = [
        (
            re.compile(r"\b(?:cheater\s*alert|scammer\s*warning|named\s*and\s*shamed|watch\s*out\s*for\s*this\s*guy)\b", re.IGNORECASE),
            "Targeted accusation requiring moderator assessment before publication",
        ),
        (
            re.compile(r"\b(?:confidential\s*leak|professor\s*exposed|exam\s*leak|frat\s*scandal)\b", re.IGNORECASE),
            "Campus controversy or institutional leak requiring review",
        ),
        (
            re.compile(r"\b(?:meet\s*me\s*tonight\s*for\s*cash|unverified\s*substance|free\s*pills)\b", re.IGNORECASE),
            "Suspected prohibited transaction requiring verification",
        ),
    ]

    @classmethod
    def evaluate_text(cls, text: str) -> ModerationResult:
        """
        Evaluate submitted text content against all AFTR safety standards.
        Returns ModerationResult with status:
        - "REJECTED": Blatant/severe violation (doxxing, hate speech, threats, scams, minor safety).
        - "PENDING_REVIEW": Held for human moderation review queue; NEVER published to feed until reviewed.
        - "PUBLISHED": Clean content approved for immediate publishing.
        """
        if not text or not text.strip():
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=["Empty content"],
                rejection_message="Content cannot be empty.",
            )

        content = text.strip()

        # Step 1: Check Doxxing & PII (Hard rejection)
        doxxing_flags = []
        for pattern, reason in cls.DOXXING_PATTERNS:
            if pattern.search(content):
                doxxing_flags.append(reason)

        if doxxing_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=doxxing_flags,
                rejection_message=(
                    "Privacy Shield: Personal contact info, student IDs, or residential identifiers "
                    f"were detected ({', '.join(doxxing_flags)}). AFTR strictly protects user anonymity."
                ),
            )

        # Step 2: Check Severe Threats & Violence (Hard rejection)
        threat_flags = []
        for pattern, reason in cls.THREAT_PATTERNS:
            if pattern.search(content):
                threat_flags.append(reason)

        if threat_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=threat_flags,
                rejection_message=(
                    "Safety Shield: Prohibited threats of harm or violence detected "
                    f"({', '.join(threat_flags)})."
                ),
            )

        # Step 3: Check Minor Safety & Prohibited Commercial Sex (Hard rejection)
        prohibited_flags = []
        for pattern, reason in cls.PROHIBITED_SEXUAL_PATTERNS:
            if pattern.search(content):
                prohibited_flags.append(reason)

        if prohibited_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=prohibited_flags,
                rejection_message=(
                    "Content Policy: Content violates AFTR adult platform integrity "
                    f"({', '.join(prohibited_flags)})."
                ),
            )

        # Step 4: Check Non-Consensual Imagery & Sextortion (Hard rejection)
        nc_flags = []
        for pattern, reason in cls.NON_CONSENSUAL_PATTERNS:
            if pattern.search(content):
                nc_flags.append(reason)

        if nc_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=nc_flags,
                rejection_message=(
                    "Safety Shield: Non-consensual content or extortion detected "
                    f"({', '.join(nc_flags)})."
                ),
            )

        # Step 5: Check Hate Speech & Severe Harassment (Hard rejection)
        harassment_flags = []
        for pattern, reason in cls.HARASSMENT_PATTERNS:
            if pattern.search(content):
                harassment_flags.append(reason)

        if harassment_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=harassment_flags,
                rejection_message=(
                    "Community Standards: Harassment or prohibited hate speech detected "
                    f"({', '.join(harassment_flags)})."
                ),
            )

        # Step 6: Check Commercial Spam & External Scams (Hard rejection)
        spam_flags = []
        for pattern, reason in cls.SPAM_PATTERNS:
            if pattern.search(content):
                spam_flags.append(reason)

        if spam_flags:
            return ModerationResult(
                is_allowed=False,
                status="REJECTED",
                flagged_reasons=spam_flags,
                rejection_message=(
                    "Anti-Spam Filter: Commercial spam, off-platform solicitations, or financial scams detected "
                    f"({', '.join(spam_flags)})."
                ),
            )

        # Step 7: Check Borderline / Questionable Patterns (Human Review Queue)
        # Content is saved with status="PENDING_REVIEW" and NOT published to public feeds until approved.
        review_flags = []
        for pattern, reason in cls.HUMAN_REVIEW_PATTERNS:
            if pattern.search(content):
                review_flags.append(reason)

        if review_flags:
            return ModerationResult(
                is_allowed=True,
                status="PENDING_REVIEW",
                flagged_reasons=review_flags,
                rejection_message=None,
            )

        # Step 8: Clean content approved for immediate public publishing
        return ModerationResult(
            is_allowed=True,
            status="PUBLISHED",
            flagged_reasons=[],
            rejection_message=None,
        )
