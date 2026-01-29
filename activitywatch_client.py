"""Client for fetching screen time data from ActivityWatch."""

import requests
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import urlparse

from config import (
    ACTIVITYWATCH_API_BASE,
    SOCIAL_APPS,
    GPT_DOMAINS,
)


def get_buckets() -> dict:
    """Get all buckets from ActivityWatch."""
    response = requests.get(f"{ACTIVITYWATCH_API_BASE}/buckets/")
    response.raise_for_status()
    return response.json()


def find_bucket_by_prefix(prefix: str) -> Optional[str]:
    """Find a bucket by prefix."""
    buckets = get_buckets()
    for bucket_id in buckets:
        if bucket_id.startswith(prefix):
            return bucket_id
    return None


def find_window_bucket() -> Optional[str]:
    """Find the aw-watcher-window bucket for the current machine."""
    return find_bucket_by_prefix("aw-watcher-window_")


def find_afk_bucket() -> Optional[str]:
    """Find the aw-watcher-afk bucket for the current machine."""
    return find_bucket_by_prefix("aw-watcher-afk_")


def find_web_bucket() -> Optional[str]:
    """Find the aw-watcher-web bucket for the browser."""
    return find_bucket_by_prefix("aw-watcher-web")


def get_events_for_date(bucket_id: str, date: datetime) -> List[dict]:
    """
    Get all events from a bucket for a specific date.
    
    Args:
        bucket_id: The bucket ID
        date: The date to get events for
        
    Returns:
        List of events
    """
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    
    response = requests.get(
        f"{ACTIVITYWATCH_API_BASE}/buckets/{bucket_id}/events",
        params={
            "start": start.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
        }
    )
    response.raise_for_status()
    return response.json()


def get_screen_time_for_date(date: datetime) -> float:
    """
    Get total screen time (non-AFK time) for a specific date.
    
    Args:
        date: The date to get screen time for
        
    Returns:
        Screen time in minutes
    """
    afk_bucket = find_afk_bucket()
    
    if not afk_bucket:
        raise RuntimeError("Could not find AFK bucket")
    
    events = get_events_for_date(afk_bucket, date)
    
    # Sum up duration of "not-afk" events
    total_seconds = 0
    for event in events:
        if event.get("data", {}).get("status") == "not-afk":
            total_seconds += event.get("duration", 0)
    
    return round(total_seconds / 60)  # Convert to minutes


def get_social_time_for_date(date: datetime) -> float:
    """
    Get time spent on social network apps (Telegram, etc.) for a specific date.
    
    Args:
        date: The date to get social time for
        
    Returns:
        Social time in minutes
    """
    window_bucket = find_window_bucket()
    
    if not window_bucket:
        raise RuntimeError("Could not find window bucket")
    
    events = get_events_for_date(window_bucket, date)
    
    # Sum up duration of social app events
    total_seconds = 0
    for event in events:
        app = event.get("data", {}).get("app", "").lower()
        for social_app in SOCIAL_APPS:
            if social_app.lower() in app:
                total_seconds += event.get("duration", 0)
                break
    
    return round(total_seconds / 60)  # Convert to minutes


def get_gpt_time_for_date(date: datetime) -> float:
    """
    Get time spent on AI/GPT sites for a specific date.
    
    Args:
        date: The date to get GPT time for
        
    Returns:
        GPT time in minutes
    """
    web_bucket = find_web_bucket()
    
    if not web_bucket:
        # No web bucket, return 0
        return 0
    
    events = get_events_for_date(web_bucket, date)
    
    # Sum up duration of GPT domain events
    total_seconds = 0
    for event in events:
        url = event.get("data", {}).get("url", "")
        try:
            domain = urlparse(url).netloc.lower()
            for gpt_domain in GPT_DOMAINS:
                if gpt_domain.lower() in domain:
                    total_seconds += event.get("duration", 0)
                    break
        except Exception:
            pass
    
    return round(total_seconds / 60)  # Convert to minutes


def get_today_screen_time() -> float:
    """Get screen time for today in minutes."""
    return get_screen_time_for_date(datetime.now())


def get_today_social_time() -> float:
    """Get social time for today in minutes."""
    return get_social_time_for_date(datetime.now())


def get_today_gpt_time() -> float:
    """Get GPT time for today in minutes."""
    return get_gpt_time_for_date(datetime.now())


if __name__ == "__main__":
    # Test the client
    print("Testing ActivityWatch client...")
    try:
        buckets = get_buckets()
        print(f"Found {len(buckets)} buckets:")
        for bucket_id in buckets:
            print(f"  - {bucket_id}")
        
        afk_bucket = find_afk_bucket()
        window_bucket = find_window_bucket()
        web_bucket = find_web_bucket()
        print(f"\nAFK bucket: {afk_bucket}")
        print(f"Window bucket: {window_bucket}")
        print(f"Web bucket: {web_bucket}")
        
        screen_time = get_today_screen_time()
        social_time = get_today_social_time()
        gpt_time = get_today_gpt_time()
        
        print(f"\nToday's stats:")
        print(f"  Screen time: {screen_time} min ({screen_time/60:.1f} hours)")
        print(f"  Social time: {social_time} min ({social_time/60:.1f} hours)")
        print(f"  GPT/AI time: {gpt_time} min ({gpt_time/60:.1f} hours)")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to ActivityWatch. Is it running?")
    except Exception as e:
        print(f"Error: {e}")
