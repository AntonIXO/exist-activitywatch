# ActivityWatch to Exist.io Sync

Syncs activity data from [ActivityWatch](https://activitywatch.net/) to [Exist.io](https://exist.io/).

## Tracked Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| **Screen Time** | Total active (non-AFK) time | AFK watcher |
| **Social Networks** | Time on Telegram, etc. | Window watcher |
| **AI Assistants** | Time on ChatGPT, Gemini, Perplexity, Claude | Browser watcher |
| **Focus Score** | Context switching score (0-100) | Window watcher |

## Focus Score Algorithm

The focus score measures how focused vs fragmented your attention is:

- **100** = Deep focus, minimal context switching
- **0** = Constant switching, fragmented attention

### How it's calculated:

1. **De-bouncing**: Filters noise (switches < 5 seconds)
2. **Median Session Duration**: How long you typically stay in one app
3. **Switches per Hour**: Frequency of context changes
4. **Shannon Entropy**: How scattered your attention is across apps

### Formula:
```
base_score = 100 × e^(-k × switches_per_hour)
session_bonus = min(20, median_session_minutes)
entropy_penalty = entropy × 5
score = base_score + session_bonus - entropy_penalty
```

### Interpretation:
- **80-100**: 🧘 Deep Work Machine
- **60-79**: ✅ Good Focus
- **40-59**: ⚠️ Moderate fragmentation
- **20-39**: 🔶 Fragmented
- **0-19**: 🚨 Severe fragmentation

## Requirements

- Python 3.6+
- ActivityWatch running locally
- Exist.io account with API access

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to:

1. Set your Exist.io access token
2. Customize tracked apps/domains:

```python
# Social apps (window app names)
SOCIAL_APPS = ["telegram-desktop", "Telegram", ...]

# AI/GPT domains
GPT_DOMAINS = ["chat.openai.com", "gemini.google.com", "perplexity.ai", ...]

# Focus score tuning
NOISE_THRESHOLD_SEC = 5      # Ignore switches shorter than this
DEEP_WORK_THRESHOLD_MIN = 15 # Threshold for "deep work"
FOCUS_SCORE_K = 0.05         # Sensitivity to switching (higher = stricter)
```

## Usage

### First-time setup

```bash
python sync.py --setup
```

### Sync today's data

```bash
python sync.py
```

### Sync a specific date

```bash
python sync.py --date 2024-01-15
```

### Sync last 7 days

```bash
python sync.py --days 7
```

### Dry run

```bash
python sync.py --dry-run
```

### Analyze focus only (no sync)

```bash
python focus_analyzer.py
```

## Automation

Add to crontab for automatic sync:

```bash
# Sync every hour
0 * * * * cd /path/to/activitywatch-exist && python sync.py

# Or at end of day
55 23 * * * cd /path/to/activitywatch-exist && python sync.py
```

## How It Works

1. Fetches events from ActivityWatch buckets:
   - `aw-watcher-afk` for screen time
   - `aw-watcher-window` for app usage and focus analysis
   - `aw-watcher-web` for browser usage
2. Calculates time spent on each category
3. Analyzes context switching patterns for focus score
4. Pushes to Exist.io custom attributes
