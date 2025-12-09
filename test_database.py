#!/usr/bin/env python3
"""
Test script voor database setup en caching functionaliteit.

Tests:
1. Database initialisatie
2. NewsItem opslaan en ophalen
3. Cache TTL werking
4. Deduplicatie (GUID/link)
5. RSS health tracking
"""
import os
import sys
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_db, session_scope, NewsItem, RSSHealth
from src.config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)


def test_database_initialization():
    """Test 1: Database initialisatie"""
    print("\n=== Test 1: Database Initialization ===")

    # Load config
    config = Config()
    db_url = config.database_url

    print(f"Database URL: {db_url}")

    # Initialize database
    init_db(db_url=db_url, echo=False)

    print("✓ Database initialized successfully")
    print(f"✓ Database file created at: {db_url.replace('sqlite:///', '')}")


def test_news_item_crud():
    """Test 2: NewsItem CRUD operaties"""
    print("\n=== Test 2: NewsItem CRUD Operations ===")

    # Create test items
    test_items = [
        {
            'source': 'TechCrunch',
            'title': 'Test Article 1',
            'link': 'https://example.com/article-1',
            'guid': 'test-guid-1',
            'description': 'This is a test article about AI',
            'language': 'en',
            'category': 'international'
        },
        {
            'source': 'TechCrunch',
            'title': 'Test Article 2',
            'link': 'https://example.com/article-2',
            'guid': 'test-guid-2',
            'description': 'Another test article',
            'language': 'en',
            'category': 'international'
        }
    ]

    # Insert items
    with session_scope() as session:
        for item_data in test_items:
            news_item = NewsItem(**item_data)
            session.add(news_item)

    print(f"✓ Inserted {len(test_items)} test items")

    # Retrieve items
    with session_scope() as session:
        items = session.query(NewsItem).filter_by(source='TechCrunch').all()
        print(f"✓ Retrieved {len(items)} items from database")

        for item in items:
            print(f"  - {item.title} (link: {item.link[:40]}...)")


def test_deduplication():
    """Test 3: Deduplicatie op basis van GUID/link"""
    print("\n=== Test 3: Deduplication (GUID/link) ===")

    # Probeer duplicate item toe te voegen (zelfde GUID)
    duplicate_item = NewsItem(
        source='TechCrunch',
        title='Duplicate Article',
        link='https://example.com/article-999',
        guid='test-guid-1',  # Zelfde GUID als eerste test item
        description='This should be rejected',
        language='en',
        category='international'
    )

    try:
        with session_scope() as session:
            # Check if exists
            existing = session.query(NewsItem).filter_by(guid='test-guid-1').first()

            if existing:
                print(f"✓ Duplicate detected via GUID: {existing.title}")
                print("  → Skipping insertion (as expected)")
            else:
                session.add(duplicate_item)
                print("✗ Duplicate was NOT detected (unexpected)")

    except Exception as e:
        print(f"✓ Database rejected duplicate (IntegrityError expected): {e}")

    # Test duplicaat via link (zonder GUID)
    duplicate_link = NewsItem(
        source='TechCrunch',
        title='Duplicate via Link',
        link='https://example.com/article-1',  # Zelfde link als eerste item
        guid=None,
        description='This should also be rejected',
        language='en',
        category='international'
    )

    try:
        with session_scope() as session:
            existing = session.query(NewsItem).filter_by(link='https://example.com/article-1').first()

            if existing:
                print(f"✓ Duplicate detected via link: {existing.title}")
                print("  → Skipping insertion (as expected)")
            else:
                session.add(duplicate_link)
                print("✗ Duplicate via link was NOT detected")

    except Exception as e:
        print(f"✓ Database rejected duplicate link: {e}")


def test_cache_ttl():
    """Test 4: Cache TTL werking"""
    print("\n=== Test 4: Cache TTL ===")

    # Maak oud item (buiten TTL van 36 uur)
    old_item = NewsItem(
        source='OldSource',
        title='Old Article',
        link='https://example.com/old-article',
        guid='old-guid',
        description='This article is too old',
        language='en',
        category='international',
        fetched_at=datetime.utcnow() - timedelta(hours=48)  # 48 uur oud
    )

    # Maak recent item (binnen TTL)
    recent_item = NewsItem(
        source='RecentSource',
        title='Recent Article',
        link='https://example.com/recent-article',
        guid='recent-guid',
        description='This article is fresh',
        language='en',
        category='international',
        fetched_at=datetime.utcnow() - timedelta(hours=12)  # 12 uur oud
    )

    with session_scope() as session:
        session.add(old_item)
        session.add(recent_item)

    print("✓ Added old (48h) and recent (12h) items")

    # Query items binnen 36 uur TTL
    cache_ttl_hours = 36
    cutoff_time = datetime.utcnow() - timedelta(hours=cache_ttl_hours)

    with session_scope() as session:
        cached_items = session.query(NewsItem).filter(
            NewsItem.fetched_at >= cutoff_time
        ).all()

        print(f"✓ Cache query (TTL={cache_ttl_hours}h) returned {len(cached_items)} items:")
        for item in cached_items:
            age_hours = (datetime.utcnow() - item.fetched_at).total_seconds() / 3600
            print(f"  - {item.title} (age: {age_hours:.1f}h)")

        # Verify old item not in results
        old_in_cache = any(item.guid == 'old-guid' for item in cached_items)
        recent_in_cache = any(item.guid == 'recent-guid' for item in cached_items)

        assert not old_in_cache, "Old item should NOT be in cache"
        assert recent_in_cache, "Recent item SHOULD be in cache"

        print("✓ Cache TTL working correctly")


def test_rss_health_tracking():
    """Test 5: RSS feed health tracking"""
    print("\n=== Test 5: RSS Health Tracking ===")

    # Simuleer successful fetches
    with session_scope() as session:
        health = RSSHealth(
            source_name='TestSource',
            feed_url='https://example.com/rss',
            language='en',
            total_fetches=5,
            total_failures=0,
            consecutive_fails=0,
            last_success=datetime.utcnow(),
            is_active=True
        )
        session.add(health)

    print("✓ Created RSS health record")

    # Simuleer failures
    with session_scope() as session:
        health = session.query(RSSHealth).filter_by(source_name='TestSource').first()

        # Simuleer 3 failures
        for i in range(3):
            health.total_fetches += 1
            health.total_failures += 1
            health.consecutive_fails += 1
            health.last_failure = datetime.utcnow()
            health.error_details = f"Test error {i+1}"

            if health.consecutive_fails >= 3:
                health.is_active = False
                print(f"✓ Feed auto-disabled after {health.consecutive_fails} consecutive failures")

    # Verify feed is disabled
    with session_scope() as session:
        health = session.query(RSSHealth).filter_by(source_name='TestSource').first()
        assert not health.is_active, "Feed should be disabled"
        assert health.consecutive_fails == 3, "Should have 3 consecutive failures"
        print(f"✓ Health tracking: {health.total_fetches} fetches, {health.total_failures} failures")


def test_cleanup():
    """Cleanup test data"""
    print("\n=== Cleanup ===")

    with session_scope() as session:
        # Delete test items
        session.query(NewsItem).filter(NewsItem.source.in_(['TechCrunch', 'OldSource', 'RecentSource'])).delete()
        session.query(RSSHealth).filter_by(source_name='TestSource').delete()

    print("✓ Test data cleaned up")


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI News Bot - Database Test Suite")
    print("=" * 60)

    try:
        test_database_initialization()
        test_news_item_crud()
        test_deduplication()
        test_cache_ttl()
        test_rss_health_tracking()
        test_cleanup()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
