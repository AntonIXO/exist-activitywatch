"""Track which dates have been successfully synced."""

import json
import os
from datetime import datetime, timedelta
from typing import List

from config import SYNC_STATE_FILE, BACKFILL_DAYS


def _load_state() -> dict:
    """Load sync state from disk."""
    if not os.path.exists(SYNC_STATE_FILE):
        return {"synced_dates": {}}
    try:
        with open(SYNC_STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"synced_dates": {}}


def _save_state(state: dict) -> None:
    """Save sync state to disk."""
    with open(SYNC_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def mark_synced(date: datetime) -> None:
    """Record that a date was successfully synced."""
    state = _load_state()
    date_str = date.strftime("%Y-%m-%d")
    state["synced_dates"][date_str] = datetime.now().isoformat()
    _save_state(state)


def is_synced(date: datetime) -> bool:
    """Check if a date has been successfully synced."""
    state = _load_state()
    return date.strftime("%Y-%m-%d") in state["synced_dates"]


def get_unsynced_dates(days: int = None) -> List[datetime]:
    """
    Get dates from the last N days that haven't been successfully synced.

    Args:
        days: Number of past days to check (default: BACKFILL_DAYS from config)

    Returns:
        List of datetime objects for unsynced dates, oldest first.
    """
    if days is None:
        days = BACKFILL_DAYS

    state = _load_state()
    synced = state.get("synced_dates", {})
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    unsynced = []
    for i in range(days, 0, -1):  # oldest first
        date = today - timedelta(days=i)
        if date.strftime("%Y-%m-%d") not in synced:
            unsynced.append(date)

    return unsynced


def cleanup_old_entries(keep_days: int = 30) -> None:
    """Remove entries older than keep_days to prevent unbounded growth."""
    state = _load_state()
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
    state["synced_dates"] = {
        k: v for k, v in state["synced_dates"].items() if k >= cutoff
    }
    _save_state(state)
