# Server Health Check Dashboard

## Overzicht

Het `health-check.sh` script biedt quick diagnostics van de AI News Bot server status. Gebruikt voor post-deployment verificatie en troubleshooting.

## Gebruik

### Lokaal (op server)

```bash
cd ~/apps/ai-news-bot
./scripts/health-check.sh
```

### Remote (vanaf development machine)

```bash
ssh dtd 'cd ~/apps/ai-news-bot && ./scripts/health-check.sh'
```

### Exit Codes

- **0** = 🟢 HEALTHY - All checks passed
- **1** = 🔴 UNHEALTHY - Critical issues detected
- **2** = 🟡 WARNING - Minor issues found

## Checks

### 1. Git Repository Status
- **Current commit hash** - Verifieert welke versie draait
- **Working tree** - Detecteert uncommitted changes
- **Remote sync** - Checkt of server in sync is met origin/main
- **Use case:** Verify deployment landed correctly

### 2. Python Environment
- **Virtual environment** - Check of venv bestaat
- **Python version** - Welke Python versie wordt gebruikt
- **Critical packages** - Import tests voor openai, pyyaml, feedparser, sqlalchemy
- **Dependencies count** - Aantal installed vs required
- **Use case:** Detect missing dependencies na deployment

### 3. Database Status
- **File existence** - Check of newsbot.db bestaat
- **Database size** - Disk usage monitoring
- **Database accessibility** - Connection test
- **Record counts** - Sanity check (NewsItem, NewsletterRun, RSSHealth)
- **Use case:** Verify database migrations and data integrity

### 4. Configuration Files
- **Config files** - config.yaml, sources.yaml, .env
- **Environment variables** - OPENROUTER_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
- **Use case:** Detect missing configuration na deployment

### 5. Systemd Service Status (alleen op server)
- **Service file** - Check of ai-news-bot.service bestaat
- **Timer status** - Is timer active?
- **Next run time** - Wanneer draait de volgende newsletter?
- **Last run result** - Success/failure van laatste run
- **Use case:** Monitor service health en scheduling

### 6. Log Files
- **Logs directory** - Check of logs/ bestaat
- **Log files** - Aantal en most recent log
- **Error detection** - Grep naar errors/exceptions in recent log
- **Use case:** Quick error diagnosis

### 7. Disk Space
- **Usage percentage** - Warning bij >80%, error bij >90%
- **Available space** - Hoeveel ruimte is er nog?
- **Use case:** Prevent disk full issues

## Output Voorbeelden

### 🟢 Healthy Server

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVER HEALTH CHECK DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Checking AI News Bot server health...
Timestamp: 2026-01-27 07:00:00 UTC
Hostname: hetzner-server

▶ Git Repository Status
  ✓ Git repository accessible
    → Current commit: 9610b85 - feat: add pre-deployment validation script
  ✓ Working tree clean
  ✓ In sync with origin/main

▶ Python Environment
  ✓ Virtual environment exists
    → Python 3.10.12
  ✓ All critical packages installed
  ✓ Dependencies appear up to date (35 installed)

▶ Database Status
  ✓ Database file exists
    → Database size: 12M
  ✓ Database accessible
    → News items: 1250
    → Newsletter runs: 45
    → RSS health records: 20

▶ Configuration Files
  ✓ Config file exists (config.yaml)
  ✓ RSS sources exists (sources.yaml)
  ✓ Environment variables exists (~/.env-newsbot)
  ✓ All required environment variables set

▶ Systemd Service Status
  ✓ Service file exists
  ✓ Timer is active
    → Next run: Tue 2026-01-28 07:00:00
  ✓ Last run: success (exit code: 0)

▶ Log Files
  ✓ Logs directory exists
  ✓ Found 5 log file(s)
    → Most recent: logs/output.log (125K, 2500 lines)
  ✓ No errors in recent log

▶ Disk Space
  ✓ Disk usage: 45%
    → Available: 25G

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEALTH CHECK SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
  ✓ Healthy:  18
  ⚠ Warnings: 0
  ✗ Errors:   0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 HEALTHY - All checks passed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Server is healthy and ready for operation
```

### 🔴 Unhealthy Server (Issues Detected)

```
▶ Python Environment
  ✓ Virtual environment exists
  ✗ Missing packages: pyyaml feedparser
    → Run: pip install -r requirements.txt
  ⚠ May need to update dependencies

▶ Database Status
  ✓ Database file exists
  ✗ Database query failed
    → Database not initialized. Call init_db() first.

▶ Systemd Service Status
  ✓ Service file exists
  ⚠ Timer is not active (inactive)
    → Run: sudo systemctl start ai-news-bot.timer
  ✗ Last run: failed (exit code: 1)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEALTH CHECK SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
  ✓ Healthy:  8
  ⚠ Warnings: 2
  ✗ Errors:   3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 UNHEALTHY - Critical issues detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Action required: Review and fix errors above
```

## Workflow Integratie

### Post-Deployment Workflow

```bash
# 1. Deploy
git push origin main

# 2. Wait for Forgejo auto-deployment
sleep 15

# 3. Run health check
ssh dtd 'cd ~/apps/ai-news-bot && ./scripts/health-check.sh'

# 4. Verify exit code
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful and healthy"
else
    echo "⚠️  Deployment issues detected - investigate"
fi
```

### Scheduled Health Checks (Cron)

Optioneel: dagelijkse health check report via email

```bash
# /etc/cron.daily/ai-news-bot-health
#!/bin/bash
cd /home/frank/apps/ai-news-bot
./scripts/health-check.sh > /tmp/health-report.txt 2>&1

if [ $? -ne 0 ]; then
    mail -s "⚠️ AI News Bot Health Check Failed" frank@example.com < /tmp/health-report.txt
fi
```

## Troubleshooting Specifieke Issues

### "Missing packages: X"

```bash
cd ~/apps/ai-news-bot
source venv/bin/activate
pip install -r requirements.txt
```

### "Database query failed"

```bash
# Check database file permissions
ls -lh data/newsbot.db

# Try to initialize database
./venv/bin/python -c "from src.database import init_db; init_db()"
```

### "Out of sync with origin/main"

```bash
# Pull latest changes
cd ~/apps/ai-news-bot
git pull origin main

# Restart service
sudo systemctl restart ai-news-bot.timer
```

### "Timer is not active"

```bash
# Start timer
sudo systemctl start ai-news-bot.timer

# Enable on boot
sudo systemctl enable ai-news-bot.timer

# Check status
systemctl status ai-news-bot.timer
```

### "Last run: failed"

```bash
# Check service logs
journalctl -u ai-news-bot.service -n 50 --no-pager

# Check application logs
tail -100 ~/apps/ai-news-bot/logs/error.log

# Try manual run for debugging
cd ~/apps/ai-news-bot
./venv/bin/python main.py
```

## Gebruik met Forgejo Actions

Je kunt de health check integreren in de Forgejo deployment workflow:

```yaml
# .forgejo/workflows/deploy.yml
- name: Post-deployment health check
  run: |
    ./scripts/health-check.sh
    if [ $? -ne 0 ]; then
      echo "::warning::Post-deployment health check failed"
    fi
```

## Monitoring Integratie

Exit codes kunnen gebruikt worden voor monitoring tools:

```bash
# Prometheus node_exporter textfile collector
ssh dtd 'cd ~/apps/ai-news-bot && ./scripts/health-check.sh' > /dev/null
echo "ai_news_bot_health $?" > /var/lib/node_exporter/ai-news-bot.prom
```

## Zie Ook

- `scripts/pre-deploy-check.sh` - Pre-deployment validation
- `TROUBLESHOOTING.md` - Gedetailleerde troubleshooting guide
- `CLAUDE.md` - Deployment retrospective en leerpunten
