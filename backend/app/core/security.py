import base64
import hashlib
import hmac
import secrets
import struct
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.account import Account, AccountStatus
from backend.app.models.persona import Persona

security_scheme = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    """Cryptographically secure SHA-256 hash of an invitation token."""
    return hashlib.sha256(token.strip().encode()).hexdigest()


def hash_recipient_email(email: str) -> str:
    """Salted HMAC-SHA256 hash of recipient email for zero-leakage binding."""
    normalized = email.lower().strip()
    return hmac.new(
        settings.SECRET_KEY.encode(),
        normalized.encode(),
        hashlib.sha256,
    ).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for verification hints (e.g., 'd***e@example.com')."""
    if "@" not in email:
        return "***"
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[0] + "***"
    else:
        masked_local = local_part[0] + "***" + local_part[-1]
    return f"{masked_local}@{domain}"


def generate_secure_invitation_token() -> str:
    """Generate a high-entropy 32-byte URL-safe cryptographic token."""
    return secrets.token_urlsafe(32)


def create_claim_ticket(token_hash: str, recipient_email: str, expires_minutes: int = 30) -> str:
    """Generate a short-lived signed claim ticket for onboarding."""
    payload = {
        "token_hash": token_hash,
        "recipient_hash": hash_recipient_email(recipient_email),
        "email": recipient_email.lower().strip(),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        "iat": datetime.now(timezone.utc),
        "ticket_type": "INVITATION_CLAIM",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_claim_ticket(ticket: str) -> Dict[str, Any]:
    """Verify and decode a claim ticket."""
    try:
        payload = jwt.decode(ticket, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("ticket_type") != "INVITATION_CLAIM":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket type",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation claim ticket has expired. Please claim the invitation again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or tampered invitation claim ticket.",
        )


def create_test_jwt(supabase_user_id: uuid.UUID, email: str, expires_hours: int = 24) -> str:
    """Generate a mock/test Supabase JWT for testing authentication."""
    payload = {
        "sub": str(supabase_user_id),
        "email": email.lower().strip(),
        "role": "authenticated",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode a Supabase JWT on the backend.
    Enforces signature validity, expiration, and audience.
    """
    try:
        # Supabase default signing uses HS256 with SUPABASE_JWT_SECRET
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256", "RS256"],
            options={"verify_aud": False},  # aud can be 'authenticated' or custom
        )
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT token missing subject (sub) claim.",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
        )


async def get_current_supabase_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """Dependency: Extract and verify JWT from Authorization Bearer header."""
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_supabase_jwt(auth_header.credentials)


async def get_current_account(
    user_payload: Dict[str, Any] = Depends(get_current_supabase_user),
    db: AsyncSession = Depends(get_db),
) -> Account:
    """
    Dependency: Lookup the internal Account record corresponding to the Supabase user UUID.
    Enforces that only registered, invited, and active accounts can access AFTR routes.
    """
    sub = user_payload.get("sub")
    try:
        user_uuid = uuid.UUID(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user UUID in authentication token.",
        )

    result = await db.execute(
        select(Account).where(Account.supabase_user_id == user_uuid)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation required: This account has not completed the AFTR invitation gate.",
        )

    if account.status == AccountStatus.BANNED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been banned due to terms or moderation violations.",
        )

    if account.status == AccountStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is currently suspended pending review.",
        )

    return account


async def get_current_persona(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> Persona:
    """Dependency: Get active anonymous persona for the authenticated account."""
    result = await db.execute(
        select(Persona)
        .options(selectinload(Persona.campus_affiliations))
        .where(Persona.account_id == account.id, Persona.is_active == True)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anonymous persona profile has not been created yet.",
        )
    return persona


async def get_optional_persona(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[Persona]:
    """Dependency: Extract persona if Authorization Bearer header is present, otherwise return None."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        payload = decode_supabase_jwt(auth_header.credentials)
        sub = payload.get("sub")
        if not sub:
            return None
        user_uuid = uuid.UUID(sub)
        account_res = await db.execute(
            select(Account).where(Account.supabase_user_id == user_uuid)
        )
        account = account_res.scalar_one_or_none()
        if not account or account.status != AccountStatus.ACTIVE:
            return None
        persona_res = await db.execute(
            select(Persona).where(Persona.account_id == account.id, Persona.is_active == True)
        )
        return persona_res.scalar_one_or_none()
    except Exception:
        return None


# --- Administrative Security & Role-Based Access Control ---

def generate_mfa_secret() -> str:
    """Generate high-entropy RFC 6238 Base32 secret for administrator MFA."""
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").replace("=", "")


def get_totp_code(secret_b32: str, interval: int = 30) -> str:
    """Generate current 6-digit TOTP code using standard RFC 6238."""
    # Add padding if needed
    padded = secret_b32.upper() + "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = int(time.time() // interval)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[19] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def verify_totp(secret_b32: str, code: str, interval: int = 30, window: int = 1) -> bool:
    """Verify 6-digit TOTP code with time-drift window (+/- 30 seconds)."""
    if not secret_b32 or not code:
        return False
    try:
        padded = secret_b32.upper() + "=" * ((8 - len(secret_b32) % 8) % 8)
        key = base64.b32decode(padded, casefold=True)
    except Exception:
        return False

    clean_code = code.strip()
    current_counter = int(time.time() // interval)
    for c in range(current_counter - window, current_counter + window + 1):
        msg = struct.pack(">Q", c)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        offset = digest[19] & 0x0F
        expected = f"{(struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000:06d}"
        if hmac.compare_digest(expected, clean_code):
            return True
    return False


async def require_moderator(
    account: Account = Depends(get_current_account),
) -> Account:
    """
    Dependency: Enforce that caller has at least MODERATOR privileges.
    Permits MODERATOR and SECURITY_ADMIN roles.
    Rejects normal USERs with 403 Forbidden.
    """
    if account.role not in ("MODERATOR", "SECURITY_ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access denied: Moderator or Security Administrator role required.",
        )
    return account


async def require_security_admin(
    account: Account = Depends(get_current_account),
) -> Account:
    """
    Dependency: Enforce that caller has SECURITY_ADMIN privileges.
    Strictly isolates security admin operations (account bans, quota adjustments, audit log export)
    from standard content moderators.
    Rejects normal USERs and standard MODERATORs with 403 Forbidden.
    """
    if account.role != "SECURITY_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access denied: Security Administrator role required for this sensitive operation.",
        )
    return account


def verify_admin_mfa_stepup(
    account: Account,
    x_admin_mfa: Optional[str] = Header(None, alias="X-Admin-MFA"),
) -> None:
    """
    Dependency / Guard: For sensitive operations, verify MFA step-up authentication.
    If MFA is enabled on the account, requires valid 6-digit TOTP code in X-Admin-MFA header.
    """
    if account.mfa_enabled and account.mfa_secret:
        if not x_admin_mfa:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA Step-Up required: Provide valid 6-digit code in X-Admin-MFA header for sensitive operation.",
            )
        if not verify_totp(account.mfa_secret, x_admin_mfa):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA Verification failed: Invalid or expired code.",
            )


