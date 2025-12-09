#!/usr/bin/env python3
"""
Test script voor volledige nieuwsbrief generatie met database tracking.

**LET OP: Dit script maakt echte API calls en kost credits!**

Test:
- Volledige two-stage generation
- Database tracking van run, selecties, summaries
- Kosten tracking
"""
import os
import sys
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.database import init_db, session_scope, NewsletterRun, AISelection, AISummary
from src.news.generator import NewsGenerator
from src.logger import setup_logger

logger = setup_logger(__name__)


def test_full_generation():
    """
    Test volledige nieuwsbrief generatie met tracking.

    **LET OP: Dit kost API credits!**
    """
    print("=" * 70)
    print("VOLLEDIGE NIEUWSBRIEF GENERATIE TEST")
    print("=" * 70)
    print()
    print("⚠️  LET OP: Dit script maakt echte LLM API calls!")
    print("⚠️  Dit kost API credits (geschat: $0.05 - $0.15)")
    print()

    # Vraag bevestiging
    response = input("Doorgaan? (ja/nee): ").strip().lower()
    if response not in ['ja', 'j', 'yes', 'y']:
        print("Afgebroken door gebruiker")
        return

    print()
    print("=" * 70)

    # Load config
    config = Config()

    # Initialize database
    print("\n[1] Database initialiseren...")
    db_url = config.database_url
    init_db(db_url=db_url)
    print(f"✓ Database: {db_url}")

    # Create generator
    print("\n[2] Generator aanmaken...")
    generator = NewsGenerator(
        provider_name=config.llm_provider,
        api_key=config.llm_api_key,
        model=config.llm_model,
        enable_web_search=config.enable_web_search
    )
    print(f"✓ Provider: {generator.provider.provider_name}")
    print(f"✓ Model: {generator.provider.model}")

    # Start timer
    start_time = time.time()

    # Create newsletter run
    print("\n[3] Newsletter run aanmaken...")
    run_id = generator._create_newsletter_run(
        language="en",
        items_fetched=0  # Wordt later geupdate
    )
    print(f"✓ Run #{run_id} aangemaakt")

    try:
        # Generate digest (dit kost API credits!)
        print("\n[4] Nieuwsbrief genereren (dit duurt ~30-60 seconden)...")
        print("    Stage 1: Item selectie...")
        print("    Stage 2: Samenvattingen maken...")
        print()

        digest = generator.generate_news_digest_from_sources(
            max_tokens=8000,
            language="en",
            max_items_per_source=5  # Minder items = goedkoper
        )

        # Calculate runtime
        runtime = time.time() - start_time

        # Mark run complete
        generator._complete_run(run_id, status='success', runtime=runtime)

        # Display results
        print("\n" + "=" * 70)
        print("✓ GENERATIE SUCCESVOL")
        print("=" * 70)

        # Query run stats
        with session_scope() as session:
            run = session.query(NewsletterRun).get(run_id)

            print(f"\n📊 Run Statistieken (Run #{run.id}):")
            print("-" * 70)
            print(f"Runtime:         {run.runtime_seconds:.2f}s")
            print(f"Items fetched:   {run.items_fetched or 'N/A'}")
            print(f"Items selected:  {run.items_selected or 'N/A'}")
            print()
            if run.stage1_tokens:
                print(f"Stage 1 tokens:  {run.stage1_tokens}")
                print(f"Stage 1 cost:    ${run.stage1_cost:.4f}")
            if run.stage2_tokens:
                print(f"Stage 2 tokens:  {run.stage2_tokens}")
                print(f"Stage 2 cost:    ${run.stage2_cost:.4f}")
            if run.total_cost:
                print(f"Total cost:      ${run.total_cost:.4f}")
            print("-" * 70)

        # Show preview
        print(f"\n📰 Nieuwsbrief Preview (eerste 500 chars):")
        print("-" * 70)
        print(digest[:500] + "...")
        print("-" * 70)

        # Save to file
        output_file = "test_newsletter_output.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(digest)

        print(f"\n✓ Volledige nieuwsbrief opgeslagen in: {output_file}")

    except Exception as e:
        # Mark run failed
        runtime = time.time() - start_time
        generator._complete_run(run_id, status='failed', error=str(e), runtime=runtime)

        print(f"\n✗ GENERATIE GEFAALD")
        print(f"Error: {e}")
        raise

    print("\n" + "=" * 70)
    print("Test compleet!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_full_generation()
    except KeyboardInterrupt:
        print("\n\nAfgebroken door gebruiker")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ FOUT: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
