# agents.md
> Deze file wordt automatisch gesynchroniseerd met CLAUDE.md
> Laatste sync: 2025-12-09 09:08

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

Last updated: 2025-12-09
