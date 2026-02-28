<div align="center">

# AI News Bot

Automated AI news curation with a two-stage AI pipeline: selection + summarization. Fetches RSS feeds, curates with Claude, delivers via email.

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=flat-square)](LICENSE)

</div>

---

## How It Works

The bot uses a **two-stage AI pipeline** to turn 100+ RSS items into a focused newsletter:

1. **Stage 1 - Selection**: AI reads all fetched RSS items and picks 15-20 relevant articles based on configurable criteria
2. **Stage 2 - Summarization**: AI writes a newsletter in [Smart Brevity](https://www.axios.com/smart-brevity) format with structured summaries

Both stages use external prompt templates (`prompts/stage1_selection.md` and `prompts/stage2_summarization.md`) that you can customize without touching code.

## Features

- **Two-Stage AI Pipeline**: Separate selection and summarization for better quality control
- **66 RSS Sources**: Pre-configured feeds across 13+ languages (English, Dutch, Chinese, Japanese, and more)
- **Multi-Provider LLM Support**: Claude (default), DeepSeek, Gemini, Grok, OpenAI, or OpenRouter
- **Database Persistence**: SQLite for RSS caching, deduplication, cost tracking, and run history
- **Newsletter Deduplication**: Prevents repeated items across consecutive newsletters (configurable window)
- **Obsidian Integration**: One-click deep links to save articles to your Obsidian vault with structured frontmatter
- **Preview Mode**: `--dry-run` flag generates newsletters without sending, opens in browser for review
- **Multiple Notification Channels**: Email (Resend or Gmail), Webhook, Slack, Telegram, Discord
- **Multilingual Output**: Generate newsletters in 13+ languages
- **RSS Health Monitoring**: Auto-disables broken feeds after repeated failures
- **External Prompt Templates**: Customize AI behavior via markdown files, no code changes needed
- **Automated Scheduling**: Run via GitHub Actions, Forgejo Actions, systemd timer, or cron

## Quick Start

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd ai-news-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required: LLM Provider
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_api_key_here

# Required: Email (choose one)
# Option 1: Resend (recommended)
RESEND_API_KEY=re_xxxxxxxxxxxxx
RESEND_FROM=news@yourdomain.com
EMAIL_TO=recipient@example.com

# Option 2: Gmail
# GMAIL_ADDRESS=you@gmail.com
# GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Notification method
NOTIFICATION_METHODS=email

# Language (default: en, comma-separated for multiple)
AI_RESPONSE_LANGUAGE=nl
```

### 3. Run

```bash
# Production run - generate and send newsletter
python3 main.py

# Preview mode - generate without sending, open in browser
python3 main.py --dry-run

# Preview specific language only
python3 main.py --dry-run --language nl
```

## CLI Options

```
python3 main.py [OPTIONS]

Options:
  --dry-run, --preview    Generate newsletter without sending (preview mode)
  --language, -l LANG     Process only specific language (e.g., nl, en, zh)
  --output-dir DIR        Directory for preview files (default: ./preview)
  --no-browser            Don't auto-open browser in preview mode
```

## Configuration

### config.yaml

The main configuration file controls LLM settings, news behavior, database, and notifications:

```yaml
llm:
  provider: claude              # claude, deepseek, gemini, grok, openai, openrouter
  # model: claude-sonnet-4-5-20250929  # optional override
  max_tokens: 16000             # max output tokens for Stage 2

news:
  enable_web_search: false      # RSS feeds are more reliable
  max_items_per_source: 10
  dedup_days: 3                 # prevent repeats within N days

database:
  type: sqlite
  sqlite:
    path: data/newsbot.db
  cache:
    enabled: false
    ttl_hours: 36
    deduplication: true

notifications:
  email_provider: resend        # resend or gmail

logging:
  level: INFO
```

### sources.yaml

RSS feed configuration with 66 pre-configured sources:

- **International**: TechCrunch, MIT Tech Review, Wired, ArXiv, Hugging Face, OpenAI Blog, and more
- **Social feeds**: Bluesky profiles, Mastodon hashtags
- **Dutch**: Tweakers, Frankwatching, Emerce, AG Connect
- **Chinese**: 36Kr, JiQiZhiXin, Leiphone
- **And 10 more languages**: Japanese, French, German, Spanish, Korean, Portuguese, Italian, Russian, Arabic, Hindi

Each source has a name, URL, category, and language tag. Add or remove feeds by editing the YAML file.

### Prompt Templates

The AI behavior is controlled by two markdown files in `prompts/`:

| File | Purpose |
|------|---------|
| `stage1_selection.md` | Criteria for selecting 15-20 items from 100+ RSS entries |
| `stage2_summarization.md` | Smart Brevity format instructions for the newsletter |

Edit these files to change what gets selected and how it's written. No code changes needed.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Optional | `claude`, `deepseek`, `gemini`, `grok`, `openai`, `openrouter` (default: `claude`) |
| `ANTHROPIC_API_KEY` | If using Claude | [Get it here](https://console.anthropic.com/) |
| `DEEPSEEK_API_KEY` | If using DeepSeek | [Get it here](https://platform.deepseek.com/) |
| `GOOGLE_API_KEY` | If using Gemini | [Get it here](https://makersuite.google.com/app/apikey) |
| `XAI_API_KEY` | If using Grok | [Get it here](https://x.ai/) |
| `OPENAI_API_KEY` | If using OpenAI | [Get it here](https://platform.openai.com/api-keys) |
| `OPENROUTER_API_KEY` | If using OpenRouter | [Get it here](https://openrouter.ai/keys) |
| `NOTIFICATION_METHODS` | Yes | Comma-separated: `email`, `webhook`, `slack`, `telegram`, `discord` |
| `AI_RESPONSE_LANGUAGE` | Optional | Language code(s), default: `en`. Multiple: `en,nl,zh` |
| `RESEND_API_KEY` | If using Resend | [Get it here](https://resend.com) |
| `RESEND_FROM` | If using Resend | Verified sender email address |
| `EMAIL_TO` | If using email | Recipient email address |
| `GMAIL_ADDRESS` | If using Gmail | Your Gmail address |
| `GMAIL_APP_PASSWORD` | If using Gmail | Gmail App Password ([setup](https://myaccount.google.com/apppasswords)) |

For webhook, Slack, Telegram, and Discord configuration, see `.env.example`.

## Deployment Options

### Option 1: GitHub Actions (no server needed)

The included `.github/workflows/daily-news.yml` runs daily at 06:00 UTC. Configure your API keys and email settings as GitHub repository secrets.

```
Repository > Settings > Secrets and variables > Actions > New repository secret
```

### Option 2: Self-Hosted Server (systemd timer)

For more control, run on your own server with a systemd timer:

1. Clone the repo on your server
2. Set up `.env` with your credentials
3. Create a systemd service and timer (see `TROUBLESHOOTING.md` for systemd details)
4. Schedule the timer for your preferred time

### Option 3: Forgejo/Gitea Actions

The included `.forgejo/workflows/deploy.yml` auto-deploys on push to `main`. Configure `SSH_PRIVATE_KEY`, `SERVER_HOST`, and `SERVER_USER` as repository secrets.

## Project Structure

```
ai-news-bot/
├── main.py                          # Entry point with CLI argument parsing
├── config.yaml                      # App configuration
├── sources.yaml                     # RSS feed sources (66 feeds, 13+ languages)
├── .env.example                     # Environment variable template
├── requirements.txt                 # Python dependencies
│
├── prompts/
│   ├── stage1_selection.md          # AI prompt: news selection criteria
│   └── stage2_summarization.md      # AI prompt: Smart Brevity summarization
│
├── src/
│   ├── config.py                    # Configuration management
│   ├── logger.py                    # Logging setup
│   ├── newsletter.py                # HTML newsletter builder
│   ├── database/
│   │   ├── models.py                # SQLAlchemy models (NewsItem, NewsletterRun, etc.)
│   │   └── db.py                    # Database manager
│   ├── news/
│   │   ├── fetcher.py               # RSS fetching with caching & health tracking
│   │   ├── generator.py             # Two-stage AI pipeline (selection + summarization)
│   │   ├── summary_parser.py        # Parse AI output into structured data
│   │   └── web_search.py            # Optional DuckDuckGo search
│   ├── llm_providers/
│   │   ├── claude_provider.py       # Anthropic Claude (primary)
│   │   ├── deepseek_provider.py     # DeepSeek
│   │   ├── gemini_provider.py       # Google Gemini
│   │   ├── grok_provider.py         # xAI Grok
│   │   ├── openai_provider.py       # OpenAI
│   │   └── openrouter_provider.py   # OpenRouter (200+ models)
│   ├── notifiers/
│   │   ├── resend_notifier.py       # Resend transactional email
│   │   ├── email_notifier.py        # Gmail SMTP
│   │   ├── webhook_notifier.py      # Generic webhook
│   │   ├── slack_notifier.py        # Slack
│   │   ├── telegram_notifier.py     # Telegram
│   │   └── discord_notifier.py      # Discord
│   └── obsidian/
│       └── uri_builder.py           # Obsidian deep link generator
│
├── scripts/
│   ├── health-check.sh              # Production health diagnostics
│   ├── pre-deploy-check.sh          # Pre-deployment validation (7 checks)
│   ├── alert-on-failure.sh          # Email alert on service failure
│   ├── weekly-report.py             # Weekly cost/usage report
│   ├── sync-database.sh             # Sync production DB to local (macOS)
│   ├── migrate_database.py          # Database schema migrations
│   └── cleanup_rss_health.py        # Clean up old RSS health records
│
├── .github/workflows/
│   └── daily-news.yml               # GitHub Actions: daily newsletter
│
├── .forgejo/workflows/
│   └── deploy.yml                   # Forgejo Actions: auto-deploy on push
│
├── data/                            # SQLite database (gitignored)
└── logs/                            # Log files (gitignored)
```

## Database

The bot uses SQLite to track everything:

| Table | Purpose |
|-------|---------|
| `NewsItem` | Cached RSS items with GUID/link deduplication |
| `NewsletterRun` | Run history with timestamps, tokens, costs, runtime |
| `AISelection` | Which items were selected in Stage 1 |
| `AISummary` | Structured summaries from Stage 2 |
| `RSSHealth` | Feed health tracking (auto-disable after repeated failures) |
| `UserFeedback` | Schema ready for future feedback collection |

The database file lives in `data/newsbot.db` and is gitignored.

## Email Setup

### Resend (recommended)

Best for reliable delivery. 100 emails/day free tier.

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Optionally verify your domain for custom sender address
4. Set `RESEND_API_KEY`, `RESEND_FROM`, and `EMAIL_TO` in `.env`
5. Set `email_provider: resend` in `config.yaml`

### Gmail (for testing)

Works for personal use but may be flagged as spam.

1. Enable [2-Step Verification](https://myaccount.google.com/security) on your Google account
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Set `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, and `EMAIL_TO` in `.env`
4. Set `email_provider: gmail` in `config.yaml`

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `health-check.sh` | Check database, RSS feeds, recent runs, costs, env consistency | `bash scripts/health-check.sh` |
| `pre-deploy-check.sh` | Validate git status, model sync, imports before deploying | `bash scripts/pre-deploy-check.sh` |
| `weekly-report.py` | Generate weekly cost and usage report | `python3 scripts/weekly-report.py` |
| `sync-database.sh` | Sync production database to local machine via SCP | `bash scripts/sync-database.sh` |
| `migrate_database.py` | Run database schema migrations | `python3 scripts/migrate_database.py` |

## Troubleshooting

### Common Issues

- **"Config file not found"**: Make sure `config.yaml` exists in the project root
- **API authentication errors**: Check that your API key is valid and matches the configured `LLM_PROVIDER`
- **Email not sending**: Verify `NOTIFICATION_METHODS=email` is set and email provider credentials are correct
- **Newsletter is empty**: Check RSS feed health with `bash scripts/health-check.sh`
- **Repeated items**: Increase `dedup_days` in `config.yaml` (default: 3)

See `TROUBLESHOOTING.md` for systemd service issues and server deployment debugging.

## Credits

Originally forked from [giftedunicorn/ai-news-bot](https://github.com/giftedunicorn/ai-news-bot). This version adds the two-stage AI pipeline, database persistence, external prompt templates, Obsidian integration, newsletter deduplication, and RSS health monitoring.

Powered by [Anthropic Claude](https://www.anthropic.com).

## License

GPL-3.0 License - See LICENSE file for details.
