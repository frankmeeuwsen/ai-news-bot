# Dry-Run / Preview Mode

## Overzicht

De testmodus (dry-run/preview mode) genereert nieuwsbrieven **zonder deze te versturen**, ideaal voor:
- Prompt iteratie en testing
- Content review voordat je verstuurt
- Testen van nieuwe RSS feeds
- Template wijzigingen verifiëren

## Gebruik

### Basis Dry-Run

```bash
# Genereer preview voor alle talen
python main.py --dry-run

# Preview voor specifieke taal
python main.py --dry-run --language nl

# Preview zonder browser (alleen file opslaan)
python main.py --dry-run --no-browser
```

### Output Locatie

Standaard worden previews opgeslagen in `./preview/`:

```
preview/
├── newsletter_preview_nl_30_20260127_110554.html
├── newsletter_preview_en_31_20260127_113022.html
└── ...
```

Bestandsnaam format: `newsletter_preview_{language}_{run_id}_{timestamp}.html`

### Custom Output Directory

```bash
python main.py --dry-run --output-dir /tmp/previews
```

## Features

### 1. Preview Banner

Elk preview bestand heeft een gele banner bovenaan met:
- **Language:** Taal van de nieuwsbrief
- **Run ID:** Database run ID (voor tracing)
- **Generated:** Timestamp van generatie
- **Notice:** "This is a preview - no notifications were sent"

### 2. Styled HTML

- Complete standalone HTML document
- Responsive design (max-width: 800px)
- Professionele styling (Apple system fonts)
- Newsletter content in witte card met box-shadow
- Geen external dependencies (volledig offline viewbaar)

### 3. Browser Auto-Open

Standaard opent de preview automatisch in je browser. Uitschakelen met:

```bash
python main.py --dry-run --no-browser
```

## Workflow Voorbeelden

### Content Iteratie

```bash
# 1. Wijzig prompt in prompts/stage2_summarization.md
nano prompts/stage2_summarization.md

# 2. Test met dry-run
python main.py --dry-run --language nl

# 3. Review in browser, itereer

# 4. Wanneer tevreden: normale run
python main.py
```

### Template Testing

```bash
# Test template wijzigingen zonder te versturen
python main.py --dry-run --language en

# Vergelijk output met vorige versie
open preview/newsletter_preview_en_*.html
```

### Specifieke RSS Feed Testen

```bash
# Voeg nieuwe feed toe aan sources.yaml

# Test met dry-run
python main.py --dry-run --language nl

# Check of nieuwe feed items zichtbaar zijn in preview
```

## Command-Line Opties

```
usage: main.py [-h] [--dry-run] [--language LANG] [--output-dir DIR]
               [--no-browser]

options:
  --dry-run, --preview
                        Generate newsletter without sending (preview mode)

  --language, -l LANG
                        Process only specific language (e.g., nl, en, zh)

  --output-dir DIR
                        Directory for preview files (default: ./preview)

  --no-browser
                        Don't open browser in dry-run mode
```

## Verschillen met Productie Run

### Dry-Run Mode

- ✅ RSS feeds ophalen
- ✅ AI selectie (Stage 1)
- ✅ AI samenvatting (Stage 2)
- ✅ Database opslag
- ✅ HTML generatie
- ✅ Preview file opslaan
- ✅ Browser openen
- ❌ **NIET** versturen via notifiers (email, webhook, etc.)

### Normale Run

- ✅ Alles van dry-run mode
- ✅ **WEL** versturen via enabled notifiers

## Logging

Dry-run mode heeft speciale logging:

```
============================================================
🔍 DRY-RUN MODE ENABLED
Newsletter will be generated but NOT sent
Preview will be saved to files and opened in browser
============================================================
AI News Bot Starting
Date: 2026-01-27 11:03:31
Mode: DRY-RUN (Preview)
...
💾 Saving preview for NL...
✅ Preview saved: preview/newsletter_preview_nl_30_20260127_110554.html
🌐 Opening preview in browser...
Language NL preview completed
```

## Tips & Tricks

### Multiple Language Testing

```bash
# Test alle talen sequentieel
for lang in nl en zh; do
    python main.py --dry-run --language $lang
done
```

### Quick Preview Check

```bash
# Genereer en open laatste preview
python main.py --dry-run --language nl && \
open preview/$(ls -t preview/ | head -1)
```

### Archive Old Previews

```bash
# Verplaats oude previews naar archive
mkdir -p preview/archive
mv preview/newsletter_preview_*.html preview/archive/
```

### Preview Cleanup

```bash
# Verwijder previews ouder dan 7 dagen
find preview/ -name "newsletter_preview_*.html" -mtime +7 -delete
```

## Troubleshooting

### "No preview directory"

Preview directory wordt automatisch aangemaakt. Als dit faalt:

```bash
mkdir -p preview
chmod 755 preview
```

### "Browser doesn't open"

Use `--no-browser` en open handmatig:

```bash
python main.py --dry-run --no-browser
open preview/newsletter_preview_nl_*.html
```

### "Permission denied writing to output-dir"

Check directory permissions:

```bash
chmod 755 /path/to/output-dir
```

## Database Impact

Dry-run mode schrijft **WEL** naar de database:
- NewsItem records
- NewsletterRun records
- AISummary records
- RSSHealth tracking

Dit is opzettelijk zodat je:
- Run history kunt tracken
- Database queries kunt testen
- Cost tracking blijft werken
- RSS health monitoring blijft accuraat

Als je dit niet wilt, gebruik een test database:

```bash
# Gebruik test database (in config.yaml)
database_url: "sqlite:///data/newsbot_test.db"
```

## Zie Ook

- `prompts/` - Prompt templates voor Stage 1 en Stage 2
- `sources.yaml` - RSS feed configuratie
- `config.yaml` - Algemene configuratie
- `main.py` - Volledige command-line opties

## Examples Output

Preview file opent automatisch in browser en toont:

```
┌─────────────────────────────────────────────────┐
│  🔍 Newsletter Preview Mode                     │
│  Language: NL | Run ID: 30                      │
│  Generated: 2026-01-27 11:05:54                │
│  This is a preview - no notifications were sent │
└─────────────────────────────────────────────────┘

  ┌───────────────────────────────────────┐
  │  Newsletter Content                   │
  │  (styled HTML met je nieuwsbrief)     │
  └───────────────────────────────────────┘
```
