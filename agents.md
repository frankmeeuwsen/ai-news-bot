# AI News Bot - Claude Context

## Project Overzicht

Een automatische nieuwsbot die RSS feeds verzamelt, cureert met AI (via OpenRouter), en verstuurt via verschillende notificatiekanalen. Ondersteunt meerdere talen en heeft een twee-staps proces (selectie + samenvatting).

**Stack:** Python, OpenRouter API, RSS feeds, YAML configuratie, Markdown templates

**Doel:** Geautomatiseerde nieuwscuratie voor verschillende doelgroepen, met focus op AI/tech nieuws.

---

## Session History

### 2025-12-09: Grote Refactoring - Configuratie Externalisatie

**Context:** Codebase was moeilijk te onderhouden met hardcoded prompts en bronnen verspreid door de code.

**Doorgevoerde wijzigingen:**

1. **Nieuwe Bestandsstructuur**
   - Aangemaakt: `sources.yaml` met RSS feed configuratie
   - Aangemaakt: `prompts/` directory met:
     - `stage1_selection.md` (nieuws selectie prompt)
     - `stage2_summarization.md` (samenvatting prompt)
   - Updated: `config.yaml` met nieuwe configuratie opties

2. **Code Refactoring**
   - `src/news/fetcher.py`: Laden van bronnen uit YAML ipv hardcoded
   - `src/news/generator.py`: Laden van prompts uit externe bestanden
   - `src/config.py`: Nieuwe config validatie en template loading
   - Nieuw bestand: `src/llm_providers/openrouter_provider.py`

3. **Nederlandse Bronnen Toegevoegd**
   - Frankwatching (marketing/tech)
   - AG Connect (agrarisch/tech)
   - FD Technologie (zakelijk/tech)
   - Totaal nu 20+ bronnen over Engels/Nederlands/Chinees

4. **Documentatie**
   - Aangemaakt: `TODO.md` met uitgebreide roadmap
   - Categorieën: High/Medium/Low priority
   - Focus items:
     - Testmodus voor prompts (dry-run)
     - RSS health monitoring
     - Kosten tracking via OpenRouter API
     - Template verbetering (Axios-stijl)

**Belangrijke Beslissingen:**

- **Configuratie-first aanpak:** Alle prompts/bronnen nu extern configureerbaar
- **OpenRouter als primaire provider:** Flexibele model keuze, kosten transparantie
- **Twee-staps proces behouden:** Stage 1 (selectie) → Stage 2 (samenvatting)
- **Multi-taal support:** Engels, Nederlands, Chinees met per-taal bronnen

**Open Items:**

- Implementeren testmodus (`--dry-run` flag) voor prompt testing
- RSS feed health check en monitoring
- Kosten tracking via OpenRouter API integreren
- Template verbetering naar Axios-stijl schrijven
- Serendipity algoritme voor nieuwsselectie (ML/feedback loop)

**Git Status:**

- Branch: `main` (refactor branch verwijderd na merge)
- Commits ahead van origin: 3 commits
- Laatste commits:
  - `13450b5` - feat: add cost tracking todo item
  - `72ba71e` - feat: add comprehensive TODO.md and fix template loading
  - `bfb1931` - feat: Add OpenRouter provider and YAML configuration

**Technische Details:**

- Virtual environment: `/venv` (Python 3.x)
- Dependencies: zie `requirements.txt`
- Config bestanden: YAML voor structuur, Markdown voor content/prompts
- LLM Provider: OpenRouter met configureerbaar model

---

## Ontwikkel Context

**Voor volgende sessies:**

1. **Testmodus prioriteren:** Belangrijk om prompts te kunnen itereren zonder echt te versturen
2. **Kosten monitoring:** OpenRouter API geeft usage data terug, kan gebruikt worden voor tracking
3. **Prompt verbetering:** Focus op Axios-stijl (bulletpoints, "why it matters", korte paragrafen)
4. **RSS monitoring:** Automatisch detecteren van broken feeds voorkomt stille failures

**Configuratie Locaties:**

- RSS feeds: `/sources.yaml`
- Prompts: `/prompts/*.md`
- App config: `/config.yaml`
- Secrets: `/.env` (niet in git)

**Code Organisatie:**

- `/src/news/` - Core nieuwslogica (fetcher, generator)
- `/src/llm_providers/` - LLM integraties (OpenRouter)
- `/src/config.py` - Configuratie management

---

### 2025-12-10: Database Persistentie & GitHub Actions Workflow Fix

**Context:** Database implementatie toegevoegd voor RSS caching, cost tracking en newsletter run logging. GitHub Actions workflow geanalyseerd en aangepast voor database support.

**Database Implementatie:**

1. **Database Module (src/database/)**
   - `models.py`: 6 SQLAlchemy tabellen (NewsItem, NewsletterRun, AISelection, AISummary, RSSHealth, UserFeedback)
   - `db.py`: DatabaseManager singleton met session handling
   - `__init__.py`: Clean exports voor module imports

2. **Database Features**
   - 36-uur RSS feed cache met GUID/link deduplicatie
   - RSS health monitoring met auto-disable na 3-5 failures
   - Newsletter run tracking (provider, model, tokens, kosten)
   - Separate cost tracking voor Stage 1 (selectie) en Stage 2 (samenvatting)
   - Schema ready voor AI selection/summary logging en user feedback

3. **Code Integratie**
   - `main.py`: Database initialisatie toegevoegd via `init_db()` call
   - `src/news/fetcher.py`: Cache check, item opslag, health tracking
   - `src/news/generator.py`: Helper methods voor database tracking
   - `src/news/generator_with_tracking.py`: Wrapper class voor volledige tracking
   - `src/llm_providers/openrouter_provider.py`: Usage data return (`return_usage=True`)

4. **Test Suite**
   - `test_database.py`: Comprehensive database tests (CRUD, dedup, cache TTL, health)
   - `test_fetch_only.py`: RSS fetch met caching zonder AI processing
   - `test_tracking.py`: Newsletter run tracking zonder API calls
   - `test_full_generation.py`: Volledige pipeline test met echte API calls
   - `test_newsletter_output.md`: Voorbeeld gegenereerde Nederlandse nieuwsbrief

**GitHub Actions Workflow Fix:**

1. **Kritieke Problemen Geïdentificeerd**
   - Database werd niet geïnitialiseerd in `main.py` (RuntimeError)
   - `data/` directory bestond niet in GitHub runner (FileNotFoundError)
   - NewsFetcher gebruikt altijd database calls (geen opt-out)
   - RSS health tracking crasht zonder database

2. **Workflow Aanpassingen (.github/workflows/daily-news.yml)**
   - Database cache restore step toegevoegd (actions/cache@v4)
   - `data/` directory aanmaken voor SQLite database
   - Database upload bij failures voor debugging
   - Cache key: `newsbot-db-${{ github.run_id }}` met fallback

3. **Performance Impact**
   - Eerste run: +0.5s database overhead
   - Cached runs: -15-20s (geen RSS fetches)
   - Broken feeds: -10-50s (auto-disabled, geen timeouts)

**Test Resultaten:**

- Run #2: 115 items (100% cache hit), 17 geselecteerd
- Stage 1: 3.2s, Stage 2: 109s, totaal: 131s
- 10 broken feeds auto-disabled
- Professionele Nederlandse nieuwsbrief gegenereerd met categorisatie

**Configuratie:**

- Cache disabled in `config.yaml` voor testrun (vers items ophalen)
- Database: SQLite (`data/newsbot.db`)
- TTL: 36 uur (configureerbaar)
- Deduplication: GUID → link fallback

**Git Status:**

- Commit: `dc33717` - feat: add database persistence with caching and cost tracking
- 21 files changed: 2103 insertions, 30 deletions
- Pushed naar: origin (dutchstack) en github
- Working tree: clean
- Database directory: volledig gewist voor testrun

**Breaking Changes:** Geen

- Backward compatible met bestaande config
- Geen nieuwe secrets vereist
- Cache disabled by default
- Alle environment variables unchanged

---

### 2025-12-22: Server Deployment (Hetzner)

**Context:** Migratie van GitHub Actions naar eigen Hetzner server voor meer controle en lagere latency.

**Server Setup:**

1. **Server Details**
   - Host: `116.203.122.56` (Hetzner)
   - User: `frank` (sudo)
   - OS: Ubuntu 20.04 (Python 3.8)
   - Locatie: `/home/frank/apps/ai-news-bot`

2. **Git Remote Configuratie**
   - **Forgejo (origin):** `git@git.dutchstack.nl:frankmeeuwsen/ai-news-bot.git`
   - **GitHub (github):** `git@github.com:frankmeeuwsen/ai-news-bot.git`
   - Web interface: `https://forgejo.dutchstack.nl:3000`
   - SSH via: `git.dutchstack.nl` (zonder Cloudflare proxy voor SSH support)
   - Beide remotes werkend op lokaal en server

3. **Systemd Configuratie**
   - Service: `/etc/systemd/system/ai-news-bot.service`
   - Timer: `/etc/systemd/system/ai-news-bot.timer`
   - Schedule: Dagelijks 07:00 Amsterdam tijd
   - Logs: `~/apps/ai-news-bot/logs/`

4. **Code Fixes voor Server Compatibiliteit**
   - `requirements.txt`: `google-generativeai` optioneel gemaakt (niet nodig voor Claude/OpenRouter)
   - `src/llm_providers/__init__.py`: Lazy imports - providers worden alleen geladen wanneer nodig
   - `src/llm_providers/openrouter_provider.py`: `Union[str, Dict]` syntax ipv `str | Dict` voor Python 3.8

**Configuratie:**

- Environment: `~/.env-newsbot` (of `.env` in project dir)
- LLM Provider: OpenRouter (claude/sonnet-4.5)
- Notificaties: Gmail SMTP
- Database: SQLite (`data/newsbot.db`)

**Handige Commando's:**

| Actie | Commando |
|-------|----------|
| Status timer | `systemctl status ai-news-bot.timer` |
| Volgende run | `systemctl list-timers ai-news-bot.timer` |
| Handmatig draaien | `sudo systemctl start ai-news-bot.service` |
| Logs bekijken | `tail -f ~/apps/ai-news-bot/logs/output.log` |
| Errors bekijken | `tail -f ~/apps/ai-news-bot/logs/error.log` |

**Failure Alerts:**

- Script: `scripts/alert-on-failure.sh`
- Triggered via `ExecStopPost` in systemd service
- Stuurt email bij failures

**Forgejo Actions CI/CD:**

- Automatische deployment via `.forgejo/workflows/deploy.yml`
- Runner: `hetzner-runner` op server (systemd service)
- Trigger: Push naar `main` branch
- Deployment flow:
  1. SSH naar server met deployment key
  2. `git pull origin main`
  3. `pip install -r requirements.txt`
  4. `sudo systemctl restart ai-news-bot.timer`
- Logs: `https://forgejo.dutchstack.nl/frankmeeuwsen/ai-news-bot/actions`
- Runner status: `sudo systemctl status forgejo-runner.service`

---

Last updated: 2025-12-23
