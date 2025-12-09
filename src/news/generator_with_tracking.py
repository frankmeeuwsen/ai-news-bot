"""
NewsGenerator wrapper met database tracking.

Dit bestand bevat een wrapper om de bestaande NewsGenerator
uit te breiden met database tracking, zonder de originele code
te moeten herschrijven.
"""
import time
from typing import Optional, Dict
from ..logger import setup_logger
from ..database import init_db, session_scope, NewsItem, AISelection, AISummary
from .generator import NewsGenerator

logger = setup_logger(__name__)


class NewsGeneratorWithTracking(NewsGenerator):
    """
    NewsGenerator met database tracking.

    Extends NewsGenerator om automatisch alle runs, selecties
    en samenvattingen in database te tracken.
    """

    def __init__(self, *args, db_url: Optional[str] = None, **kwargs):
        """
        Initialize generator met database tracking.

        Args:
            db_url: Database URL (optional, voor init_db)
            *args, **kwargs: Passed door naar NewsGenerator
        """
        super().__init__(*args, **kwargs)

        # Initialize database als URL gegeven
        if db_url:
            init_db(db_url=db_url)
            logger.info(f"Database initialized for tracking: {db_url}")

    def generate_with_tracking(
        self,
        max_tokens: int = 8000,
        language: str = "en",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> Dict:
        """
        Generate news digest met volledige database tracking.

        Returns:
            Dict met:
                - digest: Gegenereerde nieuwsbrief text
                - run_id: Newsletter run ID in database
                - stats: Statistieken (kosten, tokens, runtime)
        """
        start_time = time.time()
        run_id = None

        try:
            # Fetch news
            logger.info("Fetching news from sources...")
            news_data = self.news_fetcher.fetch_recent_news(
                language=language,
                max_items_per_source=max_items_per_source
            )

            total_fetched = len(news_data['international']) + len(news_data['domestic'])

            # Create newsletter run
            run_id = self._create_newsletter_run(
                language=language,
                items_fetched=total_fetched
            )

            # Generate digest (gebruik parent method)
            digest = self.generate_news_digest_from_sources(
                max_tokens=max_tokens,
                language=language,
                max_items_per_source=max_items_per_source,
                stage1_template=stage1_template,
                stage2_template=stage2_template
            )

            # Calculate runtime
            runtime = time.time() - start_time

            # Mark run complete
            self._complete_run(run_id, status='success', runtime=runtime)

            # Return result met metadata
            return {
                'digest': digest,
                'run_id': run_id,
                'stats': {
                    'runtime': runtime,
                    'items_fetched': total_fetched,
                    'language': language
                }
            }

        except Exception as e:
            # Mark run failed
            if run_id:
                runtime = time.time() - start_time
                self._complete_run(run_id, status='failed', error=str(e), runtime=runtime)

            logger.error(f"Generation failed: {e}", exc_info=True)
            raise


def create_generator_with_tracking(
    config,
    db_url: Optional[str] = None
) -> NewsGeneratorWithTracking:
    """
    Factory function om NewsGeneratorWithTracking te maken vanuit config.

    Args:
        config: Config object
        db_url: Optional database URL

    Returns:
        NewsGeneratorWithTracking instance
    """
    return NewsGeneratorWithTracking(
        provider_name=config.llm_provider,
        api_key=config.llm_api_key,
        model=config.llm_model,
        enable_web_search=config.enable_web_search,
        db_url=db_url or config.database_url
    )
