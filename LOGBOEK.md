# AI News Bot - Logboek

## 2025-12-23: Forgejo Actions CI/CD Implementatie

**Context:** Automatische deployment naar Hetzner server via Forgejo Actions, volledig zelfgehoste CI/CD pipeline.

**Doorgevoerde wijzigingen:**

1. **Forgejo Actions Workflow**
   - Aangemaakt: `.forgejo/workflows/deploy.yml`
   - Trigger: Push naar `main` branch
   - Steps: Checkout → SSH deploy → Git pull op server
   - SSH authenticatie via base64 encoded private key in secret

2. **Deployment Flow**
   - Automatisch: Code push → Forgejo trigger → SSH naar Hetzner → Git pull → Service restart
   - Manual: Via Forgejo UI of `git push forgejo main`
   - Logs: Zichtbaar in Forgejo Actions interface
   - Rollback: Via git revert/reset op server

3. **SSH Key Setup Debugging**
   - Iteratie 1: Heredoc problemen met SSH key formatting
   - Iteratie 2: Hardcoded id_rsa path werkte niet
   - Iteratie 3: Base64 encoding voorkomt newline/formatting issues
   - Final: `echo $SSH_PRIVATE_KEY | base64 -d` in workflow

4. **Git Remote Configuratie**
   - Added: `forgejo` remote naar `git.dutchstack.nl`
   - Workflow: Push naar GitHub (backup) en Forgejo (CI/CD trigger)
   - Authentication: SSH key gedeeld tussen dev machine en Forgejo

5. **Workspace Reset Fix**
   - Probleem: `error: Your local changes to the following files would be overwritten by merge`
   - Oplossing: `git reset --hard HEAD && git clean -fd` voor git pull
   - Reden: Database uploads via workflow creëren uncommitted changes

**Technische Details:**

- Forgejo Secret: `SSH_PRIVATE_KEY` (base64 encoded)
- Server: `frank@116.203.122.56`
- Deploy pad: `/home/frank/apps/ai-news-bot`
- Service restart: `sudo systemctl restart ai-news-bot.service`

**Belangrijke Beslissingen:**

- Base64 encoding voor SSH keys voorkomt formatting issues in YAML
- Workspace reset voor deployment acceptabel (server = productie, geen dev work)
- Database uploads blijven enabled voor debugging (ondanks reset)
- Forgejo als primary CI/CD, GitHub als backup repository

**Documentatie Updates:**

- `CLAUDE.md`: Forgejo Actions sectie toegevoegd met setup instructies
- `TODO.md`: Completed items verwijderd (Forgejo SSH setup, deployment)

**Open Items:**

- Monitoring van deployment failures (alerts)
- Rollback strategie formaliseren
- Database migrations automatiseren in deployment workflow
- Secrets rotation strategy voor SSH keys

**Git Status:**

- Branch: `main`
- Laatste commit: `a86a764` - fix: reset and clean workspace before git pull
- Working tree: clean
- Remotes: origin (dutchstack), github (backup), forgejo (CI/CD)

**Performance:**

- Deployment tijd: ~5-10 seconden (SSH + git pull + restart)
- First successful automated deployment: 2025-12-23
- Zero downtime: systemd restart handling

---

## 2025-12-22: Server Deployment (Hetzner)

**Context:** Migratie van GitHub Actions naar eigen Hetzner server voor meer controle en lagere latency.

**Server Setup:**

1. **Server Details**
   - Host: `116.203.122.56` (Hetzner)
   - User: `frank` (sudo)
   - OS: Ubuntu 20.04 (Python 3.8)
   - Locatie: `/home/frank/apps/ai-news-bot`

2. **Systemd Configuratie**
   - Service: `/etc/systemd/system/ai-news-bot.service`
   - Timer: `/etc/systemd/system/ai-news-bot.timer`
   - Schedule: Dagelijks 07:00 Amsterdam tijd
   - Logs: `~/apps/ai-news-bot/logs/`

3. **Code Fixes voor Server Compatibiliteit**
   - `requirements.txt`: `google-generativeai` optioneel gemaakt
   - `src/llm_providers/__init__.py`: Lazy imports
   - `src/llm_providers/openrouter_provider.py`: Python 3.8 syntax fixes

**Handige Commando's:**

| Actie | Commando |
|-------|----------|
| Status timer | `systemctl status ai-news-bot.timer` |
| Volgende run | `systemctl list-timers ai-news-bot.timer` |
| Handmatig draaien | `sudo systemctl start ai-news-bot.service` |
| Logs bekijken | `tail -f ~/apps/ai-news-bot/logs/output.log` |

---

## 2025-12-10: Database Persistentie & Workflow Fix

**Context:** Database implementatie voor RSS caching, cost tracking en newsletter logging.

**Database Features:**

- 36-uur RSS feed cache met deduplicatie
- RSS health monitoring met auto-disable
- Newsletter run tracking (tokens, kosten, provider)
- Schema ready voor AI selection/summary logging

**Test Resultaten:**

- Run #2: 115 items (100% cache hit), 17 geselecteerd
- Stage 1: 3.2s, Stage 2: 109s
- 10 broken feeds auto-disabled

---

## 2025-12-09: Grote Refactoring - Configuratie Externalisatie

**Context:** Hardcoded prompts en bronnen verspreid door code.

**Wijzigingen:**

1. **Nieuwe Structuur**
   - `sources.yaml`: RSS feed configuratie
   - `prompts/`: Externe prompt templates
   - `config.yaml`: App configuratie

2. **Code Refactoring**
   - `src/news/fetcher.py`: YAML bronnen
   - `src/news/generator.py`: Externe prompts
   - Nieuw: `src/llm_providers/openrouter_provider.py`

3. **Nederlandse Bronnen**
   - Frankwatching, AG Connect, FD Technologie
   - Totaal 20+ bronnen (Engels/Nederlands/Chinees)

**Belangrijke Beslissingen:**

- Configuratie-first aanpak
- OpenRouter als primaire provider
- Twee-staps proces (selectie + samenvatting)
- Multi-taal support

---

Last updated: 2025-12-23
