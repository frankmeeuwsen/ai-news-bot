# AI News Bot - Logboek

## 2026-02-28: Security Audit & README Herschreven - Repo Publiek (80 min)

### Wat is gedaan

- **Security audit voor publieke GitHub repo:** Gevoelige bestanden en data uit git verwijderd
  - `CLAUDE.md`, `gemini.md`, `agents.md` uit git tracking gehaald (bevatten server IP, SSH paden)
  - `examples/` directory verwijderd (HTML met persoonlijke emailadressen)
  - `.gitignore` bijgewerkt met `examples/`
  - Server IP, SSH key paden en server paden gescrubbed uit `LOGBOEK.md`, `TROUBLESHOOTING.md`, `scripts/README-database-sync.md`
  - Forgejo deploy workflow: hardcoded IP/user vervangen door `${{ secrets.SERVER_HOST }}` en `${{ secrets.SERVER_USER }}`
  - `StrictHostKeyChecking=no` verwijderd uit deploy workflow
  - Hardcoded email default verwijderd uit `resend_notifier.py`

- **SSH key management:** Nieuwe deploy key (`dtd_deploy_new`) aangemaakt maar bleek overbodig. Bestaande `forgejo_deploy_key` werkte al correct. Oude `dtd_rsync` key was per ongeluk van server verwijderd en hersteld.

- **Forgejo secrets geconfigureerd:** `SERVER_HOST` en `SERVER_USER` als repository secrets toegevoegd.

- **README.md volledig herschreven** naar actuele staat van het project:
  - Two-stage AI pipeline beschreven
  - Accurate projectstructuur
  - CLI opties, database schema, scripts overzicht
  - Drie deployment opties (Hetzner systemd, GitHub Actions, lokaal)
  - Credits naar originele fork

- **GitHub repo publiek gemaakt** - project is nu open source.

### Commits

- `4842285` - chore: security audit - scrub sensitive data before making repo public
- `703b9a5` - docs: rewrite README.md to reflect current project state
- Beide commits gepusht naar origin (Forgejo) en github

### Open Items

- [ ] NewsletterRun tracking completeren
- [ ] Deployment Smoke Tests
- [ ] Verify Forgejo deploy workflow werkt met nieuwe secrets

---

## 2026-02-27: SSH Sudo Automatisering & Weekly Report Timer (30 min)

### Wat is gedaan

- **SSH sudo whitelist op server:** `/etc/sudoers.d/claude-automation` aangemaakt met passwordless sudo voor specifieke systemd commando's (start/stop/restart/status op `ai-news-bot*` units en `ai-news-bot-weekly-report*` units)
- **Claude Code permissies bijgewerkt:** `.claude/settings.local.json` uitgebreid met wildcard SSH en SCP patterns voor de Hetzner server (staat in `.gitignore`, niet in git)
- **Weekly report systemd timer gedeployed:** `ai-news-bot-weekly-report.timer` en `ai-news-bot-weekly-report.service` op server geinstalleerd, draait elke maandag 08:00 Amsterdam tijd
- **Getest:** Positieve tests (correcte commando's zonder sudo password) en negatieve tests (ongeautoriseerde commando's geweigerd) - alles werkt zoals verwacht

### Technische Details

- Sudoers whitelist beperkt tot specifieke systemd unit namen (geen root shell, geen algemene sudo)
- Timer configuratie: `OnCalendar=Mon *-*-* 08:00:00`, timezone Amsterdam, `Persistent=true`
- TODO.md bijgewerkt: SSH sudo automatisering als afgerond gemarkeerd, weekly report timer correctie (maandag ipv zaterdag)

### Open Items

- [ ] NewsletterRun tracking completeren (items_selected, runtime_seconds etc. worden niet ingevuld)
- [ ] Deployment Smoke Tests

---

## 2026-02-17: Server Failure - Dubbele .env Bestanden & Verouderde Config

**Context:** Nieuwsbot faalde op 17 februari met `401 - User not found` van OpenRouter. Er was niets gewijzigd aan code of server. Laatste succesvolle run: 16 februari 06:00 UTC.

**Root Cause Analyse:**

Het probleem bleek een **configuratie-divergentie** die maanden onopgemerkt bleef:

| Bestand | Locatie | LLM_PROVIDER | Email | Laatst gewijzigd |
|---------|---------|-------------|-------|------------------|
| `.env-newsbot` | `~/.env-newsbot` | `openrouter` | Gmail | 4 jan |
| `.env` | `~/apps/ai-news-bot/.env` | `claude` | Resend | 25 jan |

**Hoe dit kon gebeuren:**

1. Bij de oorspronkelijke server setup (dec 2025) werd `.env-newsbot` aangemaakt als systemd `EnvironmentFile`
2. Later is de code gemigreerd van OpenRouter naar Anthropic Claude direct, en van Gmail naar Resend
3. Die wijzigingen zijn alleen in het project `.env` bestand gedaan, NIET in `~/.env-newsbot`
4. Systemd laadt `.env-newsbot` VOOR Python start. Python's `load_dotenv()` overschrijft geen bestaande variabelen
5. Dus `LLM_PROVIDER=openrouter` uit het oude bestand won altijd, ook al stond `.env` op `claude`
6. Dit werkte toevallig omdat OpenRouter het model `anthropic/claude-sonnet-4.5` aanriep - zelfde resultaat, omweg via OpenRouter
7. Op 17 februari werd de OpenRouter API key ongeldig (verlopen/credits op) en faalde alles

**Bijkomende problemen ontdekt:**

- `alert-on-failure.sh` sourcede ook `~/.env-newsbot` (oud bestand)
- Gmail app wachtwoord met spaties veroorzaakte bash parsing errors
- `mail` commando niet geinstalleerd op server (alerts werkten nooit)
- `health-check.sh` checkte op `OPENROUTER_API_KEY` en `GMAIL_ADDRESS` als "required" vars (verouderd)

**Doorgevoerde fixes:**

1. **Systemd service:** `EnvironmentFile` gewijzigd van `~/.env-newsbot` naar `/home/<user>/apps/ai-news-bot/.env`
2. **Alert script:** Source pad gewijzigd naar project `.env`
3. **Systemd herlaad:** `daemon-reload` + handmatige testrun
4. **Opruiming:** `.env-newsbot` hernoemd naar `.env-newsbot.old`
5. **Health check:** Required vars bijgewerkt naar actuele provider (Claude/Resend)
6. **CLAUDE.md:** Verouderde OpenRouter/Gmail referenties opgeschoond
7. **Failsafes:** Env-consistentie check toegevoegd aan health-check en pre-deploy scripts

**Geleerde lessen - Failsafes:**

1. **Single Source of Truth voor env:** Nooit twee env bestanden naast elkaar houden
2. **Systemd EnvironmentFile + load_dotenv() conflict:** `load_dotenv()` overschrijft geen bestaande vars - systemd wint altijd
3. **Health check moet actuele stack reflecteren:** Bij provider/notifier wijzigingen ook health check updaten
4. **Configuratie-drift detectie:** Periodiek checken of server config matcht met code verwachtingen

**Git Status:**

- Branch: `main`
- Commit: `a3b6746` - fix: alert script source project .env instead of deprecated .env-newsbot

---

## 2026-02-12: Feed Expansion - Social Media & Deep Tech Bronnen (30 min)

**Context:** Grote uitbreiding van RSS bronnen voor bredere AI-dekking: MKB tools, PKM, creativiteit, deep tech research en kritische stemmen. Twitter/X API te duur ($200/mo), daarom migratie naar Bluesky en Mastodon social feeds.

**Doorgevoerde wijzigingen:**

1. **Nieuwe RSS Feeds (14 feeds toegevoegd)**
   - **MKB/Implementatie:** Ben's Bites (dagelijkse AI roundup), n8n Blog (automation workflows)
   - **PKM/Productiviteit:** Ness Labs (digital tools, productivity)
   - **Creativiteit:** Replicate Blog (creative AI tools, image/video gen)
   - **Deep Tech/Research:**
     - Sebastian Raschka (ML research, LLM papers)
     - Eugene Yan (applied ML, production systems)
     - Chip Huyen (ML systems design)
     - EleutherAI (open-source LLMs, research)
     - The Gradient (AI research magazine)
     - Jay Alammar (visual ML explanations)
   - **Kritisch/Ethiek:**
     - AI Snake Oil (Narayanan & Kapoor, kritische AI analyse)
     - Gary Marcus (AGI skepticus)
     - Tech Policy Press (AI policy, regulering)
     - Montreal AI Ethics Institute (AI ethics research)

2. **Social Media Feeds (8 feeds toegevoegd)**
   - **Bluesky (5 feeds):**
     - ML Curator (@mlcurator.bsky.social) - gecureerde ML nieuws
     - Yann LeCun (@ylecun.bsky.social) - Meta AI Chief
     - Emily Bender (@emilymbender.bsky.social) - computational linguistics
     - Margaret Mitchell (@mmitchell.bsky.social) - ethical AI
     - Paper Skygest (@paperskygest.bsky.social) - arXiv papers
   - **Mastodon (3 hashtag feeds):**
     - #AI op mastodon.social
     - #MachineLearning op mastodon.social
     - #LLM op mastodon.social

3. **Technische Implementatie**
   - Bluesky: DID-based profile URLs (stabiel, geen handle-afhankelijkheid)
   - Mastodon: Hashtag feeds via standaard RSS 2.0 URLs
   - Geen code wijzigingen nodig - bestaande `NewsFetcher` parsed social feeds direct
   - Categorisatie: MKB, PKM, Creativiteit, Deep Tech, Kritisch (voor filtering)

**Belangrijke Beslissingen:**

- **Twitter/X afgewezen:** $200/mo API kosten te hoog, scraping fragiel, Nitter dood
- **Bluesky gekozen:** Gratis API, betrouwbaar, veel AI researchers migreren hiernaartoe
- **Mastodon hashtags:** Breed maar mogelijk lawaaierig, evalueren na 1-2 weken
- **DID URLs voor Bluesky:** Stabiel bij handle changes (bijv. `did:plc:ragtjsm2j2vknwkz3zp4oxrd`)
- **Geen filtering code:** Laat Stage 1 selectie prompt de kwaliteit bepalen

**Feed Overzicht:**

```
Totaal international feeds: 33 → 55 (+67%)
  - RSS feeds: 47
  - Social feeds: 8 (5 Bluesky + 3 Mastodon)
```

**Rationale per Categorie:**

- **MKB:** Ben's Bites heeft grote community, n8n is praktisch (workflows)
- **PKM:** Ness Labs past bij Frank's PKM focus (Obsidian, second brain)
- **Creativiteit:** Replicate voor visual AI tools (image gen, video, etc.)
- **Deep Tech:** Research papers en production ML (Raschka, Yan, Huyen = authorities)
- **Kritisch:** Balans tegen hype - Gary Marcus, AI Snake Oil, ethics instituten

**Social Feed URLs:**

Bluesky:
```
https://bsky.app/profile/{did}/rss
```

Mastodon:
```
https://mastodon.social/tags/{hashtag}.rss
```

**Test Strategie:**

1. Eerste productie run monitoren (morgen 07:00):
   - Check RSS parse errors in logs
   - Controleer database `rss_health` tabel op failures
   - Review geselecteerde items: komen nieuwe feeds door Stage 1?

2. Na 1-2 weken evalueren:
   - Mastodon hashtags: noise level (te veel irrelevante posts?)
   - Bluesky feeds: kwaliteit vs overlap met bestaande bronnen
   - Deep tech feeds: te academisch of goed voor doelgroep?
   - Social feeds: duplicate detection werkt goed genoeg?

**Git Status:**

- Branch: `main`
- Laatste commit: `aa73e06` - fix: clean up 18 broken RSS feeds and add is_active check to fetcher
- Working tree: Clean (sources.yaml commit bevatte feed expansion)
- Uncommitted: LOGBOEK.md (deze sessie)

**Volgende Stappen:**

- Monitoring eerste run met nieuwe feeds (parse errors?)
- Evaluatie na 1 week: noise level Mastodon hashtags
- Eventueel meer Bluesky accounts toevoegen op basis van kwaliteit
- Overwegen: Bluesky lists (gecureerde AI lists) als alternatief voor individuele accounts

**Totaal: 30 min**

---

## 2026-01-27: Developer Tooling - Preview Mode, Health Check & Pre-Deploy Validation (95 min)

**Context:** Implementatie van developer tooling voor veiligere deployments en snellere ontwikkelcyclus.

**Doorgevoerde wijzigingen:**

1. **Obsidian Filename Sanitization**
   - `src/obsidian/uri_builder.py`: Nieuwe `sanitize_filename()` functie
   - Vervangt illegale karakters: `/\:*?"<>|` → underscores
   - Handhaaft maximale lengte (255 karakters)
   - Voorkomt Obsidian file creation errors

2. **Pre-Deployment Validation Script**
   - `scripts/pre-deploy-check.sh`: 7 geautomatiseerde checks
   - Git status audit (uncommitted files, untracked files)
   - Database model sync check (models.py vs gebruikers)
   - Breaking changes scan (nullable=False, NOT NULL)
   - Import validation (Python syntax check)
   - Dependencies check (requirements.txt sync)
   - Exit code support voor CI/CD integration
   - Kleurgecodeerde output (groen/geel/rood)

3. **Server Health Check Dashboard**
   - `scripts/health-check.py`: 7 diagnostics voor production monitoring
   - System checks: Database, RSS feeds, recent runs, AI summaries
   - Cost tracking: Last 7 days, provider/model breakdown
   - RSS health: Failure rates, disabled feeds
   - Performance: Average tokens per run
   - Exit codes: 0=healthy, 1=warnings, 2=critical
   - Quiet mode voor scripting (`--quiet` flag)

4. **Dry-Run/Preview Mode**
   - `main.py`: Nieuwe `--preview` flag toegevoegd
   - Stage 1 + Stage 2 processing zonder notificaties
   - Saves output naar `preview_newsletter.html`
   - Browser auto-open voor visual inspection
   - Volledige database tracking (run ID, costs, summaries)
   - Gebruik: `python main.py --preview` voor snelle prompt testing

**Belangrijke Beslissingen:**

- Pre-deploy check voorkomt repeat van deployment chaos (zie 2026-01-04 retrospective)
- Health check gebruikt database queries voor accuratere metrics dan log parsing
- Preview mode schrijft WEL naar database (consistency met production)
- Sanitization alleen voor filenames, niet voor URL encoding (UX priority)

**Test Resultaten:**

- Pre-deploy check: 7/7 checks passed lokaal
- Health check: Successvol op lokale database (17 runs, 279 summaries)
- Preview mode: Newsletter gegenereerd in 2:13 min (15 items)
- Obsidian links: Correcte filename sanitization (test passed)

**Technische Details:**

Pre-deploy check scans:
```bash
# Git status
git status --short

# Model sync
git diff src/database/models.py | grep "class \|Column"

# Breaking changes
git diff | grep -E "nullable=False|NOT NULL|ForeignKey"

# Import test
python -c "from src.database.models import AISummary"
```

Health check metrics:
```
Database: OK (279 summaries across 17 runs)
RSS Feeds: 2 disabled, 51 total
Recent Activity: Last run 1 day ago
Cost (7d): $0.58 (claude-3.5-sonnet-20241022)
```

**Documentatie:**

- `scripts/README.md`: Nieuwe sectie voor pre-deploy en health check
- Usage examples en exit code documentatie
- Integration met CI/CD workflows

**Git Status:**

- Branch: `main`
- Commits:
  - `af33e58` - feat: add dry-run/preview mode for newsletter testing
  - `2588fea` - fix: suppress stdout logging in database health check
  - `8adb568` - fix: suppress logging in health check database queries
  - `42b4533` - fix: correct package import name and database init in health check
  - `b9b7d8f` - feat: add server health check dashboard
- Uncommitted: LOGBOEK.md (deze sessie)

**Volgende Stappen:**

- Integreren pre-deploy check in Forgejo Actions workflow
- Health check in systemd timer voor daily monitoring
- Alerting bij health check failures (email/webhook)
- Preview mode gebruiken voor prompt iteratie cycles

**Totaal: 95 min**

---

## 2026-01-14: Database Sync Throttle - Rapid-Fire Preventie (10 min)

**Context:** Script fix om te voorkomen dat database sync binnen 12 uur opnieuw draait, als bescherming tegen onbedoelde rapid-fire syncs.

**Doorgevoerde wijzigingen:**

1. **scripts/sync-database.sh - Throttle Logica**
   - 12-uur throttle toegevoegd met `.last-sync` timestamp bestand
   - Controleert bij elke run of laatste sync minder dan 12 uur geleden was
   - Logt throttle events naar `logs/db-sync.log`
   - Timestamp bestand: `data/.last-sync` (Unix timestamp)

2. **CLAUDE.md - Documentatie Update**
   - Sync throttle beschrijving toegevoegd aan Database Sync sectie
   - Throttle override uitleg: verwijder `.last-sync` bestand
   - Manual sync procedure gedocumenteerd

**Rationale:**

- Launchd StartOnMount kan tot onbedoelde syncs leiden bij herhaald opstarten
- 12-uur window voorkomt database corruption door overlappende syncs
- Throttle file in `data/` directory (samen met database)

**Technische Details:**

Throttle check logic:
```bash
if [ -f "$THROTTLE_FILE" ]; then
    last_sync=$(cat "$THROTTLE_FILE")
    now=$(date +%s)
    diff=$((now - last_sync))
    if [ $diff -lt $THROTTLE_SECONDS ]; then
        hours_left=$(((THROTTLE_SECONDS - diff) / 3600))
        log_message "THROTTLE: Last sync was $((diff / 3600))h ago. Wait ${hours_left}h more."
        exit 0
    fi
fi
```

**Test:**
- Dry-run uitgevoerd: throttle logica werkt correct
- `.last-sync` bestand wordt correct aangemaakt en gerespecteerd
- Logging naar `logs/db-sync.log` werkt

**Git Status:**

- Branch: `main`
- Commits:
  - `066455b` - feat: add 12-hour throttle to database sync script
  - (uncommitted) CLAUDE.md documentation update
- Pushed naar: origin en github (script commit)

**Volgende Stap:**

- Monitoring van throttle events in `logs/db-sync.log`
- Eventueel throttle window aanpassen op basis van gebruik

---

## 2026-01-04: Obsidian Integratie - Newsletter met Deep Links

**Context:** Implementatie van Obsidian deep links in nieuwsbrief voor directe opslag van artikelen in Obsidian vault. Newsletter workflow aangepast om database-first te werken met structured summaries.

**Doorgevoerde wijzigingen:**

1. **Bug Fixes**
   - `src/news/generator.py:239-240`: Runtime logging fix (None handling)
   - `src/news/generator.py:245-290`: Nieuwe `get_digest_from_run()` functie
   - `src/news/summary_parser.py:185-228`: Nieuwe `format_summaries_to_markdown()` functie

2. **Obsidian URI Builder Verbeteringen**
   - `src/obsidian/uri_builder.py:65`: Bestandsnamen niet meer URL-encoded (leesbare namen)
   - `src/obsidian/uri_builder.py:83-99`: Dynamische frontmatter met `onderwerp` field
   - Frontmatter `onderwerp` bevat nu `summary.why_matters` waarde
   - File path: `4 - Resources/AI/{title}` met normale tekst

3. **Newsletter Builder Workflow**
   - `generate_test_newsletter.py`: Volledig herschreven voor database-driven workflow
   - Gebruikt nu `build_newsletter_html()` voor Obsidian links
   - Inline HTML template (geen dependency op EmailNotifier)
   - Test output: 16-17 Obsidian links per newsletter

4. **Test Tooling**
   - `test_single_obsidian_link.py`: Debug tool voor individuele Obsidian URIs
   - Toont decoded file path en content preview
   - Verificatie van frontmatter formatting

**Technische Details:**

**Obsidian URI Format:**
```
obsidian://new?vault=frankopedia
&file=4%20-%20Resources%2FAI%2F{title}
&content={encoded_markdown}
&silent=true
```

**Frontmatter Voorbeeld:**
```yaml
---
aliases:
context:
  - "[[Thema - Artificial Intelligence]]"
type:
  - "[[Artikel]]"
onderwerp: AI-systemen krijgen onterecht menselijke eigenschappen toegeschreven
---
```

**Newsletter Workflow:**
1. `generate_news_digest_from_sources()` → returns `run_id`
2. Summaries opgeslagen in database met structured fields
3. `build_newsletter_html(run_id)` → genereert HTML met Obsidian URIs
4. Browser preview met werkende `[Obs]` links

**Belangrijke Beslissingen:**

- Database-first workflow: Digest tekst wordt niet meer direct gebruikt
- Obsidian URIs gebouwd uit database summaries voor consistentie
- Bestandsnamen leesbaar (geen URL encoding) voor betere UX
- `onderwerp` frontmatter field bevat "why matters" voor filtering in Obsidian
- Test scripts voor snelle verificatie zonder volledige newsletter run

**Test Resultaten:**

- Run #3: 19 items geselecteerd, 17 summaries opgeslagen (1 URL mismatch)
- Run #4: 19 items geselecteerd, 17 Obsidian links gegenereerd
- Run #5: 16 items geselecteerd, 16 Obsidian links gegenereerd
- Bestandsnamen: Correct decoded (bv. "Google lanceert Gemini 3 Flash model")
- Frontmatter: `onderwerp` field correct gevuld met why_matters

**Code Files Aangepast:**

- `src/news/generator.py`: Runtime fix + `get_digest_from_run()` helper
- `src/news/summary_parser.py`: `format_summaries_to_markdown()` helper
- `src/obsidian/uri_builder.py`: Dynamische frontmatter + bestandsnaam fix
- `generate_test_newsletter.py`: Database-driven workflow
- `test_single_obsidian_link.py`: Nieuw debug tool

**Git Status:**

- Branch: `main`
- Working tree: Uncommitted changes (dit logboek + code fixes)
- Next: Commit en push naar origin/github

**Volgende Stappen:**

- Testen Obsidian links in echte newsletter (klik + opslag)
- Verificatie frontmatter in Obsidian vault
- Evaluatie `onderwerp` field voor filtering/querying
- Eventueel categorisatie toevoegen aan frontmatter

---

## 2025-12-24: Geautomatiseerde Database Synchronisatie

**Context:** Database sync van server naar lokaal voor development, geïmplementeerd via launchd agent.

**Doorgevoerde wijzigingen:**

1. **Database Sync Script**
   - Aangemaakt: `scripts/sync-db.sh`
   - Functionaliteit: SCP download van `newsbot.db` van Hetzner server
   - Lokaal pad: `data/newsbot.db` (overschrijft bestaande database)
   - SSH: Via `~/.ssh/<deploy_key>` key

2. **Launchd Agent**
   - Aangemaakt: `~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot-sync.plist`
   - Schedule: Dagelijks 08:00 uur
   - Automatische start bij login via `launchctl load`
   - Logs: `~/Library/Logs/ai-news-bot-sync.log`

3. **Documentatie**
   - CLAUDE.md: Database sync sectie toegevoegd aan server deployment
   - TROUBLESHOOTING.md: Nieuwe troubleshooting guide aangemaakt
     - Database sync debugging (permissions, SSH, launchd)
     - Server deployment issues
     - Common errors met oplossingen

**Technische Details:**

- SCP commando: `scp -i ~/.ssh/<deploy_key> <user>@<SERVER_IP>:/home/<user>/apps/ai-news-bot/data/newsbot.db data/`
- Launchd: `StartCalendarInterval` met Hour=8, Minute=0
- Executable bit: `chmod +x scripts/sync-db.sh`
- Launchd load: `launchctl load ~/Library/LaunchAgents/nl.frankmeeuwsen.ai-news-bot-sync.plist`

**Workflow:**

1. Server draait daily newsletter om 07:00 (systemd timer)
2. Lokale sync om 08:00 (launchd agent)
3. Development met verse productie data

**Belangrijke Beslissingen:**

- Launchd agent boven cron voor macOS compatibility
- Overschrijven lokale database acceptabel (dev environment)
- SSH key hergebruik (deploy key) voor consistency
- Eén uur delay tussen newsletter run en sync

**Git Status:**

- Branch: `main`
- Laatste commit: `fd25bd0` - feat: add automated daily database sync from server to local
- Working tree: 2 uncommitted files (CLAUDE.md, TROUBLESHOOTING.md)

**Open Items:**

- Testen eerste sync morgen 08:00
- Monitoring van sync failures (launchd logs)
- Optioneel: Bidirectionele sync voor feedback data

---

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
- Server: `<user>@<SERVER_IP>`
- Deploy pad: `/home/<user>/apps/ai-news-bot`
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
   - Host: `<SERVER_IP>` (Hetzner)
   - User: `frank` (sudo)
   - OS: Ubuntu 20.04 (Python 3.8)
   - Locatie: `/home/<user>/apps/ai-news-bot`

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

## 2025-12-28: Prompt Refactor - B1 Nederlands & Smart Brevity

**Context:** Prompts waren in Engels en te technisch. Refactor naar B1 Nederlands met duidelijkere Smart Brevity instructies voor betere output kwaliteit.

**Doorgevoerde wijzigingen:**

1. **Stage 1: Nieuwsselectie**
   - Volledig vertaald naar Nederlands
   - Duidelijke prioritering: 60% hard news (doorbraken, launches, beleid)
   - Uitgebreide kwaliteitscriteria met voorbeelden
   - Betere spreiding over 7 categorieën (modellen, producten, onderzoek, etc.)
   - Expliciete "vermijd" sectie: dubbele berichtgeving, marketing fluff, oude nieuws

2. **Stage 2: Samenvatting**
   - Vertaald naar B1 Nederlands schrijfniveau
   - Concreter voorbeeld met cijfers en feiten
   - Meer nadruk op meetbare details (percentages, aantallen, tijdslijnen)
   - Nederlandse context waar relevant
   - Actieve taal, stellige schrijfstijl, geen modaalwoorden

3. **Smart Brevity Format Verbeteringen**
   - Structuur per item: Kop → Waarom belangrijk → Grote plaatje → Details (3 bullets) → Volgende stap
   - Koppen: max 10 woorden, actieve werkwoorden
   - Details: begin bullets met cijfers waar mogelijk
   - Vertaal jargon direct ("language model" → "taalmodel")

**Rationale:**

- B1 Nederlands maakt output toegankelijker voor Nederlandse doelgroep
- Concrete cijfers en feiten geven meer waarde dan vage beschrijvingen
- Duidelijkere instructies = consistentere AI output
- Focus op scanbaarheid: bullets boven alinea's

**Git Status:**

- Branch: `main`
- Laatste commit: `d6c0340` - refactor: improve prompt clarity with Dutch B1 and Smart Brevity format
- Working tree: Uncommitted changes (dit logboek)
- Pushed naar: origin (dutchstack) en github

**Volgende Stappen:**

- Testen nieuwe prompts met volgende newsletter run (morgen 07:00)
- Evalueren output kwaliteit: meer cijfers, betere koppen, duidelijkere structuur
- Eventueel fine-tunen op basis van eerste resultaten

---

## 2025-12-28: Resend Email Provider & Forgejo SSH Fix

**Context:** Gmail SMTP rejection na 2 weken stabiele werking. Migratie naar Resend voor betrouwbaardere email delivery. Forgejo SSH authenticatie gefixed met nieuwe ED25519 key.

**Doorgevoerde wijzigingen:**

1. **Resend Email Provider**
   - Aangemaakt: `src/notifiers/resend_notifier.py`
   - Config optie: `notifications.email_provider` (gmail/resend)
   - Dependencies: `resend>=0.8.0` in requirements.txt
   - Environment: `RESEND_API_KEY`, `RESEND_FROM`, `EMAIL_TO`
   - Voordelen: 99%+ deliverability, 100 emails/dag gratis, custom domein support

2. **Forgejo SSH Key Fix**
   - Probleem: `git.dutchstack.nl` SSH authenticatie faalde (Permission denied)
   - Oorzaak: Server upgrade gisteren, oude ED25519 key werkte niet meer
   - Oplossing: Nieuwe ED25519 key gemaakt (`id_ed25519_forgejo`)
   - SSH config: Port 2222, IdentitiesOnly yes
   - Key naam in Forgejo: `frank@macbook-ai-news-bot-forgejo`
   - Getest: Lokaal en server kunnen nu beide git pull van Forgejo

3. **Email Provider Selection**
   - main.py: Dynamische notifier selectie op basis van config
   - Backward compatible: Gmail blijft werken als fallback
   - Test script: `test_resend.py` voor lokaal testen

4. **Documentatie**
   - README.md: Resend setup guide toegevoegd (Option 1: Recommended)
   - Gmail downgraded naar Option 2 met waarschuwing over betrouwbaarheid
   - Environment variabelen gedocumenteerd voor beide providers

**Technische Details:**

- Resend API: Transactional email service, professioneler dan SMTP
- SSH Port: 2222 (niet standaard 22) voor Forgejo
- Key type: ED25519 (moderner dan RSA, korter, sneller)
- Config path: `~/.ssh/config` (lokaal + server)

**Belangrijke Beslissingen:**

- Resend als recommended provider (Gmail = testing only)
- Nieuwe SSH key ipv oude key debuggen (sneller, cleaner)
- Port 2222 expliciet in SSH config (was impliciet in oude setup)
- Test script voor snelle verificatie zonder volledige nieuwsbrief run

**Deployment Status:**

- Code gepulled naar server: commit d877b38 (Resend integratie)
- Dependencies geïnstalleerd: resend package
- Service herstart: ai-news-bot.timer
- Volgende run: Maandag 29 dec 06:00 UTC (07:00 Amsterdam)
- Forgejo Actions: Nu werkend (SSH key gefixed)

**Git Status:**

- Branch: `main`
- Laatste commit: `d877b38` - feat: add Resend email provider
- Working tree: Uncommitted changes (dit logboek)
- SSH keys: Nieuwe `id_ed25519_forgejo` in gebruik

**Open Items:**

- Monitoring eerste Resend delivery morgenochtend
- Eventueel Gmail variabelen verwijderen uit server .env
- Domein verificatie in Resend (optioneel, voor custom domein)

---

Last updated: 2025-12-28
