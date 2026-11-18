import base64
import json
import uuid
from datetime import datetime
from typing import Optional, Tuple, TypeVar, Generic, List
from pydantic import BaseModel

from backend.app.models.base import ensure_utc

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool = False


def encode_cursor(created_at: datetime, item_id: uuid.UUID) -> str:
    """Encode created_at datetime and UUID item_id into an opaque URL-safe base64 string."""
    payload = {
        "t": ensure_utc(created_at).isoformat(),
        "id": str(item_id),
    }
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor_str: str) -> Optional[Tuple[datetime, uuid.UUID]]:
    """Decode an opaque cursor into (created_at_utc, item_id) tuple. Returns None if invalid."""
    if not cursor_str:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
        dt = ensure_utc(datetime.fromisoformat(payload["t"]))
        item_id = uuid.UUID(payload["id"])
        return dt, item_id
    except Exception:
        return None
