# AI News Bot - TODO & Roadmap

## High Priority

### ✍️ Content & Writing Quality

- [ ] **Prompt Verbetering via Leerproces**
  - Analyseer opgehaalde → gecureerde → gelezen nieuwsitems
  - Identificeer patronen in succesvolle vs overgeslagen items
  - Automatisch prompt tuning op basis van feedback
  - A/B testing van verschillende prompt varianten
  - Logging van prompt effectiviteit (selectie accuracy)

- [ ] **Template Nieuwsberichten Verbeteren**
  - Duidelijke one-liner direct onder de titel (the "why it matters")
  - Inspiratie: Axios "Why it matters" sectie
  - Subheadline moet standalone readable zijn
  - Test verschillende formaten met gebruikers

- [ ] **Axios-stijl Nieuwsteksten**
  - Meer bulletpoints waar mogelijk
  - "Smart Brevity" principes toepassen:
    - Strong subject lines
    - "Why it matters" one-liner
    - Bullet points voor details
    - "The big picture" context
    - "What's next" of "What to watch"
  - Kortere paragrafen (max 3 zinnen)
  - Visuele hiërarchie met headers/bullets

### 🧪 Testing & Development

- [ ] **Testmodus voor Prompts**
  - Dry-run mode: genereer nieuwsbrief zonder te versturen
  - Preview in terminal of browser
  - Output naar bestand (HTML/Markdown)
  - Command-line flag: `--dry-run` of `--preview`
  - Handig voor prompt iteratie en testing
  - Optie om specifieke taal te testen zonder andere te versturen

- [ ] **Raycast Integratie voor TODO Beheer**
  - Maak Raycast script command voor snelle TODO toevoegingen
  - Gebruik headless Claude via MCP/API voor intelligente TODO parsing
  - Features:
    - Natuurlijke taal input: "voeg toe: test nieuwe prompt variant"
    - Automatische categorisatie (High/Medium/Low priority)
    - Juiste sectie detectie (Content/Testing/Logging/etc.)
    - Direct committen naar git met relevante message
  - Workflow: Raycast → headless Claude → parse input → edit TODO.md → git commit
  - Alternatief: Simpele template-based script zonder AI voor snelheid

### 🔧 Logging & Monitoring
- [ ] **RSS Feed Health Check**
  - Detecteer niet-bestaande/broken RSS feeds tijdens fetch
  - Log welke feeds falen en waarom
  - Automatisch verwijderen uit sources.yaml na X achtereenvolgende failures
  - Notificatie naar admin over gefaalde feeds

- [ ] **End-of-Run Rapport**
  - Echo eindrapport naar console met:
    - Gebruikte LLM provider en model
    - Totaal aantal opgehaalde nieuwsitems
    - Aantal geselecteerde items (per taal)
    - Aantal verzonden nieuwsbrieven
    - Statistieken per notificatie methode (geslaagd/gefaald)
    - Runtime en kosten (indien beschikbaar)

- [ ] **Kosten Tracking per Editie**
  - Ophalen van daadwerkelijke kosten via OpenRouter API
  - API endpoint: `/api/v1/generation` response bevat `usage` object met costs
  - Logging van kosten per stage (Stage 1 + Stage 2)
  - Totaalkosten per nieuwsbrief editie
  - Cumulatieve kosten tracking over tijd
  - Export naar CSV voor accounting/analyse

### 🤖 Machine Learning & Personalisatie

- [ ] **Data Opslag voor Fine-tuning**
  - Opslaan van alle opgehaalde nieuwsitems in database/vector store
  - Metadata: timestamp, source, language, selected (yes/no)
  - Embeddings genereren voor semantische zoek
  - Export functie naar trainingsdata formaat

- [ ] **Feedback Mechanisme**
  - Thumbs up/down knoppen in nieuwsbrief (HTML versie)
  - Feedback API endpoint om votes te registreren
  - Opslag van user preferences per nieuwsitem
  - Analytics dashboard voor feedback trends

- [ ] **Serendipity Algoritme**
  - Analyseer historische klik/feedback data
  - Identificeer gebruikersvoorkeuren en patterns
  - Injecteer X% "surprise" items die:
    - Buiten normale categorieën vallen
    - Trending zijn in bredere AI community
    - Hoge quality score hebben maar off-topic
  - Voorkom filter bubbles door diversiteit te forceren
  - A/B testing voor optimale serendipity ratio

## Medium Priority

### 📊 Analytics & Insights
- [ ] Dashboard met statistieken over:
  - Meest populaire bronnen
  - Engagement per categorie
  - Click-through rates (indien trackable)
  - User retention metrics

### 🔄 Workflow Verbeteringen
- [ ] RSS feed caching mechanisme (vermijd dubbele fetches)
- [ ] Rate limiting voor RSS feeds
- [ ] Retry logic met exponential backoff
- [ ] Parallelle RSS feed fetching (asyncio)

### 📬 Email Interactiviteit
- [ ] **Obsidian x-success URI voor Feedback**
  - Voeg x-success URI toe aan email template voor thumbs up/down
  - Opent Obsidian note met pre-filled feedback data
  - URI format: `obsidian://x-callback-url/open?vault=VaultName&file=Feedback&x-success=...`
  - Logs feedback naar Obsidian vault voor analyse

- [ ] **Click Tracking in Email**
  - Bijhouden welke nieuwslinks worden aangeklikt
  - Unieke tracking parameters per link in email
  - Analytics endpoint om clicks te registreren
  - Koppel clicks aan user profiles voor personalisatie
  - Privacy-vriendelijk: geen third-party trackers

### 💾 Database Sync Verbeteringen
- [ ] **Betere Failure Notificaties**
  - Extra regel in macOS notificatie met specifieke error message
  - Log waarom sync gefaald is (SSH timeout, bestand niet gevonden, etc.)
  - Maak errors actionable voor troubleshooting

- [ ] **Delayed Startup bij Reboot**
  - Sync moet niet direct bij opstarten draaien
  - Wacht 5-10 minuten na boot voordat eerste sync start
  - Voorkomt race conditions met netwerk/SSH initialisatie
  - Gebruik `StartCalendarInterval` + delay ipv immediate `StartOnMount`

### 🌍 Internationalisatie
- [ ] Per-taal prompt templates (nu: generieke template)
- [ ] Taal-specifieke news categorieën
- [ ] Timezone-aware scheduling per taal

## Low Priority

### 🎨 UI/UX
- [ ] Web interface voor configuratie
- [ ] Preview functie voor nieuwsbrief
- [ ] Template editor voor prompts

### 🔐 Security & Privacy
- [ ] GDPR compliance audit
- [ ] User data encryption
- [ ] Opt-in/opt-out mechanisme per categorie

## Research / Future Ideas

- [ ] Multi-modal nieuwsanalyse (images, video thumbnails)
- [ ] Sentiment analysis op nieuwsitems
- [ ] Trend detection over tijd
- [ ] Collaborative filtering tussen gebruikers
- [ ] RSS feed discovery (auto-suggest nieuwe bronnen)
- [ ] AI-gegenereerde nieuwssamenvattingen in audio formaat

---

## Implementation Notes

**Serendipity Algoritme Details:**
```python
# Pseudo-code voor serendipity
def select_with_serendipity(items, user_profile, serendipity_ratio=0.15):
    # 85% based on user preferences
    relevant_items = rank_by_relevance(items, user_profile)
    selected = relevant_items[:int(len(items) * (1 - serendipity_ratio))]

    # 15% serendipity (diverse, surprising, high-quality)
    surprise_items = rank_by_novelty(items, user_profile)
    selected += surprise_items[:int(len(items) * serendipity_ratio)]

    return selected
```

**RSS Health Check:**
- Track failure count per feed in separate JSON
- Auto-disable after 3 consecutive failures
- Weekly report van disabled feeds
- Re-check disabled feeds elke maand

**Feedback Loop:**
- Thumbs up/down → update embedding weights
- Implicit feedback: open rate, click-through
- Negative feedback → reduce similar items
- Positive feedback → boost similar categories

---

Last updated: 2025-12-27
