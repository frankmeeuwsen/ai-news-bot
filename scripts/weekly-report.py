#!/usr/bin/env python3
"""
Wekelijks rapport voor AI News Bot.

Genereert een overzicht van de afgelopen week:
- Newsletter runs (per dag, status, items, runtime)
- Database statistieken (nieuwe items, totalen)
- RSS feed health (actief/disabled)
- Kosten overzicht (tokens, geschatte kosten)
- Git commit activiteit

Gebruik:
    python3 scripts/weekly-report.py              # Genereer en verstuur email
    python3 scripts/weekly-report.py --dry-run     # Print rapport, stuur niet
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Voeg project root toe aan Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy import func
from src.database.db import init_db, session_scope
from src.database.models import NewsItem, NewsletterRun, RSSHealth


def get_week_boundaries():
    """Bereken begin en eind van de afgelopen 7 dagen."""
    now = datetime.now(tz=None)
    week_ago = now - timedelta(days=7)
    return week_ago, now


def query_newsletter_runs(session, since, until):
    """Haal alle newsletter runs op van de afgelopen week."""
    runs = (
        session.query(NewsletterRun)
        .filter(NewsletterRun.run_date >= since)
        .filter(NewsletterRun.run_date < until)
        .order_by(NewsletterRun.run_date)
        .all()
    )
    return runs


def query_news_items_count(session, since, until):
    """Tel nieuwe items opgehaald deze week."""
    count = (
        session.query(func.count(NewsItem.id))
        .filter(NewsItem.fetched_at >= since)
        .filter(NewsItem.fetched_at < until)
        .scalar()
    )
    return count or 0


def query_total_items(session):
    """Tel totaal aantal items in database."""
    return session.query(func.count(NewsItem.id)).scalar() or 0


def query_rss_health(session):
    """Haal RSS feed health stats op."""
    active = (
        session.query(func.count(RSSHealth.id))
        .filter(RSSHealth.is_active == True)
        .scalar()
    ) or 0
    disabled = (
        session.query(func.count(RSSHealth.id))
        .filter(RSSHealth.is_active == False)
        .scalar()
    ) or 0
    return active, disabled


def get_git_commits(days=7):
    """Haal git commits op van de afgelopen week."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={days} days ago"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")
        return []
    except Exception:
        return []


def format_runtime(seconds):
    """Formatteer runtime in leesbaar formaat."""
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"


def format_cost(cost):
    """Formatteer kosten."""
    if cost is None or cost == 0:
        return "-"
    return f"${cost:.4f}"


def generate_report():
    """Genereer het wekelijks rapport als markdown."""
    since, until = get_week_boundaries()

    # Bereken weeknummer en datumbereik
    now = datetime.now()
    week_num = now.isocalendar()[1]
    date_from = (now - timedelta(days=7)).strftime("%d %b")
    date_to = now.strftime("%d %b %Y")

    with session_scope() as session:
        runs = query_newsletter_runs(session, since, until)
        new_items = query_news_items_count(session, since, until)
        total_items = query_total_items(session)
        active_feeds, disabled_feeds = query_rss_health(session)

        # Bouw rapport (binnen session scope zodat lazy-loaded attributen werken)
        lines = []
        lines.append(f"# Wekelijks Rapport - AI News Bot")
        lines.append(f"Week {week_num} ({date_from} - {date_to})")
        lines.append("")

        # Newsletter Runs tabel
        lines.append("## Newsletter Runs")
        total_fetched = 0
        total_selected = 0
        total_runtime = 0
        total_tokens = 0
        total_cost = 0
        success_count = 0
        fail_count = 0

        if runs:
            lines.append("")
            lines.append("| Dag | Taal | Status | Opgehaald | Geselecteerd | Runtime |")
            lines.append("|-----|------|--------|-----------|--------------|---------|")

            for run in runs:
                dag = run.run_date.strftime("%a %d/%m")
                status = run.status or "unknown"
                fetched = run.items_fetched or 0
                selected = run.items_selected or 0
                runtime = format_runtime(run.runtime_seconds)

                if status == "success":
                    success_count += 1
                else:
                    fail_count += 1

                total_fetched += fetched
                total_selected += selected
                total_runtime += (run.runtime_seconds or 0)
                total_tokens += (run.stage1_tokens or 0) + (run.stage2_tokens or 0)
                total_cost += (run.total_cost or 0)

                lines.append(f"| {dag} | {run.language} | {status} | {fetched} | {selected} | {runtime} |")

            lines.append("")
            lines.append(f"**Totaal:** {len(runs)} runs ({success_count} success, {fail_count} failed)")
            lines.append(f"**Totale runtime:** {format_runtime(total_runtime)}")
        else:
            lines.append("Geen runs deze week.")
        lines.append("")

        # Database stats
        lines.append("## Database")
        lines.append(f"- Nieuwe items deze week: {new_items:,}")
        lines.append(f"- Totaal items in database: {total_items:,}")
        lines.append(f"- Actieve RSS feeds: {active_feeds}")
        lines.append(f"- Disabled feeds: {disabled_feeds}")
        lines.append("")

        # Kosten (alleen als er runs zijn met kosten data)
        if runs:
            lines.append("## Kosten")
            lines.append(f"- Totaal tokens: {total_tokens:,}")
            lines.append(f"- Geschatte kosten: {format_cost(total_cost)}")
            lines.append("")

    # Git commits
    commits = get_git_commits()
    lines.append("## Git Activiteit")
    if commits:
        for commit in commits:
            lines.append(f"- `{commit}`")
    else:
        lines.append("Geen commits deze week.")
    lines.append("")

    return "\n".join(lines)


def send_report(report_text):
    """Verstuur rapport via Resend email."""
    from src.notifiers.resend_notifier import ResendNotifier

    notifier = ResendNotifier()

    now = datetime.now()
    week_num = now.isocalendar()[1]
    subject = f"AI News Bot - Weekrapport #{week_num}"

    return notifier.send(
        content=report_text,
        subject=subject,
        language="nl",
    )


def main():
    parser = argparse.ArgumentParser(description="Wekelijks rapport AI News Bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rapport naar console, verstuur niet per email",
    )
    args = parser.parse_args()

    # Database initialiseren
    init_db()

    # Rapport genereren
    report = generate_report()

    if args.dry_run:
        print(report)
        return 0

    # Verstuur email
    success = send_report(report)
    if success:
        print(f"Weekrapport verstuurd naar {os.getenv('EMAIL_TO')}")
        return 0
    else:
        print("FOUT: Weekrapport versturen mislukt", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
