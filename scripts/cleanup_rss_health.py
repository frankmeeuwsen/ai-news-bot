#!/usr/bin/env python3
"""
Cleanup script voor RSSHealth tabel na sources.yaml opschoning.

Wat dit script doet:
1. Reset arXiv feeds (waren tijdelijk broken, URLs zijn correct)
2. Verwijdert health records voor feeds die uit sources.yaml zijn gehaald

Gebruik:
    python3 scripts/cleanup_rss_health.py [--dry-run]
"""
import sys
import os

# Voeg project root toe aan Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, session_scope, RSSHealth

# Feeds die uit sources.yaml zijn verwijderd (2026-02-12)
REMOVED_FEEDS = [
    "The Neuron",
    "The AI Report",
    "Healthcare IT News AI",
    "80 Level (AI Section)",
    "Meta AI Blog",
    "DeepMind Blog",
    "Data & Society",
    "AI in Business",
    "MarkTechPost",
    "Computable",
    "Dutch IT Channel",
    "AG Connect",
    "MT/Sprout (Tech)",
    # Hernoemde feeds - oude naam verwijderen (nieuwe naam start met clean state)
    "Engadget AI",                          # hernoemd naar "Engadget"
    "NVIDIA Blog (AI Category)",            # hernoemd naar "NVIDIA Blog"
    "Simon Willison\u2019s Weblog - AI in Industry",  # curly apostrophe variant
    "Simon Willison's Weblog - AI in Industry",        # straight apostrophe variant
]

# Feeds die gereset moeten worden (tijdelijke issues of nieuwe URL)
RESET_FEEDS = [
    "arXiv AI",
    "arXiv Machine Learning",
    "arXiv Computer Vision",
    "arXiv NLP",
    "OpenAI Blog",             # nieuwe URL (openai.com/news/rss.xml)
    "Stability AI",            # nieuwe URL (stability.ai/blog)
    "Simon Willison\u2019s Weblog", # curly apostrophe variant in database
    "Simon Willison's Weblog",     # straight apostrophe variant
    "VentureBeat AI",          # onterecht inactive (fails=0)
    "MIT Technology Review",   # onterecht inactive (fails=0)
]


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN - geen wijzigingen worden opgeslagen ===\n")

    # Initialiseer database
    init_db()

    with session_scope() as session:
        # 1. Reset feeds (arXiv + feeds met nieuwe URLs)
        print("--- Reset feeds ---")
        for feed_name in RESET_FEEDS:
            health = session.query(RSSHealth).filter_by(source_name=feed_name).first()
            if health:
                print(f"  RESET: {feed_name} (was: fails={health.consecutive_fails}, active={health.is_active})")
                if not dry_run:
                    health.consecutive_fails = 0
                    health.is_active = True
            else:
                print(f"  SKIP: {feed_name} (geen health record)")

        # 2. Verwijder records voor verwijderde feeds
        print("\n--- Verwijder health records voor verwijderde feeds ---")
        for feed_name in REMOVED_FEEDS:
            health = session.query(RSSHealth).filter_by(source_name=feed_name).first()
            if health:
                print(f"  DELETE: {feed_name} (fails={health.consecutive_fails}, active={health.is_active})")
                if not dry_run:
                    session.delete(health)
            else:
                print(f"  SKIP: {feed_name} (geen health record)")

        # 3. Toon overzicht van resterende inactive feeds
        print("\n--- Resterende inactive feeds ---")
        inactive = session.query(RSSHealth).filter_by(is_active=False).all()
        if inactive:
            for h in inactive:
                print(f"  INACTIVE: {h.source_name} (fails={h.consecutive_fails})")
        else:
            print("  Geen inactive feeds meer!")

        if dry_run:
            print("\n=== DRY RUN - rollback ===")
            session.rollback()
        else:
            print("\n=== Wijzigingen opgeslagen ===")


if __name__ == "__main__":
    main()
