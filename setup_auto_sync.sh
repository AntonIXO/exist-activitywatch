#!/bin/bash
# Complete setup for automatic syncing
# Usage: bash setup_auto_sync.sh [cron|systemd]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ActivityWatch to Exist.io Auto-Sync Setup ===${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
if [ ! -f "$PROJECT_DIR/sync.py" ]; then
    echo -e "${RED}❌ Error: sync.py not found in $PROJECT_DIR${NC}"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/config.py" ]; then
    echo -e "${RED}❌ Error: config.py not found${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project directory: $PROJECT_DIR${NC}"
echo -e "${GREEN}✓ Python: $PYTHON_PATH${NC}"
echo -e "${GREEN}✓ User: $(whoami)${NC}"
echo ""

# Detect method
METHOD="${1:-}"
if [ -z "$METHOD" ]; then
    echo -e "${YELLOW}Choose setup method:${NC}"
    echo "  1) Cron job (simpler, recommended for most users)"
    echo "  2) Systemd timer (more modern, better logging)"
    read -p "Select (1-2): " choice
    
    case $choice in
        1) METHOD="cron" ;;
        2) METHOD="systemd" ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
fi

echo ""
echo -e "${BLUE}Setting up with: $METHOD${NC}"
echo ""

if [ "$METHOD" = "cron" ]; then
    # ===== CRON SETUP =====
    
    echo -e "${YELLOW}Choose sync frequency:${NC}"
    echo "  1) Every hour (recommended)"
    echo "  2) Every 30 minutes"
    echo "  3) Every 15 minutes"
    echo "  4) Every 6 hours"
    echo "  5) Custom"
    read -p "Select (1-5): " freq_choice
    
    case $freq_choice in
        1) CRON_SCHEDULE="0 * * * *" ;;
        2) CRON_SCHEDULE="*/30 * * * *" ;;
        3) CRON_SCHEDULE="*/15 * * * *" ;;
        4) CRON_SCHEDULE="0 */6 * * *" ;;
        5) 
            read -p "Enter cron schedule (e.g., '0 * * * *'): " CRON_SCHEDULE
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${YELLOW}Cron schedule: $CRON_SCHEDULE${NC}"
    echo ""
    
    # Create cron entry
    CRON_CMD="$CRON_SCHEDULE cd $PROJECT_DIR && $PYTHON_PATH sync.py >> /tmp/aw-exist-sync.log 2>&1"
    
    # Check if already in crontab
    if crontab -l 2>/dev/null | grep -q "sync.py"; then
        echo -e "${YELLOW}⚠️  Sync job already exists in crontab${NC}"
        echo ""
        crontab -l | grep -i "sync" || true
        echo ""
        read -p "Replace it? (y/n): " confirm
        if [ "$confirm" != "y" ]; then
            echo -e "${YELLOW}Cancelled.${NC}"
            exit 0
        fi
        # Remove old entry
        (crontab -l 2>/dev/null | grep -v "sync.py") | crontab - || true
    fi
    
    # Add new entry
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Verify: crontab -l"
    echo "  2. View logs: tail -f /tmp/aw-exist-sync.log"
    echo "  3. Remove: crontab -r"
    echo ""
    
elif [ "$METHOD" = "systemd" ]; then
    # ===== SYSTEMD SETUP =====
    
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}❌ Systemd setup requires sudo. Run:${NC}"
        echo "  sudo $0 systemd"
        exit 1
    fi
    
    echo -e "${YELLOW}Choose sync frequency:${NC}"
    echo "  1) Every hour (recommended)"
    echo "  2) Every 30 minutes"
    echo "  3) Every 15 minutes"
    echo "  4) Custom"
    read -p "Select (1-4): " freq_choice
    
    case $freq_choice in
        1) TIMER_SCHEDULE="1h" ;;
        2) TIMER_SCHEDULE="30min" ;;
        3) TIMER_SCHEDULE="15min" ;;
        4)
            read -p "Enter systemd timer schedule (e.g., '1h', '30min'): " TIMER_SCHEDULE
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${YELLOW}Timer schedule: $TIMER_SCHEDULE${NC}"
    echo ""
    
    # Copy service files
    echo -e "${BLUE}Installing systemd files...${NC}"
    cp "$PROJECT_DIR/aw-exist-sync.service" /etc/systemd/system/
    cp "$PROJECT_DIR/aw-exist-sync.timer" /etc/systemd/system/
    
    # Update timer if custom schedule
    if [ "$freq_choice" = "4" ]; then
        sed -i "s/OnUnitActiveSec=1h/OnUnitActiveSec=$TIMER_SCHEDULE/" /etc/systemd/system/aw-exist-sync.timer
    fi
    
    # Enable and start
    systemctl daemon-reload
    systemctl enable aw-exist-sync.timer
    systemctl start aw-exist-sync.timer
    
    echo -e "${GREEN}✅ Systemd timer installed and started!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Check status: systemctl status aw-exist-sync.timer"
    echo "  2. View logs: journalctl -u aw-exist-sync.service -f"
    echo "  3. Next run: systemctl list-timers aw-exist-sync.timer"
    echo "  4. Remove: sudo systemctl disable --now aw-exist-sync.timer && sudo rm /etc/systemd/system/aw-exist-sync.*"
    echo ""

else
    echo -e "${RED}Unknown method: $METHOD${NC}"
    exit 1
fi

# Common next steps
echo -e "${BLUE}Test the sync manually first:${NC}"
echo "  cd $PROJECT_DIR"
echo "  python3 sync.py"
echo ""
echo -e "${YELLOW}Remember:${NC}"
echo "  - ActivityWatch must be running for sync to work"
echo "  - Check your Exist.io account to verify data is updating"
echo "  - Edit config.py to customize what gets tracked"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
