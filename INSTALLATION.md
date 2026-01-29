# Installation & Auto-Sync Setup Guide

## ✅ Complete Setup (What Was Done)

Your ActivityWatch to Exist.io sync is now ready!

### Cron Job Installed
```
0 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1
```

This runs **every hour at the top of the hour**.

---

## 🚀 Quick Commands

### View logs in real-time
```bash
tail -f /tmp/aw-exist-sync.log
```

### Test sync manually
```bash
cd /home/antonix/exist/activitywatch-exist
python3 sync.py
```

### Check installed cron jobs
```bash
crontab -l
```

### View cron job history
```bash
grep CRON /var/log/syslog | tail -20
```

### Modify cron job
```bash
crontab -e
```

### Remove cron job
```bash
crontab -r
```

---

## 📊 Data Synced (4 Metrics)

| Metric | Description | Value Type | Example |
|--------|-------------|-----------|---------|
| Screen Time | Total active time | Minutes | 480 min/day |
| Social Networks | Telegram usage | Minutes | 45 min/day |
| AI Assistants | ChatGPT, Gemini, etc. | Minutes | 120 min/day |
| Focus Score | Context switching score | 0-100 | 42/100 |

All values are synced to your Exist.io dashboard every hour.

---

## 🔧 Alternative: Systemd Timer

If you prefer systemd (more modern):

```bash
sudo cp /home/antonix/exist/activitywatch-exist/aw-exist-sync.service /etc/systemd/system/
sudo cp /home/antonix/exist/activitywatch-exist/aw-exist-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aw-exist-sync.timer
```

View logs:
```bash
sudo journalctl -u aw-exist-sync.service -f
```

---

## ✨ Sync Frequency Options

Current setup: **Every hour**

To change frequency, edit crontab:

```bash
crontab -e
```

**Common schedules:**
- Every 15 minutes: `*/15 * * * *`
- Every 30 minutes: `*/30 * * * *`
- Every hour: `0 * * * *` (current)
- Every 6 hours: `0 */6 * * *`
- Once daily at 11:55 PM: `55 23 * * *`

---

## 🐛 Troubleshooting

### Sync not running?

1. **Check cron is enabled:**
   ```bash
   sudo systemctl status cron
   ```

2. **Check crontab entries:**
   ```bash
   crontab -l
   ```

3. **Check Python path:**
   ```bash
   which python3
   # Should output: /usr/bin/python3
   ```

4. **Test manually:**
   ```bash
   cd /home/antonix/exist/activitywatch-exist
   python3 sync.py
   ```

### ActivityWatch not running?

```bash
# Check if running
ps aux | grep aw-server

# Start ActivityWatch
activitywatch &
```

### No data in Exist.io?

1. Verify your token in config.py
2. Check sync logs: `tail -f /tmp/aw-exist-sync.log`
3. Test manually: `python3 sync.py`

---

## 📁 Project Files

```
/home/antonix/exist/activitywatch-exist/
├── sync.py                      # Main sync script
├── config.py                    # Configuration (EDIT THESE!)
├── activitywatch_client.py      # ActivityWatch API client
├── exist_client.py              # Exist.io API client
├── focus_analyzer.py            # Focus score calculation
├── setup_auto_sync.sh           # Interactive setup helper
├── setup_cron.sh                # Simple cron setup
├── aw-exist-sync.service        # Systemd service file
├── aw-exist-sync.timer          # Systemd timer file
├── README.md                    # Feature overview
├── SETUP_AUTO_SYNC.md           # Detailed setup guide
├── INSTALLATION.md              # This file
└── requirements.txt             # Python dependencies
```

---

## 🎯 Next Steps

1. **Verify sync is working:**
   ```bash
   # Check logs
   tail -f /tmp/aw-exist-sync.log
   
   # Or test manually
   python3 sync.py
   ```

2. **Check Exist.io dashboard:**
   - Go to https://exist.io
   - Look for: Screen Time, Social Networks, AI Assistants, Focus Score
   - Should update hourly

3. **Customize configuration:**
   Edit `/home/antonix/exist/activitywatch-exist/config.py`:
   - Change tracked apps
   - Change tracked domains
   - Adjust focus score sensitivity

4. **View detailed logs:**
   ```bash
   # Show last 50 lines
   tail -50 /tmp/aw-exist-sync.log
   
   # Follow in real-time
   tail -f /tmp/aw-exist-sync.log
   ```

---

## 📚 Documentation

- **README.md** - Feature overview & usage
- **SETUP_AUTO_SYNC.md** - Detailed setup guide with troubleshooting
- **INSTALLATION.md** - This file (quick reference)
- **config.py** - Inline comments for all options

---

## 🆘 Need Help?

Check logs first:
```bash
tail -f /tmp/aw-exist-sync.log
```

Common issues:
- **No data:** ActivityWatch isn't running
- **Auth error:** Wrong Exist.io token in config.py
- **Cron not running:** Check `crontab -l` and `sudo systemctl status cron`

For more help, see SETUP_AUTO_SYNC.md

---

**Status: ✅ Ready to go!**

Your sync is scheduled to run every hour. Check back in a few hours to see your first data in Exist.io!
