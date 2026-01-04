#!/usr/bin/env python3
"""Test Obsidian link generation voor een enkel artikel"""

import os
import sys
import urllib.parse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db, get_session
from src.database.models import AISummary, AISelection
from src.obsidian import build_obsidian_uri


def main():
    # Initialize database
    init_db()

    # Get latest summary
    session = get_session()
    try:
        summary = (
            session.query(AISummary)
            .join(AISelection)
            .order_by(AISummary.id.desc())
            .first()
        )

        if not summary:
            print("No summaries found in database")
            return

        print(f"Testing Obsidian link for: {summary.title}\n")
        print(f"Why matters: {summary.why_matters}\n")

        # Build URI
        uri = build_obsidian_uri(summary)

        # Parse and decode to show what will be created
        parsed = urllib.parse.urlparse(uri)
        params = urllib.parse.parse_qs(parsed.query)

        print("=" * 80)
        print("OBSIDIAN URI DETAILS")
        print("=" * 80)
        print(f"\nVault: {params['vault'][0]}")
        print(f"File path: {urllib.parse.unquote(params['file'][0])}")
        print(f"\nContent preview (first 500 chars):")
        print("-" * 80)
        content = urllib.parse.unquote(params['content'][0])
        print(content[:500])
        print("...")
        print("-" * 80)
        print(f"\nFull URI length: {len(uri)} characters")
        print(f"\nClick to test in Obsidian:")
        print(uri[:200] + "...")

    finally:
        session.close()


if __name__ == '__main__':
    main()
