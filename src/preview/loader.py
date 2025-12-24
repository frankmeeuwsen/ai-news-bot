"""
Test Data Loader - Load news items from database for testing

Loads existing news items from the database instead of fetching from RSS feeds.
This allows rapid prompt iteration without network requests.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc
from ..database import session_scope, NewsItem
from ..logger import setup_logger


logger = setup_logger(__name__)


class TestDataLoader:
    """Load news items from database for testing prompts"""

    def __init__(self):
        """Initialize the test data loader"""
        pass

    def get_recent_items(
        self,
        language: str = "nl",
        hours: int = 48,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent news items from database.

        Args:
            language: Language code to filter by
            hours: Look back period in hours
            limit: Maximum items to return

        Returns:
            List of news item dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        with session_scope() as session:
            items = session.query(NewsItem).filter(
                NewsItem.language == language,
                NewsItem.fetched_at >= cutoff
            ).order_by(
                desc(NewsItem.fetched_at)
            ).limit(limit).all()

            result = []
            for item in items:
                result.append({
                    'id': item.id,
                    'source': item.source,
                    'title': item.title,
                    'link': item.link,
                    'description': item.description,
                    'published': item.published_at.isoformat() if item.published_at else None,
                    'fetched_at': item.fetched_at.isoformat(),
                    'category': item.category
                })

            logger.info(f"Loaded {len(result)} items from database (lang={language}, hours={hours})")
            return result

    def get_items_by_ids(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get specific news items by their database IDs.

        Args:
            item_ids: List of database IDs

        Returns:
            List of news item dictionaries
        """
        with session_scope() as session:
            items = session.query(NewsItem).filter(
                NewsItem.id.in_(item_ids)
            ).all()

            result = []
            for item in items:
                result.append({
                    'id': item.id,
                    'source': item.source,
                    'title': item.title,
                    'link': item.link,
                    'description': item.description,
                    'published': item.published_at.isoformat() if item.published_at else None,
                    'fetched_at': item.fetched_at.isoformat(),
                    'category': item.category
                })

            logger.info(f"Loaded {len(result)} items by ID")
            return result

    def get_random_sample(
        self,
        language: str = "nl",
        count: int = 20,
        hours: int = 72
    ) -> List[Dict[str, Any]]:
        """
        Get random sample of news items for testing.

        Args:
            language: Language code to filter by
            count: Number of items to sample
            hours: Look back period in hours

        Returns:
            List of news item dictionaries
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        import random

        with session_scope() as session:
            # Get all matching items and shuffle in Python (simpler than SQL RANDOM)
            items = session.query(NewsItem).filter(
                NewsItem.language == language,
                NewsItem.fetched_at >= cutoff
            ).all()

            # Shuffle and take sample
            random.shuffle(items)
            items = items[:count]

            result = []
            for item in items:
                result.append({
                    'id': item.id,
                    'source': item.source,
                    'title': item.title,
                    'link': item.link,
                    'description': item.description,
                    'published': item.published_at.isoformat() if item.published_at else None,
                    'fetched_at': item.fetched_at.isoformat(),
                    'category': item.category
                })

            logger.info(f"Loaded random sample of {len(result)} items")
            return result

    def get_stats(self, language: str = "nl") -> Dict[str, Any]:
        """
        Get statistics about available test data.

        Args:
            language: Language code to filter by

        Returns:
            Dictionary with stats
        """
        with session_scope() as session:
            total = session.query(NewsItem).filter(
                NewsItem.language == language
            ).count()

            last_24h = session.query(NewsItem).filter(
                NewsItem.language == language,
                NewsItem.fetched_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()

            last_48h = session.query(NewsItem).filter(
                NewsItem.language == language,
                NewsItem.fetched_at >= datetime.utcnow() - timedelta(hours=48)
            ).count()

            sources = session.query(NewsItem.source).filter(
                NewsItem.language == language
            ).distinct().count()

            return {
                'language': language,
                'total_items': total,
                'last_24h': last_24h,
                'last_48h': last_48h,
                'unique_sources': sources
            }
