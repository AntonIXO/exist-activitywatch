#!/usr/bin/env python3
"""
Sync ActivityWatch data to Exist.io.

Metrics synced:
- Total screen time (non-AFK time)
- Social networks time (Telegram, etc.)
- AI assistants time (ChatGPT, Gemini, Perplexity, etc.)
- Focus score (0-100 based on context switching analysis)

Usage:
    python sync.py              # Sync today's data
    python sync.py --date 2024-01-15  # Sync specific date
    python sync.py --days 7     # Sync last 7 days
"""

import argparse
import sys
from datetime import datetime, timedelta

from activitywatch_client import (
    get_buckets,
    get_screen_time_for_date,
    get_social_time_for_date,
    get_gpt_time_for_date,
)
from focus_analyzer import (
    analyze_focus_for_date,
    interpret_score,
)
from exist_client import (
    ensure_all_attributes,
    push_screen_time,
    push_social_time,
    push_gpt_time,
    push_focus_score,
)
from config import (
    EXIST_SCREEN_TIME_ATTR,
    EXIST_SOCIAL_ATTR,
    EXIST_GPT_ATTR,
    EXIST_FOCUS_SCORE_ATTR,
)


def sync_date(date: datetime, dry_run: bool = False) -> bool:
    """
    Sync all metrics for a specific date.
    
    Returns True if all successful.
    """
    date_str = date.strftime("%Y-%m-%d")
    all_ok = True
    
    try:
        # Get all metrics from ActivityWatch
        screen_time = get_screen_time_for_date(date)
        social_time = get_social_time_for_date(date)
        gpt_time = get_gpt_time_for_date(date)
        
        # Get focus score
        focus_metrics = analyze_focus_for_date(date)
        focus_score = focus_metrics.focus_score if focus_metrics else 50
        
        print(f"{date_str}:")
        print(f"  Screen time: {screen_time} min ({screen_time/60:.1f}h)")
        print(f"  Social:      {social_time} min ({social_time/60:.1f}h)")
        print(f"  AI/GPT:      {gpt_time} min ({gpt_time/60:.1f}h)")
        print(f"  Focus score: {focus_score}/100", end="")
        if focus_metrics:
            print(f" (median: {focus_metrics.median_session_min:.1f}m, "
                  f"switches: {focus_metrics.switches_per_hour:.0f}/h)")
        else:
            print(" (no data)")
        
        if dry_run:
            print("  (dry run - not pushing)")
            return True
        
        # Push to Exist.io
        metrics = [
            (EXIST_SCREEN_TIME_ATTR, screen_time, push_screen_time),
            (EXIST_SOCIAL_ATTR, social_time, push_social_time),
            (EXIST_GPT_ATTR, gpt_time, push_gpt_time),
            (EXIST_FOCUS_SCORE_ATTR, focus_score, push_focus_score),
        ]
        
        for attr_name, value, push_func in metrics:
            result = push_func(value, date)
            if result.get("success"):
                pass  # Silent success
            else:
                print(f"  ✗ Failed {attr_name}: {result.get('failed', result)}")
                all_ok = False
        
        if all_ok:
            print("  ✓ Pushed to Exist.io")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        all_ok = False
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Sync ActivityWatch data to Exist.io"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Specific date to sync (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of past days to sync (default: 1, today only)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without actually pushing"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Only set up Exist.io attributes, don't sync"
    )
    
    args = parser.parse_args()
    
    # Check ActivityWatch connection
    print("Checking ActivityWatch connection...")
    try:
        buckets = get_buckets()
        print(f"✓ Connected to ActivityWatch ({len(buckets)} buckets)")
    except Exception as e:
        print(f"✗ Cannot connect to ActivityWatch: {e}")
        print("  Make sure ActivityWatch is running!")
        sys.exit(1)
    
    # Ensure all attributes are set up in Exist.io
    print()
    if not ensure_all_attributes():
        print("✗ Failed to set up some Exist.io attributes")
        sys.exit(1)
    print("✓ Exist.io attributes ready")
    
    if args.setup:
        print("\nSetup complete!")
        return
    
    print("\nSyncing data...")
    
    # Determine dates to sync
    if args.date:
        dates = [datetime.strptime(args.date, "%Y-%m-%d")]
    else:
        today = datetime.now()
        dates = [today - timedelta(days=i) for i in range(args.days)]
        dates.reverse()  # Oldest first
    
    # Sync each date
    success_count = 0
    for date in dates:
        if sync_date(date, args.dry_run):
            success_count += 1
    
    print(f"\nSynced {success_count}/{len(dates)} days")
    
    if success_count < len(dates):
        sys.exit(1)


if __name__ == "__main__":
    main()
