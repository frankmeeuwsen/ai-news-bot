#!/usr/bin/env python3
"""
Test script for Obsidian integration with database-driven architecture.

This tests the complete new flow:
1. LLM generates summaries (without Obsidian URIs)
2. Parser extracts structured data
3. Summaries saved to database
4. Python builds Obsidian URIs from database
5. HTML newsletter generated with embedded Obsidian links
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.news.generator import NewsGenerator
from src.newsletter import build_newsletter_html
from src.database import init_db
from datetime import datetime


def main():
    # Initialize database
    print("Initializing database...")
    init_db()

    print("\n" + "=" * 80)
    print("TESTING OBSIDIAN INTEGRATION - DATABASE-DRIVEN ARCHITECTURE")
    print("=" * 80)

    # Initialize generator
    print("\nInitializing news generator...")
    generator = NewsGenerator(
        provider_name='openrouter',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        model='anthropic/claude-sonnet-4'
    )

    # Generate newsletter (Stage 1 + Stage 2 + Parse + Save to DB)
    print("\n" + "-" * 80)
    print("STAGE 1-2: Generating and saving summaries to database...")
    print("-" * 80)

    run_id = generator.generate_news_digest_from_sources(
        max_tokens=12000,
        language='nl',
        max_items_per_source=2  # Small test with 2 items per source
    )

    print(f"\n✓ Newsletter run #{run_id} completed and saved to database")

    # Build HTML newsletter from database with Obsidian links
    print("\n" + "-" * 80)
    print("BUILDING: Generating HTML newsletter with Obsidian links from database...")
    print("-" * 80)

    newsletter_html = build_newsletter_html(run_id)

    if not newsletter_html:
        print("\n✗ ERROR: Failed to build newsletter HTML")
        return 1

    # Count Obsidian links
    obs_count = newsletter_html.count('[Obs]')
    print(f"\n✓ Newsletter HTML generated ({len(newsletter_html)} characters)")
    print(f"✓ Found {obs_count} Obsidian links in newsletter")

    # Save to file for browser testing
    output_file = f'test_obsidian_{datetime.now().strftime("%Y%m%d_%H%M")}.html'

    # Wrap in basic HTML structure for browser viewing
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI News Digest - Obsidian Integration Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <h1>AI News Digest - Obsidian Integration Test</h1>
    <p><strong>Newsletter Run ID:</strong> {run_id}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    <p><strong>Obsidian Links:</strong> {obs_count}</p>
    <hr>
    {newsletter_html}
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"✓ Newsletter saved to: {output_file}")

    # Open in browser
    import webbrowser
    file_path = os.path.abspath(output_file)
    print(f"\nOpening in browser: {file_path}")
    webbrowser.open(f'file://{file_path}')

    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check the opened browser window")
    print("2. Verify all news items have [Obs] links")
    print("3. Click an [Obs] link to test Obsidian integration")
    print("4. Check if note is created in Obsidian vault at:")
    print("   /Users/frank/frankopedia/4 - Resources/AI/")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
