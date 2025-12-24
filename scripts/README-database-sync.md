# Database Sync - Automatische Dagelijkse Synchronisatie

## Overzicht

Automatische synchronisatie van de `newsbot.db` database van de Hetzner server naar je lokale machine.

**Wanneer:** Dagelijks om 08:00 uur
**Wat:** Haalt de nieuwste database op via SCP
**Notificatie:** macOS notificatie bij succes of falen
**Catch-up:** Draait automatisch na opstarten als je laptop om 8 uur uit stond

## Bestanden

| Bestand | Locatie | Doel |
|---------|---------|------|
| Sync script | `scripts/sync-database.sh` | Haalt database op + notificatie |
| Launchd plist | `~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist` | Dagelijkse scheduling |
| Sync log | `logs/db-sync.log` | Log van sync operaties |
| Launchd stdout | `logs/launchd-sync-stdout.log` | Launchd output |
| Launchd stderr | `logs/launchd-sync-stderr.log` | Launchd errors |

## Handige Commando's

### Status Controleren

```bash
# Is de agent geladen?
launchctl list | grep ai-news-bot

# Output: -    0    nl.frankmeeuwsen.ai-news-bot.sync
# Eerste getal = laatste exit status (0 = success)
```

### Handmatig Draaien

```bash
# Trigger een sync nu (voor testen)
launchctl start nl.frankmeeuwsen.ai-news-bot.sync

# Check de log
tail -f logs/db-sync.log
```

### Agent Beheren

```bash
# Stop de agent (voorkomt automatische runs)
launchctl unload ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist

# Start de agent opnieuw
launchctl load ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist

# Herlaad na wijzigingen aan plist
launchctl unload ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist
launchctl load ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist
```

### Logs Bekijken

```bash
# Sync log (vanuit script)
tail -20 logs/db-sync.log

# Launchd logs
tail -20 logs/launchd-sync-stdout.log
tail -20 logs/launchd-sync-stderr.log

# Live monitoring
tail -f logs/db-sync.log
```

## Wat Gebeurt Er Bij Een Sync?

1. **Backup:** Huidige `data/newsbot.db` wordt gekopieerd naar `data/newsbot.db.backup`
2. **Download:** Nieuwe database wordt opgehaald via SCP van server
3. **Notificatie:** macOS notificatie met status (✓ of ✗)
4. **Logging:** Timestamp en status in `logs/db-sync.log`

## Troubleshooting

### Sync Faalt

```bash
# Check SSH connectie naar server
ssh dtd "ls -lh /home/frank/apps/ai-news-bot/data/newsbot.db"

# Check of bestand bestaat op server
scp dtd:/home/frank/apps/ai-news-bot/data/newsbot.db /tmp/test.db

# Check logs
cat logs/launchd-sync-stderr.log
```

### Geen Notificaties

macOS notificaties werken alleen als:
- Laptop niet in Do Not Disturb modus staat
- Terminal/script rechten heeft voor notificaties (System Settings > Notifications)

### Agent Start Niet

```bash
# Check syntax van plist
plutil -lint ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist

# Check permissions
ls -l ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist
# Moet leesbaar zijn voor je user

# Herlaad agent
launchctl unload ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist
launchctl load ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist
```

## Schema Wijzigen

Om de tijd te veranderen, pas `~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist` aan:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>  <!-- Wijzig dit getal (0-23) -->
    <key>Minute</key>
    <integer>0</integer>  <!-- Wijzig dit getal (0-59) -->
</dict>
```

Herlaad daarna de agent (zie commando's hierboven).

## Backup Strategie

Het script maakt automatisch een backup (`data/newsbot.db.backup`) bij elke sync. Deze backup wordt overschreven bij de volgende sync. Voor langere geschiedenis:

```bash
# Maak handmatig een gedateerde backup
cp data/newsbot.db data/newsbot-$(date +%Y%m%d).db
```

## SSH Configuratie

Het script gebruikt de SSH alias `dtd` (gedefinieerd in `~/.ssh/config`):

```
Host dtd
    HostName 116.203.122.56
    User frank
    IdentityFile ~/.ssh/dtd_rsync
```

Als je SSH setup wijzigt, pas dan ook `scripts/sync-database.sh` aan.
