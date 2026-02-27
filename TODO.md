# AI News Bot - TODO & Roadmap

## Afgerond

<details>
<summary>Klik om afgeronde items te zien</summary>

- [x] **Escape Ongeldige Karakters in Obsidian Bestandsnamen** (2026-01-27)
- [x] **Pre-Deployment Checklist & Validation** (2026-01-27) - `scripts/pre-deploy-check.sh`
- [x] **Server Health Check Dashboard** (2026-01-27) - `scripts/health-check.sh`
- [x] **Testmodus voor Prompts** (2026-01-27) - `--dry-run`, `--preview`, preview server
- [x] **RSS Feed Health Check** - Auto-disable na 3 consecutive failures, `is_active` check in fetcher, database tracking
- [x] **Axios-stijl Nieuwsteksten & Template Verbetering** - Stage 2 prompt herschreven naar Smart Brevity format (Dutch B1)
- [x] **RSS Feed Caching** - 36-uur cache met GUID/link deduplicatie + newsletter deduplicatie
- [x] **Preview Functie voor Nieuwsbrief** - Preview server + dry-run mode
- [x] **Database Sync Throttle** - 12-uur throttle voorkomt rapid-fire syncs bij reboot

</details>

## High Priority

### Deployment & Server Operations

- [ ] **Deployment Smoke Tests**
  - Automated test suite die na deployment draait op server
  - Tests: imports, database connection, model/schema match, env vars, dependencies
  - Exit code 0 = success, non-zero = rollback advised
  - Integreer in Forgejo Actions workflow

### Content & Writing Quality

- [ ] **Prompt Verbetering via Leerproces**
  - Analyseer opgehaalde vs gecureerde vs gelezen nieuwsitems
  - Identificeer patronen in succesvolle vs overgeslagen items
  - A/B testing van verschillende prompt varianten
  - Logging van prompt effectiviteit (selectie accuracy)

### Logging & Monitoring

- [x] **Wekelijks Rapport Email** (2026-02-27)
  - Script: `scripts/weekly-report.py` (--dry-run voor test)
  - Inhoud: newsletter runs, database stats, RSS health, kosten, git commits
  - Schedule: zaterdagochtend 08:00 via systemd timer op server

- [ ] **NewsletterRun Tracking Completeren**
  - `items_selected`, `runtime_seconds`, `stage1_tokens`, `stage2_tokens`, `total_cost` worden niet ingevuld door generator
  - Weekrapport toont deze velden als 0/leeg
  - Fix nodig in `src/news/generator.py` om deze waarden na elke run op te slaan

### Machine Learning & Personalisatie

- [ ] **Feedback Mechanisme**
  - Thumbs up/down knoppen in nieuwsbrief (HTML versie)
  - Feedback API endpoint om votes te registreren
  - Opslag van user preferences per nieuwsitem

- [ ] **Serendipity Algoritme**
  - Injecteer X% "surprise" items buiten normale categorieeen
  - Voorkom filter bubbles door diversiteit te forceren
  - Vereist: feedback mechanisme eerst implementeren

## Medium Priority

### Analytics & Insights
- [ ] Dashboard met statistieken (populaire bronnen, engagement per categorie)

### Workflow Verbeteringen
- [ ] Rate limiting voor RSS feeds
- [ ] Retry logic met exponential backoff
- [ ] Parallelle RSS feed fetching (asyncio)

### Email Interactiviteit
- [ ] **Obsidian x-success URI voor Feedback**
  - Thumbs up/down via Obsidian x-callback-url in email template
- [ ] **Click Tracking in Email**
  - Privacy-vriendelijk bijhouden welke links worden aangeklikt

### Database Sync Verbeteringen
- [ ] **Betere Failure Notificaties**
  - Specifieke error messages in macOS notificaties
  - Actionable troubleshooting info

### Internationalisatie
- [ ] Per-taal prompt templates
- [ ] Taal-specifieke news categorieen

### Infrastructure & Dependencies
- [ ] **Dependency Mapping & Overzicht**
  - Visueel overzicht van alle componenten (Hetzner, Cloudflare, Forgejo, Resend)
  - Mermaid diagram + tabel met kritieke configuratie

## Low Priority

### UI/UX
- [ ] Web interface voor configuratie
- [ ] Template editor voor prompts

### Security & Privacy
- [ ] GDPR compliance audit
- [ ] Opt-in/opt-out mechanisme per categorie

## Research / Future Ideas

### Infrastructure Simplificatie
- [ ] **Self-Hosted Stack Research**
  - Email: Postfix/Dovecot vs Resend
  - Monitoring: Uptime Kuma / Grafana
  - Trade-offs: betrouwbaarheid, onderhoud, kosten

### AI & ML
- [ ] Multi-modal nieuwsanalyse (images, video thumbnails)
- [ ] Sentiment analysis op nieuwsitems
- [ ] Trend detection over tijd
- [ ] RSS feed discovery (auto-suggest nieuwe bronnen)
- [ ] AI-gegenereerde nieuwssamenvattingen in audio formaat

---

Last updated: 2026-02-27
