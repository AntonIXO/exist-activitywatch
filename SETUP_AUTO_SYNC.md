# Automatic Syncing Setup Guide

Two methods to automatically sync ActivityWatch data to Exist.io in Linux.

## Method 1: Cron Jobs (Simple)

### Setup

1. Open crontab editor:
```bash
crontab -e
```

2. Add one or more of these lines:

```bash
# Sync every hour at the top of the hour
0 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1

# Sync every 30 minutes
*/30 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1

# Sync at end of day (11:55 PM)
55 23 * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1

# Sync every 15 minutes during work hours (9 AM - 6 PM, Mon-Fri)
*/15 9-17 * * 1-5 cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1
```

3. Save and exit (Ctrl+X then Y for nano, :wq for vim)

4. Verify cron is set:
```bash
crontab -l
```

### View Logs

```bash
# See recent syncs
tail -f /tmp/aw-exist-sync.log

# Check cron errors
sudo journalctl -u cron

# Or for systemd-based systems
sudo journalctl -u cron.service
```

---

## Method 2: Systemd Timer (Modern)

More robust than cron, integrates with systemd.

### Setup

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/aw-exist-sync.service
```

Add this content:

```ini
[Unit]
Description=ActivityWatch to Exist.io Sync
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=antonix
WorkingDirectory=/home/antonix/exist/activitywatch-exist
ExecStart=/usr/bin/python3 /home/antonix/exist/activitywatch-exist/sync.py
StandardOutput=journal
StandardError=journal
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `antonix` with your username
- `/home/antonix/...` with actual path

2. Create a systemd timer file:

```bash
sudo nano /etc/systemd/system/aw-exist-sync.timer
```

Add this content:

```ini
[Unit]
Description=Run ActivityWatch to Exist.io Sync
Requires=aw-exist-sync.service

[Timer]
# Run every hour
OnBootSec=5min
OnUnitActiveSec=1h

# Alternative: Run every 30 minutes
# OnUnitActiveSec=30min

# Alternative: Run at specific times
# OnCalendar=*-*-* 09:00,12:00,15:00,18:00:00
# OnCalendar=*-*-* 23:55:00

[Install]
WantedBy=timers.target
```

3. Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aw-exist-sync.timer
sudo systemctl start aw-exist-sync.timer
```

4. Verify it's running:

```bash
sudo systemctl status aw-exist-sync.timer
```

5. View logs:

```bash
# See last 50 lines
sudo journalctl -u aw-exist-sync.service -n 50

# Follow in real-time
sudo journalctl -u aw-exist-sync.service -f

# See all occurrences
sudo journalctl -u aw-exist-sync.service
```

6. Check next run time:

```bash
sudo systemctl list-timers aw-exist-sync.timer
```

---

## Comparison

| Feature | Cron | Systemd Timer |
|---------|------|---------------|
| Setup difficulty | ⭐ Easy | ⭐⭐ Medium |
| Logging | File-based | journalctl (system) |
| Reliability | Good | Excellent |
| Resource efficient | ✅ | ✅ |
| Persistent across reboots | ✅ | ✅ |
| Complex schedules | Limited | Excellent |
| Integration with system | None | Native |

---

## Recommended Setup

**For most users: Cron is simpler**
```bash
# Run every hour
0 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1

# Or more frequently (every 30 min)
*/30 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py >> /tmp/aw-exist-sync.log 2>&1
```

**For advanced users: Systemd timer is more robust**
- Better logging integration
- Can depend on other services
- More flexible scheduling

---

## Troubleshooting

### Cron not running?

1. Check cron is enabled:
```bash
sudo systemctl status cron
sudo systemctl enable cron
sudo systemctl start cron
```

2. Check crontab format:
```bash
# Verify the syntax
crontab -l
# Should show your entries without errors
```

3. Use absolute paths:
```bash
# ❌ Wrong
* * * * * cd /path && python3 sync.py

# ✅ Correct
* * * * * cd /path && /usr/bin/python3 sync.py
```

4. Find Python path:
```bash
which python3
# Output: /usr/bin/python3
```

### Timer not running?

1. Check if enabled:
```bash
sudo systemctl is-enabled aw-exist-sync.timer
```

2. Check status:
```bash
sudo systemctl status aw-exist-sync.timer
```

3. Check for errors:
```bash
sudo journalctl -u aw-exist-sync.service -n 20 --no-pager
```

### Script fails silently?

Add more detailed logging to sync.py or check:

```bash
# Test the script manually
cd /home/antonix/exist/activitywatch-exist
python3 sync.py

# Check permissions
ls -la sync.py
chmod +x sync.py
```

### ActivityWatch not running?

The sync won't work if ActivityWatch daemon isn't running:

```bash
# Check if running
ps aux | grep aw-server

# Start it if needed
activitywatch &

# Or use systemd if available
sudo systemctl start activitywatch
```

---

## Verification

After setup, verify the sync is working:

1. **Check Exist.io dashboard** - should see updated values
2. **Check logs** - look for successful syncs
3. **Test manually** first:
```bash
cd /home/antonix/exist/activitywatch-exist
python3 sync.py
```

---

## Best Practices

1. **Use absolute paths** to Python and working directory
2. **Log output** to track what happens
3. **Test manually first** before automating
4. **Monitor logs** regularly
5. **Start with hourly syncs**, increase frequency if needed
6. **Add error notifications** if possible (optional enhancement)

---

## Optional: Email Notifications on Failure

Add to cron (sends email on error only):

```bash
0 * * * * cd /home/antonix/exist/activitywatch-exist && /usr/bin/python3 sync.py || echo "AW Exist sync failed" | mail -s "Sync Error" your-email@example.com
```

Or for systemd, add to service file:
```ini
OnFailure=notify-send@%n.service
```

---

## Uninstalling

### Cron:
```bash
crontab -r  # Remove all cron jobs
# Or edit:
crontab -e  # Remove specific lines
```

### Systemd:
```bash
sudo systemctl stop aw-exist-sync.timer
sudo systemctl disable aw-exist-sync.timer
sudo rm /etc/systemd/system/aw-exist-sync.*
sudo systemctl daemon-reload
```
