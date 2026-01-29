"""Configuration for ActivityWatch to Exist.io sync."""

# Exist.io API configuration
EXIST_ACCESS_TOKEN = ""
EXIST_API_BASE = "https://exist.io/api/2"

# ActivityWatch API configuration
ACTIVITYWATCH_API_BASE = "http://localhost:5600/api/0"

# Attribute names in Exist.io (custom attributes)
# Note: Exist.io normalizes names - underscores become separate words
EXIST_SCREEN_TIME_ATTR = "screen_time"  # Total screen time
EXIST_SOCIAL_ATTR = "social_networks"  # Social networks time (Telegram, etc.)
EXIST_GPT_ATTR = "ai_assistants"  # AI assistants time (ChatGPT, Gemini, Perplexity, etc.)
EXIST_FOCUS_SCORE_ATTR = "focus_score"  # Focus/context switching score (0-100)

# Apps to track for social networks (window app names)
SOCIAL_APPS = [
    "telegram-desktop",
    "Telegram",
    "org.telegram.desktop",
    "telegramdesktop",
]

# Domains to track for GPT/AI usage (from browser)
GPT_DOMAINS = [
    "chat.openai.com",
    "chatgpt.com",
    "gemini.google.com",
    "perplexity.ai",
    "www.perplexity.ai",
    "claude.ai",
    "poe.com",
    "bard.google.com",
]

# --- Focus Score Configuration ---

# Noise threshold: events shorter than this are considered noise (seconds)
# Used for de-bouncing quick app switches
NOISE_THRESHOLD_SEC = 5

# Deep work threshold: sessions longer than this indicate deep focus (minutes)
DEEP_WORK_THRESHOLD_MIN = 15

# Fragmentation threshold: median session below this is fragmented (minutes)
FRAGMENTATION_THRESHOLD_MIN = 2

# Focus score sensitivity coefficient (k in e^(-k * switches_per_hour))
# Higher k = more penalty for switching
# k=0.05: 20 switches/hr -> score 37, 50 switches/hr -> score 8
# k=0.03: 20 switches/hr -> score 55, 50 switches/hr -> score 22
FOCUS_SCORE_K = 0.05
