"""
News fetcher module - Fetches real-time AI news from various sources

Supports:
- RSS feed fetching met caching
- Deduplicatie op basis van GUID/link
- Database persistentie voor token besparing
"""
import requests
import yaml
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from sqlalchemy import and_, or_
from ..logger import setup_logger
from ..database import NewsItem, RSSHealth, session_scope


logger = setup_logger(__name__)


class NewsFetcher:
    """Fetch real-time AI news from RSS feeds and news APIs"""

    def __init__(
        self,
        sources_file: str = "sources.yaml",
        cache_enabled: bool = True,
        cache_ttl_hours: int = 36,
        deduplication: bool = True
    ):
        """
        Initialize the news fetcher.

        Args:
            sources_file: Path to YAML file containing RSS feed sources
            cache_enabled: Enable database caching (hergebruik recente items)
            cache_ttl_hours: Cache TTL in hours (default: 36 uur)
            deduplication: Enable deduplicatie op basis van GUID/link
        """
        # Load sources from YAML file
        self._load_sources(sources_file)

        # Cache instellingen
        self.cache_enabled = cache_enabled
        self.cache_ttl_hours = cache_ttl_hours
        self.deduplication = deduplication

        logger.info(
            f"NewsFetcher initialized (cache: {cache_enabled}, "
            f"ttl: {cache_ttl_hours}h, dedup: {deduplication})"
        )

    def _load_sources(self, sources_file: str):
        """
        Load RSS feed sources from YAML configuration file.

        Args:
            sources_file: Path to YAML file containing RSS feed sources
        """
        try:
            # Determine absolute path (support both relative and absolute paths)
            if not os.path.isabs(sources_file):
                # Get project root directory (2 levels up from this file)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))
                sources_file = os.path.join(project_root, sources_file)

            with open(sources_file, 'r', encoding='utf-8') as f:
                sources = yaml.safe_load(f)

            # Load international feeds
            self.rss_feeds = sources.get('international', {})

            # Load language-specific feeds
            languages = sources.get('languages', {})
            self.chinese_feeds = languages.get('zh', {})
            self.japanese_feeds = languages.get('ja', {})
            self.french_feeds = languages.get('fr', {})
            self.spanish_feeds = languages.get('es', {})
            self.german_feeds = languages.get('de', {})
            self.korean_feeds = languages.get('ko', {})
            self.portuguese_feeds = languages.get('pt', {})
            self.italian_feeds = languages.get('it', {})
            self.russian_feeds = languages.get('ru', {})
            self.dutch_feeds = languages.get('nl', {})
            self.arabic_feeds = languages.get('ar', {})
            self.hindi_feeds = languages.get('hi', {})

            logger.info(f"Loaded {len(self.rss_feeds)} international sources from {sources_file}")
            logger.info(f"Loaded language-specific sources for {len(languages)} languages")

        except FileNotFoundError:
            logger.error(f"Sources file not found: {sources_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing sources YAML file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            raise


    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, str]]:
        """
        Fetch news items from an RSS feed.

        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to fetch

        Returns:
            List of news items with title, link, description, guid, and published date
        """
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            items = []
            # Handle both RSS 2.0 and Atom formats
            if root.tag == 'rss':
                news_items = root.findall('.//item')[:max_items]
                for item in news_items:
                    title = item.find('title')
                    link = item.find('link')
                    guid = item.find('guid')
                    description = item.find('description')
                    pub_date = item.find('pubDate')

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.text if link is not None else '',
                        'guid': guid.text if guid is not None else None,  # GUID voor deduplicatie
                        'description': self._clean_html(description.text if description is not None else ''),
                        'published': pub_date.text if pub_date is not None else '',
                    })
            else:
                # Atom format
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('.//atom:entry', namespace)[:max_items]
                for entry in entries:
                    title = entry.find('atom:title', namespace)
                    link = entry.find('atom:link', namespace)
                    guid = entry.find('atom:id', namespace)  # Atom gebruikt 'id' als GUID
                    summary = entry.find('atom:summary', namespace)
                    updated = entry.find('atom:updated', namespace)

                    items.append({
                        'title': title.text if title is not None else '',
                        'link': link.get('href', '') if link is not None else '',
                        'guid': guid.text if guid is not None else None,
                        'description': self._clean_html(summary.text if summary is not None else ''),
                        'published': updated.text if updated is not None else '',
                    })

            logger.info(f"Fetched {len(items)} items from RSS feed")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {str(e)}")
            return []

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _parse_published_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse RSS date string naar datetime object.

        Args:
            date_str: Date string uit RSS feed

        Returns:
            datetime object of None als parsing faalt
        """
        if not date_str:
            return None

        # Probeer verschillende RSS date formaten
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.debug(f"Could not parse date '{date_str}': {e}")
            return None

    def _get_cached_items(
        self,
        source: str,
        language: str,
        category: str
    ) -> List[NewsItem]:
        """
        Haal gecachte items op uit database binnen TTL.

        Args:
            source: Source naam (bijv. "TechCrunch")
            language: Taal code (en/nl/etc.)
            category: Category (international/domestic)

        Returns:
            List van NewsItem objecten uit cache
        """
        if not self.cache_enabled:
            return []

        # Bereken cache cutoff tijd
        cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_ttl_hours)

        try:
            with session_scope() as session:
                cached = session.query(NewsItem).filter(
                    and_(
                        NewsItem.source == source,
                        NewsItem.language == language,
                        NewsItem.category == category,
                        NewsItem.fetched_at >= cutoff_time
                    )
                ).order_by(NewsItem.fetched_at.desc()).all()

                # Detach from session (anders krijg je lazy loading errors)
                session.expunge_all()

                logger.debug(f"Found {len(cached)} cached items for {source} (lang={language})")
                return cached

        except Exception as e:
            logger.error(f"Error fetching cached items: {e}", exc_info=True)
            return []

    def _save_news_item(
        self,
        item_data: Dict[str, str],
        source: str,
        language: str,
        category: str
    ) -> Optional[NewsItem]:
        """
        Sla nieuwsitem op in database (met deduplicatie check).

        Args:
            item_data: RSS item data (title, link, description, etc.)
            source: Source naam
            language: Taal code
            category: Category

        Returns:
            NewsItem object of None als duplicaat
        """
        try:
            with session_scope() as session:
                # Check duplicaat op basis van GUID (primair) of link (fallback)
                guid = item_data.get('guid')
                link = item_data.get('link')

                # Zoek bestaand item
                existing = None
                if self.deduplication:
                    if guid:
                        existing = session.query(NewsItem).filter_by(guid=guid).first()
                    if not existing and link:
                        existing = session.query(NewsItem).filter_by(link=link).first()

                if existing:
                    logger.debug(f"Skipping duplicate item: {item_data.get('title', '')[:50]}")
                    return None

                # Parse published date
                published_at = self._parse_published_date(item_data.get('published', ''))

                # Maak nieuw item
                news_item = NewsItem(
                    source=source,
                    title=item_data['title'],
                    link=link,
                    guid=guid,
                    description=item_data.get('description', ''),
                    published_at=published_at,
                    fetched_at=datetime.utcnow(),
                    language=language,
                    category=category,
                    raw_data=item_data  # Bewaar volledige RSS entry
                )

                session.add(news_item)
                session.flush()  # Get ID zonder te committen

                # Detach van session
                session.expunge(news_item)

                logger.debug(f"Saved new item: {news_item.title[:50]}")
                return news_item

        except Exception as e:
            logger.error(f"Error saving news item: {e}", exc_info=True)
            return None

    def _update_rss_health(self, source_name: str, feed_url: str, success: bool, error: str = None):
        """
        Update RSS feed health tracking in database.

        Args:
            source_name: Source naam
            feed_url: RSS feed URL
            success: Of fetch succesvol was
            error: Error message (indien van toepassing)
        """
        try:
            with session_scope() as session:
                # Zoek of maak health record
                health = session.query(RSSHealth).filter_by(source_name=source_name).first()

                if not health:
                    # Maak nieuw record met expliciete default waarden
                    health = RSSHealth(
                        source_name=source_name,
                        feed_url=feed_url,
                        total_fetches=0,
                        total_failures=0,
                        consecutive_fails=0,
                        is_active=True
                    )
                    session.add(health)
                    # Flush om defaults te initialiseren
                    session.flush()

                # Update metrics
                health.total_fetches += 1

                if success:
                    health.last_success = datetime.utcnow()
                    health.consecutive_fails = 0
                else:
                    health.last_failure = datetime.utcnow()
                    health.consecutive_fails += 1
                    health.total_failures += 1
                    health.error_details = error

                    # Auto-disable na 3 failures (zoals TODO vraagt)
                    if health.consecutive_fails >= 3:
                        health.is_active = False
                        logger.warning(
                            f"RSS feed '{source_name}' disabled after {health.consecutive_fails} "
                            f"consecutive failures"
                        )

                logger.debug(f"Updated RSS health for {source_name} (success={success})")

        except Exception as e:
            logger.error(f"Error updating RSS health: {e}", exc_info=True)

    def fetch_recent_news(
        self,
        language: str = "en",
        max_items_per_source: int = 5
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Fetch recent AI news from all configured sources met caching support.

        Workflow:
        1. Check cache voor recente items (binnen TTL)
        2. Fetch nieuwe items van RSS feeds
        3. Sla nieuwe items op in database
        4. Update RSS health tracking
        5. Return gecombineerde resultaten

        Args:
            language: Language code for the response
            max_items_per_source: Maximum items to fetch per source

        Returns:
            Dictionary with 'international' and 'domestic' news lists
        """
        logger.info("Fetching recent AI news from all sources...")

        all_news = {
            'international': [],
            'domestic': []
        }

        stats = {
            'cached': 0,
            'fetched': 0,
            'duplicates': 0
        }

        # Fetch international news
        for source_name, feed_url in self.rss_feeds.items():
            # Check cache eerst
            cached_items = self._get_cached_items(source_name, language, 'international')

            if cached_items and len(cached_items) >= max_items_per_source:
                # Gebruik cached items (converteren naar dict formaat)
                logger.info(f"Using {len(cached_items[:max_items_per_source])} cached items for {source_name}")
                for cached in cached_items[:max_items_per_source]:
                    all_news['international'].append({
                        'source': cached.source,
                        'title': cached.title,
                        'link': cached.link,
                        'guid': cached.guid,
                        'description': cached.description,
                        'published': cached.published_at.isoformat() if cached.published_at else ''
                    })
                stats['cached'] += len(cached_items[:max_items_per_source])
            else:
                # Fetch van RSS feed
                items = self.fetch_rss_feed(feed_url, max_items_per_source)

                if items:
                    # Update health: success
                    self._update_rss_health(source_name, feed_url, success=True)

                    # Sla nieuwe items op
                    for item in items:
                        saved_item = self._save_news_item(item, source_name, language, 'international')
                        if saved_item:
                            all_news['international'].append({
                                'source': source_name,
                                'title': item['title'],
                                'link': item['link'],
                                'guid': item.get('guid'),
                                'description': item['description'],
                                'published': item['published']
                            })
                            stats['fetched'] += 1
                        else:
                            stats['duplicates'] += 1
                else:
                    # Update health: failure
                    self._update_rss_health(source_name, feed_url, success=False, error="No items fetched")

        # Fetch domestic news based on language
        language_feeds_map = {
            "zh": self.chinese_feeds,
            "ja": self.japanese_feeds,
            "fr": self.french_feeds,
            "es": self.spanish_feeds,
            "de": self.german_feeds,
            "ko": self.korean_feeds,
            "pt": self.portuguese_feeds,
            "it": self.italian_feeds,
            "ru": self.russian_feeds,
            "nl": self.dutch_feeds,
            "ar": self.arabic_feeds,
            "hi": self.hindi_feeds,
        }

        feeds = language_feeds_map.get(language)
        if not feeds:
            logger.warning(f"No domestic feeds configured for language: {language}, using international only")
        else:
            for source_name, feed_url in feeds.items():
                # Check cache
                cached_items = self._get_cached_items(source_name, language, 'domestic')

                if cached_items and len(cached_items) >= max_items_per_source:
                    # Gebruik cached items
                    logger.info(f"Using {len(cached_items[:max_items_per_source])} cached items for {source_name}")
                    for cached in cached_items[:max_items_per_source]:
                        all_news['domestic'].append({
                            'source': cached.source,
                            'title': cached.title,
                            'link': cached.link,
                            'guid': cached.guid,
                            'description': cached.description,
                            'published': cached.published_at.isoformat() if cached.published_at else ''
                        })
                    stats['cached'] += len(cached_items[:max_items_per_source])
                else:
                    # Fetch van RSS feed
                    items = self.fetch_rss_feed(feed_url, max_items_per_source)

                    if items:
                        # Update health: success
                        self._update_rss_health(source_name, feed_url, success=True)

                        # Sla nieuwe items op
                        for item in items:
                            saved_item = self._save_news_item(item, source_name, language, 'domestic')
                            if saved_item:
                                all_news['domestic'].append({
                                    'source': source_name,
                                    'title': item['title'],
                                    'link': item['link'],
                                    'guid': item.get('guid'),
                                    'description': item['description'],
                                    'published': item['published']
                                })
                                stats['fetched'] += 1
                            else:
                                stats['duplicates'] += 1
                    else:
                        # Update health: failure
                        self._update_rss_health(source_name, feed_url, success=False, error="No items fetched")

        logger.info(
            f"Fetched {len(all_news['international'])} international and "
            f"{len(all_news['domestic'])} domestic ({language}) items "
            f"(cached: {stats['cached']}, new: {stats['fetched']}, duplicates: {stats['duplicates']})"
        )

        return all_news

    def format_news_for_summary(self, news_data: Dict[str, List[Dict[str, str]]]) -> str:
        """
        Format fetched news into a text suitable for AI summarization.

        Args:
            news_data: Dictionary with 'international' and 'domestic' news lists

        Returns:
            Formatted news text
        """
        formatted = "# Recent AI News Items to Summarize\n\n"

        if news_data['international']:
            formatted += "## International News\n\n"
            for i, item in enumerate(news_data['international'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        if news_data['domestic']:
            formatted += "## Domestic News\n\n"
            for i, item in enumerate(news_data['domestic'], 1):
                formatted += f"### {i}. {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:300]}...\n"
                formatted += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"

        return formatted
