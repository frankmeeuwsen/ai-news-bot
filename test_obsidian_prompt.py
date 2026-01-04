#!/usr/bin/env python3
"""Test script om Obsidian links in nieuwsbrief te testen"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.news.fetcher import NewsFetcher
from src.news.generator import NewsGenerator
from src.database import init_db

def main():
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Fetching news items...")
    fetcher = NewsFetcher()
    news_data = fetcher.fetch_recent_news(language='nl', max_items_per_source=2)

    total_items = len(news_data['international']) + len(news_data['domestic'])
    print(f"Fetched {total_items} items total")
    print(f"  International: {len(news_data['international'])}")
    print(f"  Domestic: {len(news_data['domestic'])}")

    if total_items == 0:
        print("No items fetched, exiting")
        return

    print("\nGenerating digest with Obsidian links...")
    generator = NewsGenerator(
        provider_name='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='anthropic/claude-sonnet-4'
    )

    digest = generator.generate_news_digest_from_sources(
        max_tokens=4000,
        language='nl',
        max_items_per_source=2
    )

    # Save to test file
    output_file = 'test_obsidian_output.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(digest)

    print(f"\nDigest saved to {output_file}")

    # Check if Obsidian links are present
    if '[Obs]' in digest:
        obs_count = digest.count('[Obs]')
        print(f"✓ Found {obs_count} Obsidian links in digest")

        # Show first Obsidian link as example
        obs_start = digest.find('[Obs](obsidian://')
        if obs_start != -1:
            obs_end = digest.find(')', obs_start) + 1
            example = digest[obs_start:obs_end]
            print(f"\nExample Obsidian link (first 200 chars):")
            print(example[:200] + "..." if len(example) > 200 else example)
    else:
        print("⚠ No Obsidian links found in digest")

    print("\nDone!")

if __name__ == '__main__':
    main()
