# AI News Bot - Troubleshooting Guide

## Service Start Failure (Exit Code 209)

**Datum:** 2025-12-23

**Symptomen:**
- Bot draait niet volgens timer schedule
- Handmatige start faalt met: `Job for ai-news-bot.service failed because the control process exited with error code`
- `systemctl status` toont: `code=exited, status=209/STDOUT`
- systemd journal toont geen entries voor de service

**Root Cause:**

Exit code 209/STDOUT betekent dat systemd de geconfigureerde output stream (logbestand) niet kan openen. In ons geval bestond de logs directory niet.

**Diagnose Stappen:**

```bash
# 1. Check service configuratie
cat /etc/systemd/system/ai-news-bot.service

# 2. Zoek naar StandardOutput/StandardError configuratie
# Bijvoorbeeld:
#   StandardOutput=append:/home/frank/apps/ai-news-bot/logs/output.log
#   StandardError=append:/home/frank/apps/ai-news-bot/logs/error.log

# 3. Check of de directory bestaat
ls -la ~/apps/ai-news-bot/logs/

# 4. Check systemd journal voor details
journalctl -u ai-news-bot.service -n 50 --no-pager
```

**Oplossing:**

```bash
# Maak logs directory aan met correcte permissies
mkdir -p ~/apps/ai-news-bot/logs
chmod 755 ~/apps/ai-news-bot/logs

# Start service opnieuw
sudo systemctl start ai-news-bot.service

# Verificatie
systemctl status ai-news-bot.service
tail -f ~/apps/ai-news-bot/logs/output.log
```

**Verificatie Succesvolle Run:**

```bash
# Service moet 'inactive (dead)' zijn met SUCCESS status
systemctl status ai-news-bot.service

# Output moet eindigen met:
# Main PID: XXXX (code=exited, status=0/SUCCESS)

# Logs moeten bevestiging tonen
tail -5 ~/apps/ai-news-bot/logs/output.log

# Output moet eindigen met ongeveer:
# AI News Bot Completed
# Successfully sent: email (NL)
```

**Preventie:**

Bij toekomstige deployments altijd checken:
1. Alle directories in systemd service configuratie bestaan
2. Directories hebben correcte permissies (755 voor directories, 644 voor files)
3. Test service handmatig na deployment voordat je op timer vertrouwt

**Handige Debug Commando's:**

| Doel | Commando |
|------|----------|
| Service status | `systemctl status ai-news-bot.service` |
| Laatste journal entries | `journalctl -u ai-news-bot.service -n 50 --no-pager` |
| Live logs volgen | `tail -f ~/apps/ai-news-bot/logs/output.log` |
| Error logs bekijken | `tail -f ~/apps/ai-news-bot/logs/error.log` |
| Timer verificatie | `systemctl list-timers ai-news-bot.timer` |
| Process check | `ps aux \| grep 'python main.py'` |

---

## Service Gedrag bij Handmatige Start

**Observatie:**

Wanneer je `sudo systemctl start ai-news-bot.service` handmatig draait, keert het commando **pas terug naar de prompt wanneer het Python proces klaar is** (1-2 minuten).

**Waarom:**

Dit is normaal gedrag voor een `Type=oneshot` systemd service. De service:
- Draait niet in de achtergrond van je terminal sessie
- Wordt volledig beheerd door systemd
- Systemctl wacht op proces completion voordat het terugkeert

**Workaround:**

Als je de logs live wilt volgen tijdens de run, gebruik een apart terminal tabblad:

```bash
# Tabblad 1: Start de service
sudo systemctl start ai-news-bot.service

# Tabblad 2: Volg de logs
ssh -i ~/.ssh/dtd_rsync frank@116.203.122.56
tail -f ~/apps/ai-news-bot/logs/output.log
```

---

## Common systemd Exit Codes

| Code | Betekenis | Mogelijke Oorzaken |
|------|-----------|-------------------|
| 0 | SUCCESS | Proces voltooid zonder errors |
| 1 | FAILURE | Algemene runtime error |
| 126 | NOEXEC | Bestand niet uitvoerbaar (chmod +x nodig) |
| 127 | NOTFOUND | Python binary niet gevonden (check venv path) |
| 203 | EXEC | ExecStart commando kon niet worden uitgevoerd |
| 209 | STDOUT | Kan niet schrijven naar geconfigureerde output |
| 210 | STDERR | Kan niet schrijven naar geconfigureerde error log |

---

Last updated: 2025-12-23
