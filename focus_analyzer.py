"""
Focus Score Analyzer - Context Switching Detection

Calculates a focus score (0-100) based on:
1. Session duration (de-bounced to filter noise)
2. Switches per hour
3. Shannon entropy of app distribution

Score 100 = Deep focus, minimal switching
Score 0 = Constant context switching, fragmented attention
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from activitywatch_client import (
    get_events_for_date,
    find_window_bucket,
    get_not_afk_intervals,
    filter_events_by_not_afk,
)

from config import (
    NOISE_THRESHOLD_SEC,
    DEEP_WORK_THRESHOLD_MIN,
    FRAGMENTATION_THRESHOLD_MIN,
    FOCUS_SCORE_K,
)


@dataclass
class FocusMetrics:
    """Container for focus analysis results."""
    median_session_min: float
    switches_per_hour: float
    shannon_entropy: float
    total_sessions: int
    total_time_min: float
    focus_score: int  # 0-100
    
    def __str__(self):
        return (
            f"Focus Score: {self.focus_score}/100\n"
            f"  Median session: {self.median_session_min:.1f} min\n"
            f"  Switches/hour: {self.switches_per_hour:.1f}\n"
            f"  Entropy: {self.shannon_entropy:.2f}\n"
            f"  Sessions: {self.total_sessions}, Time: {self.total_time_min:.0f} min"
        )


def get_window_events_for_date(date: datetime) -> List[dict]:
    """Get window events for a specific date, filtered to exclude AFK time."""
    bucket = find_window_bucket()
    if not bucket:
        return []
    events = get_events_for_date(bucket, date)
    not_afk = get_not_afk_intervals(date)
    return filter_events_by_not_afk(events, not_afk)


def debounce_events(events: List[dict], noise_threshold_sec: float = None) -> List[dict]:
    """
    De-bounce events to filter noise.
    
    Merges consecutive events of the same app and filters out
    micro-switches (< threshold seconds).
    
    Example:
        [VS Code, 5s] -> [Chrome, 2s] -> [VS Code, 10m]
        becomes:
        [VS Code, 10m 7s]  (Chrome was just noise)
    """
    if noise_threshold_sec is None:
        noise_threshold_sec = NOISE_THRESHOLD_SEC
    
    if not events:
        return []
    
    # Sort by timestamp (oldest first)
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
    
    # First pass: merge consecutive same-app events
    merged = []
    for event in sorted_events:
        app = event.get("data", {}).get("app", "unknown")
        duration = event.get("duration", 0)
        
        if merged and merged[-1]["app"] == app:
            merged[-1]["duration"] += duration
        else:
            merged.append({"app": app, "duration": duration})
    
    # Second pass: absorb noise (short events between same-app events)
    # If we have A -> B -> A where B is short, merge into A
    cleaned = []
    i = 0
    while i < len(merged):
        current = merged[i].copy()
        
        # Look ahead for pattern: current -> short_noise -> same_as_current
        while i + 2 < len(merged):
            noise = merged[i + 1]
            next_same = merged[i + 2]
            
            if (noise["duration"] < noise_threshold_sec and 
                next_same["app"] == current["app"]):
                # Absorb both the noise and the next same-app event
                current["duration"] += noise["duration"] + next_same["duration"]
                i += 2
            else:
                break
        
        cleaned.append(current)
        i += 1
    
    # Filter out remaining micro-sessions
    real_sessions = [s for s in cleaned if s["duration"] >= noise_threshold_sec]
    
    return real_sessions


def calculate_shannon_entropy(sessions: List[dict]) -> float:
    """
    Calculate Shannon entropy of app time distribution.
    
    H = -Σ(p_i * log2(p_i))
    
    Low entropy (< 1.0) = focused on few apps
    High entropy (> 3.0) = scattered across many apps
    """
    if not sessions:
        return 0.0
    
    # Calculate total time per app
    app_durations: Dict[str, float] = {}
    for session in sessions:
        app = session["app"]
        duration = session["duration"]
        app_durations[app] = app_durations.get(app, 0) + duration
    
    total_duration = sum(app_durations.values())
    if total_duration == 0:
        return 0.0
    
    # Calculate probabilities and entropy
    entropy = 0.0
    for duration in app_durations.values():
        p = duration / total_duration
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def calculate_median(values: List[float]) -> float:
    """Calculate median of a list of values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def calculate_focus_score(
    median_session_min: float,
    switches_per_hour: float,
    entropy: float
) -> int:
    """
    Calculate overall focus score (0-100).
    
    Combines multiple factors:
    1. Penalty for high switch rate: e^(-k * switches_per_hour)
    2. Bonus for long median sessions
    3. Penalty for high entropy
    
    Formula:
        base_score = 100 * e^(-k * switches_per_hour)
        session_bonus = min(20, median_session_min)  # cap at 20 min bonus
        entropy_penalty = entropy * 5  # each unit of entropy costs 5 points
        
        score = base_score + session_bonus - entropy_penalty
    """
    # Base score from switch rate (exponential decay)
    # At 0 switches/hour: 100, at 20 switches/hour: ~37, at 50: ~7
    base_score = 100 * math.exp(-FOCUS_SCORE_K * switches_per_hour)
    
    # Session duration bonus (longer sessions = better)
    # Capped contribution: 0-20 points based on median session
    session_bonus = min(20, median_session_min)
    
    # Entropy penalty (more scattered = worse)
    # Low entropy (< 1): minimal penalty
    # High entropy (> 3): significant penalty
    entropy_penalty = entropy * 5
    
    # Combine
    score = base_score + session_bonus - entropy_penalty
    
    # Clamp to 0-100
    return max(0, min(100, int(round(score))))


def analyze_focus_for_date(date: datetime) -> Optional[FocusMetrics]:
    """
    Analyze focus/context switching for a specific date.
    
    Returns FocusMetrics or None if no data.
    """
    events = get_window_events_for_date(date)
    
    if not events:
        return None
    
    # De-bounce to get real sessions
    sessions = debounce_events(events)
    
    if not sessions:
        return None
    
    # Calculate metrics
    durations_sec = [s["duration"] for s in sessions]
    durations_min = [d / 60 for d in durations_sec]
    
    median_session_min = calculate_median(durations_min)
    total_time_sec = sum(durations_sec)
    total_time_hours = total_time_sec / 3600
    
    # Switches per hour (number of context switches divided by active hours)
    switches_per_hour = (len(sessions) - 1) / total_time_hours if total_time_hours > 0 else 0
    
    # Shannon entropy
    entropy = calculate_shannon_entropy(sessions)
    
    # Overall focus score
    focus_score = calculate_focus_score(median_session_min, switches_per_hour, entropy)
    
    return FocusMetrics(
        median_session_min=median_session_min,
        switches_per_hour=switches_per_hour,
        shannon_entropy=entropy,
        total_sessions=len(sessions),
        total_time_min=total_time_sec / 60,
        focus_score=focus_score
    )


def get_focus_score_for_date(date: datetime) -> int:
    """Get just the focus score (0-100) for a date."""
    metrics = analyze_focus_for_date(date)
    return metrics.focus_score if metrics else 50  # Default to neutral


def get_today_focus_score() -> int:
    """Get focus score for today."""
    return get_focus_score_for_date(datetime.now())


def interpret_score(score: int) -> str:
    """Get human-readable interpretation of focus score."""
    if score >= 80:
        return "🧘 Deep Work Machine - Excellent focus!"
    elif score >= 60:
        return "✅ Good Focus - Solid work session"
    elif score >= 40:
        return "⚠️ Moderate - Some fragmentation"
    elif score >= 20:
        return "🔶 Fragmented - Many context switches"
    else:
        return "🚨 Severe Fragmentation - Dopamine detox needed"


if __name__ == "__main__":
    print("Testing Focus Analyzer...")
    print()
    
    metrics = analyze_focus_for_date(datetime.now())
    
    if metrics:
        print(metrics)
        print()
        print(interpret_score(metrics.focus_score))
        
        # Show breakdown
        print("\n--- Score Breakdown ---")
        print(f"Deep work threshold: {DEEP_WORK_THRESHOLD_MIN} min")
        print(f"Fragmentation zone: < {FRAGMENTATION_THRESHOLD_MIN} min")
        
        if metrics.median_session_min < FRAGMENTATION_THRESHOLD_MIN:
            print("⚠️ Median session below fragmentation threshold!")
        elif metrics.median_session_min > DEEP_WORK_THRESHOLD_MIN:
            print("✅ Median session in deep work range!")
    else:
        print("No window data available for today")
