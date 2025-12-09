#!/usr/bin/env python3
"""
Test script voor alleen RSS feed fetching met caching.

Dit script:
- Initialiseert database
- Fetcht RSS feeds
- Toont cache statistieken
- GEEN AI processing
- GEEN nieuwsbrief verzending
"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_db
from src.config import Config
from src.news.fetcher import NewsFetcher
from src.logger import setup_logger

logger = setup_logger(__name__)


def main():
    print("=" * 60)
    print("AI News Bot - Feed Fetch Test (alleen ophalen)")
    print("=" * 60)

    # Load config
    config = Config()

    # Initialize database
    print("\n[1] Database initialiseren...")
    db_url = config.database_url
    init_db(db_url=db_url, echo=False)
    print(f"✓ Database: {db_url}")

    # Initialize fetcher met cache settings uit config
    print("\n[2] NewsFetcher initialiseren...")
    fetcher = NewsFetcher(
        sources_file="sources.yaml",
        cache_enabled=config.cache_enabled,
        cache_ttl_hours=config.cache_ttl_hours,
        deduplication=config.cache_deduplication
    )
    print(f"✓ Cache enabled: {config.cache_enabled}")
    print(f"✓ Cache TTL: {config.cache_ttl_hours} uur")
    print(f"✓ Deduplicatie: {config.cache_deduplication}")

    # Fetch news (met caching)
    print("\n[3] RSS feeds ophalen...")
    print("-" * 60)

    # Test met Engels (international + domestic nl)
    language = "en"
    max_items = config.max_items_per_source

    print(f"Taal: {language}")
    print(f"Max items per bron: {max_items}")
    print()

    news_data = fetcher.fetch_recent_news(
        language=language,
        max_items_per_source=max_items
    )

    print("-" * 60)

    # Toon resultaten
    print(f"\n[4] Resultaten:")
    print(f"✓ International items: {len(news_data['international'])}")
    print(f"✓ Domestic items: {len(news_data['domestic'])}")
    print(f"✓ Totaal: {len(news_data['international']) + len(news_data['domestic'])} items")

    # Toon eerste paar items als voorbeeld
    print(f"\n[5] Voorbeeld items (eerste 3):")
    print("-" * 60)

    all_items = news_data['international'][:3]
    for i, item in enumerate(all_items, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Bron: {item['source']}")
        print(f"   Link: {item['link'][:60]}...")
        if item.get('guid'):
            print(f"   GUID: {item['guid'][:60]}...")

    print("\n" + "=" * 60)
    print("✓ Fetch test compleet")
    print("=" * 60)
    print("\nTips:")
    print("- Run dit script opnieuw om caching te testen")
    print("- Check data/newsbot.db met SQLite viewer")
    print("- Binnen 36 uur zal cache worden gebruikt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAfgebroken door gebruiker")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ FOUT: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
