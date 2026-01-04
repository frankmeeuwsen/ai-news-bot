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

**⚠️ KRITIEKE WERKWIJZE - Anti-Duplicatie Protocol:**

**ALTIJD voordat je een taak uitvoert of een TODO toevoegt:**

1. **Check TODO.md eerst:**
   - Grep/zoek of de taak al bestaat (completed of open)
   - Check of het een herhaling is van eerder werk
   - Wijs Frank erop als hij iets dubbel vraagt

2. **Check git history:**
   - Zoek in commits of het al is gedaan
   - Check LOGBOEK.md voor eerdere sessies
   - Refereer naar eerdere oplossingen

3. **Zeg het hardop:**
   - "Ik zie dat dit al in TODO.md staat onder [sectie]"
   - "Dit lijkt op wat we deden op [datum], zie commit [hash]"
   - "Wil je dit opnieuw doen of de bestaande TODO afmaken?"

**Voorbeeld:**
```
Frank: "Kunnen we een testmodus maken voor prompts?"
Claude: "Ik zie dat dit al in TODO.md staat (regel 33-39) als
'Testmodus voor Prompts' onder High Priority. Wil je dat ik
dit nu ga implementeren, of vroeg je iets anders?"
```

**Waarom kritiek:** Frank vraagt soms dingen opnieuw omdat hij vergeet
wat er al is. Jij moet hem scherp houden en voorkomen dat werk dubbel
wordt gedaan of TODO's dubbel worden toegevoegd.

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
   - OS: Ubuntu (Python 3.10.12)
   - Locatie: `/home/frank/apps/ai-news-bot`
   - SSH Key: `~/.ssh/dtd_rsync`
   - SSH Commando: `ssh -i ~/.ssh/dtd_rsync frank@116.203.122.56`

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
| Herladen wijzigingen | `sudo systemctl restart ai-news-bot.service` |
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

**Troubleshooting:**

Voor problemen met de service, zie [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

### 2025-12-24: Lokale Database Synchronisatie (macOS)

**Context:** Automatische dagelijkse sync van production database van server naar lokale machine voor analyse en development.

**Implementatie:**

1. **Sync Script** (`scripts/sync-database.sh`)
   - Haalt dagelijks `newsbot.db` op van Hetzner server via SCP
   - Maakt automatisch backup (`newsbot.db.backup`) voor rollback
   - macOS notificaties bij succes/falen
   - Logging naar `logs/db-sync.log`

2. **Launchd Agent** (`~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist`)
   - Label: `nl.frankmeeuwsen.ai-news-bot.sync`
   - Schedule: Dagelijks 08:00 uur
   - StartOnMount: Catch-up bij gemiste runs (laptop uit)
   - Logs: `logs/launchd-sync-stdout.log` en `logs/launchd-sync-stderr.log`

3. **Documentatie** (`scripts/README-database-sync.md`)
   - Beheer commando's (start/stop/status)
   - Troubleshooting guide
   - Schema wijziging instructies

**Handige Commando's:**

| Actie | Commando |
|-------|----------|
| Status checken | `launchctl list \| grep ai-news-bot` |
| Handmatig draaien | `launchctl start nl.frankmeeuwsen.ai-news-bot.sync` |
| Logs bekijken | `tail -f logs/db-sync.log` |
| Agent stoppen | `launchctl unload ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist` |
| Agent starten | `launchctl load ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot.sync.plist` |

**SSH Configuratie:**

Gebruikt SSH alias `dtd` (gedefinieerd in `~/.ssh/config`):
```
Host dtd
    HostName 116.203.122.56
    User frank
    IdentityFile ~/.ssh/dtd_rsync
```

**Naming Convention:**

⚠️ **BELANGRIJK:** Gebruik altijd `frankmeeuwsen` (niet `frankwatching`) in:
- Launchd plist labels
- Script namen en identifiers
- Alle macOS services en agents

**Workflow:**

1. Server draait dagelijks om 07:00 (Amsterdam tijd) → genereert nieuwe database
2. Lokaal draait sync om 08:00 → haalt nieuwe database op
3. Notificatie verschijnt automatisch
4. Backup wordt overschreven bij volgende sync

---

## Deployment Leerpunten & Best Practices

### 2026-01-04: Obsidian Integration Deployment - Retrospective

**Context:** Grote feature deployment (Obsidian deep links) met database schema wijzigingen en nieuwe structured fields in `AISummary` model.

**Wat er misging:**

1. **Uncommitted Critical Files (models.py)**
   - **Probleem:** `src/database/models.py` met nieuwe kolommen was NIET gecommit toen `main.py` wel werd gepusht
   - **Impact:** Server kreeg runtime errors: `'title' is an invalid keyword argument for AISummary`
   - **Root cause:** Aanname dat alle gerelateerde wijzigingen automatisch gecommit waren
   - **Gevolg:** 3 gefaalde deployment pogingen voordat dit ontdekt werd

2. **Database Schema vs Code Mismatch**
   - **Probleem:** `summary_text` kolom was `NOT NULL` in database, maar code gaf `None` mee
   - **Impact:** SQLite IntegrityError bij elke summary save
   - **Root cause:** `models.py` had `nullable=True` in code, maar database had nog oude schema
   - **Gevolg:** Nog 2 extra deployment cycles om backward compatibility te fixen

3. **Incomplete Pre-Deployment Validation**
   - **Probleem:** Geen systematische check of alle gerelateerde files gecommit waren
   - **Impact:** Incrementele fixes nodig in plaats van one-shot deployment
   - **Root cause:** Te snel naar `git push` zonder volledige `git status` check
   - **Gevolg:** 5 separate commits nodig om deployment werkend te krijgen

4. **Aanname over Forgejo Auto-Deployment**
   - **Probleem:** Wist dat Forgejo runner bestaat, maar vergat dit actief te verifiëren
   - **Impact:** Onnodige SSH commando's om "handmatig" te deployen
   - **Root cause:** Onvolledige mentale model van deployment pipeline
   - **Gevolg:** Verwarring over waarom server "automatisch" updates kreeg

**Commit History van de Chaos:**

```
7fd9380 - fix: update main.py to use run_id workflow         [main.py ALLEEN]
bd05adf - feat: add structured fields to AISummary            [models.py - VERGETEN]
eafb21b - fix: provide summary_text for backward compat       [generator.py - NULLABLE FIX]
```

**Totale Deployment Tijd:** ~45 minuten (had 5 minuten moeten zijn)

**Wat WEL goed ging:**

- Database migratie script werkte perfect first-time
- Forgejo runner pipeline werkte betrouwbaar
- Feature zelf (Obsidian URIs) werkte direct toen dependencies compleet waren
- Server recovery was snel (geen data loss)

---

### 🎯 Deployment Checklist (VERPLICHT voor schema wijzigingen)

**VOOR elke git push naar main met database/model wijzigingen:**

1. **Git Status Audit**
   ```bash
   git status --short
   # Check ALLE modified files in src/database/, src/news/, main.py
   # Vraag jezelf: "Zijn deze wijzigingen gerelateerd?"
   ```

2. **Database Model Changes Check**
   ```bash
   git diff src/database/models.py
   # Als dit diff toont → check of alle GEBRUIKERS van dit model ook gecommit zijn
   # Grep naar AISummary( in codebase
   ```

3. **Breaking Changes Scan**
   ```bash
   git diff | grep -E "(nullable=False|Column.*NOT NULL|ForeignKey)"
   # Elke nieuwe NOT NULL kolom → migratie nodig OF code moet default waarde geven
   ```

4. **Commit Logica Validatie**
   - Als `models.py` wijzigt → check of `generator.py` of andere gebruikers ook wijzigen
   - Als `main.py` API wijzigt → check of alle aanroepers ook updated zijn
   - Als database schema → check of migratie script up-to-date is

5. **Pre-Push Dry Run (lokaal)**
   ```bash
   # Test of imports werken met nieuwe models
   ./venv/bin/python -c "from src.database.models import AISummary; print(AISummary.__table__.columns.keys())"

   # Test of generator nieuwe fields kan gebruiken
   ./venv/bin/python -c "from src.news.generator import NewsGenerator; print('OK')"
   ```

6. **Post-Push Verification (server)**
   ```bash
   # Wacht 10 seconden op Forgejo runner
   sleep 10

   # Check of commit landed
   ssh dtd 'cd ~/apps/ai-news-bot && git log -1 --oneline'

   # Check of imports werken op server
   ssh dtd 'cd ~/apps/ai-news-bot && ./venv/bin/python -c "from src.database.models import AISummary; print(AISummary.__table__.columns.keys())"'
   ```

---

### 🚨 Red Flags die Deployment Problemen Signaleren

**Tijdens Development:**
- "Ik commit eerst X, dan later Y" → FOUT: commit atomisch of niet
- "Deze file hoef ik niet te committen" → Check 2x of deze file door andere files gebruikt wordt
- `git status` toont modified files in `src/database/` → 99% kans dat je meer moet committen

**Tijdens Deployment:**
- Error: `'X' is an invalid keyword argument` → Model definitie mismatch (models.py niet gesynchroniseerd)
- Error: `NOT NULL constraint failed` → Database schema vs code mismatch (migratie vergeten OF code geeft None)
- Error: `No module named 'X'` → Dependencies niet geïnstalleerd (requirements.txt outdated)

**Deployment Success Criteria:**
- ✅ Alle gerelateerde files in één atomic commit
- ✅ Database migratie script gedraaid (indien schema wijzigt)
- ✅ Server imports testen zonder errors
- ✅ Handmatige testrun op server succesvol

---

### 💡 Ontwikkel Best Practices (afgeleid uit deze sessie)

1. **Atomic Commits voor Gerelateerde Wijzigingen**
   - Models + Gebruikers van die models = 1 commit
   - Schema wijziging + Migratie script = 1 commit
   - API change + Alle callers = 1 commit

2. **Database Schema Wijzigingen = Special Case**
   - ALTIJD migratie script maken (ook voor nullable kolommen)
   - ALTIJD backward compatibility overwegen
   - ALTIJD default waarden geven voor nieuwe NOT NULL kolommen
   - NOOIT oude kolommen verwijderen zonder deprecation periode

3. **"Trust But Verify" voor Automated Deployment**
   - Forgejo runner is betrouwbaar MAAR check altijd of commit daadwerkelijk landed
   - Git push ≠ Deployment success → verify via SSH
   - Automated ≠ Infallible → smoke test na deployment

4. **Mental Model van Deployment Pipeline**
   ```
   git push origin main
       ↓
   Forgejo detecteert push (binnen 5 sec)
       ↓
   Runner draait deploy.yml workflow
       ↓
   SSH naar server → git pull → pip install → systemd restart
       ↓
   Server heeft nieuwe code (binnen 10-15 sec)
   ```

5. **Error Messages zijn Diagnostiek Tools**
   - `'title' is invalid keyword` → Models definitie probleem (check models.py commit)
   - `NOT NULL constraint failed` → Database vs code mismatch (check nullable settings)
   - `ModuleNotFoundError` → Dependency probleem (check requirements.txt + pip install)

---

### 🔧 Tooling Verbeteringen (TODO items hierboven)

- Pre-deployment validation script (`scripts/pre-deploy-check.sh`)
- Post-deployment health check (`scripts/health-check.sh`)
- Automated smoke tests in Forgejo workflow
- Git pre-push hook met model sync check

---

Last updated: 2026-01-04
