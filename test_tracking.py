#!/usr/bin/env python3
"""
Test script voor NewsGenerator met database tracking.

Test:
- NewsletterRun aanmaken
- Run metadata tracking
- Status updates
"""
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.database import init_db, session_scope, NewsletterRun
from src.news.generator_with_tracking import create_generator_with_tracking
from src.logger import setup_logger

logger = setup_logger(__name__)


def test_basic_tracking():
    """Test basic newsletter run tracking"""
    print("=" * 60)
    print("NewsGenerator Tracking Test")
    print("=" * 60)

    # Load config
    config = Config()

    # Initialize database
    print("\n[1] Database initialiseren...")
    db_url = config.database_url
    init_db(db_url=db_url)
    print(f"✓ Database: {db_url}")

    # Create generator met tracking
    print("\n[2] Generator aanmaken...")
    generator = create_generator_with_tracking(config)
    print(f"✓ Provider: {generator.provider.provider_name}")
    print(f"✓ Model: {generator.provider.model}")

    # Fetch news en create run (zonder AI generation)
    print("\n[3] Newsletter run aanmaken...")

    # Fetch news
    news_data = generator.news_fetcher.fetch_recent_news(
        language="en",
        max_items_per_source=5
    )

    total_items = len(news_data['international']) + len(news_data['domestic'])
    print(f"✓ Gefetched: {total_items} items")

    # Create run record
    run_id = generator._create_newsletter_run(
        language="en",
        items_fetched=total_items
    )
    print(f"✓ Newsletter run #{run_id} aangemaakt")

    # Simulate Stage 1 update
    print("\n[4] Stage 1 metrics simuleren...")
    generator._update_run_stage1(
        run_id=run_id,
        prompt_hash="test_hash_1",
        tokens=500,
        cost=0.015,
        items_selected=18
    )
    print("✓ Stage 1 metrics opgeslagen")

    # Simulate Stage 2 update
    print("\n[5] Stage 2 metrics simuleren...")
    generator._update_run_stage2(
        run_id=run_id,
        prompt_hash="test_hash_2",
        tokens=3000,
        cost=0.090
    )
    print("✓ Stage 2 metrics opgeslagen")

    # Complete run
    print("\n[6] Run afsluiten...")
    generator._complete_run(
        run_id=run_id,
        status='success',
        runtime=45.5
    )
    print("✓ Run afgerond")

    # Query en display resultaten
    print("\n[7] Database query...")
    with session_scope() as session:
        run = session.query(NewsletterRun).get(run_id)

        print("-" * 60)
        print(f"Newsletter Run #{run.id}")
        print("-" * 60)
        print(f"Datum:           {run.run_date}")
        print(f"Taal:            {run.language}")
        print(f"Provider:        {run.provider}")
        print(f"Model:           {run.model}")
        print(f"Status:          {run.status}")
        print(f"Runtime:         {run.runtime_seconds:.2f}s")
        print()
        print(f"Items fetched:   {run.items_fetched}")
        print(f"Items selected:  {run.items_selected}")
        print()
        print(f"Stage 1 tokens:  {run.stage1_tokens}")
        print(f"Stage 1 cost:    ${run.stage1_cost:.4f}")
        print(f"Stage 2 tokens:  {run.stage2_tokens}")
        print(f"Stage 2 cost:    ${run.stage2_cost:.4f}")
        print(f"Total cost:      ${run.total_cost:.4f}")
        print("-" * 60)

    print("\n" + "=" * 60)
    print("✓ Tracking test compleet")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_basic_tracking()
    except KeyboardInterrupt:
        print("\n\nAfgebroken door gebruiker")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ FOUT: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
