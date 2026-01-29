#!/bin/bash
# Quick setup script for automatic syncing
# Usage: bash setup_cron.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
USER=$(whoami)

echo "=== ActivityWatch to Exist.io Auto-Sync Setup ==="
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Python: $PYTHON_PATH"
echo "User: $USER"
echo ""

# Check if sync.py exists
if [ ! -f "$PROJECT_DIR/sync.py" ]; then
    echo "❌ Error: sync.py not found in $PROJECT_DIR"
    exit 1
fi

# Ask user for frequency
echo "Choose sync frequency:"
echo "  1) Every hour (recommended)"
echo "  2) Every 30 minutes"
echo "  3) Every 15 minutes"
echo "  4) Every 6 hours"
echo "  5) Custom"
read -p "Select (1-5): " choice

case $choice in
    1) CRON_SCHEDULE="0 * * * *" ;;
    2) CRON_SCHEDULE="*/30 * * * *" ;;
    3) CRON_SCHEDULE="*/15 * * * *" ;;
    4) CRON_SCHEDULE="0 */6 * * *" ;;
    5) 
        read -p "Enter cron schedule (e.g., '0 * * * *'): " CRON_SCHEDULE
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Cron schedule: $CRON_SCHEDULE"
echo ""

# Create cron entry
CRON_CMD="$CRON_SCHEDULE cd $PROJECT_DIR && $PYTHON_PATH sync.py >> /tmp/aw-exist-sync.log 2>&1"

# Check if already in crontab
if crontab -l 2>/dev/null | grep -q "aw-exist-sync.py\|$PROJECT_DIR.*sync.py"; then
    echo "⚠️  Sync job already exists in crontab"
    echo ""
    echo "Current crontab:"
    crontab -l | grep -i "sync" || echo "  (not found)"
    echo ""
    read -p "Replace it? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove old entry
    (crontab -l 2>/dev/null | grep -v "sync.py") | crontab - || true
fi

# Add new entry
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "Verify with:"
echo "  crontab -l"
echo ""
echo "View logs with:"
echo "  tail -f /tmp/aw-exist-sync.log"
echo ""
echo "Remove with:"
echo "  crontab -r"
