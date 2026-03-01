"""
AI News Generator using configurable LLM providers

Supports:
- Two-stage prompt chaining (selection + summarization)
- Database tracking van runs, selections en summaries
- Kosten tracking per stage
"""
from typing import List, Optional, Dict, Tuple
import json
import re
import os
import time
import hashlib
from datetime import datetime, timedelta
from ..logger import setup_logger
from ..config import LANGUAGE_NAMES
from .web_search import WebSearchTool, get_search_tool_definition
from .fetcher import NewsFetcher
from .summary_parser import parse_summaries
from ..llm_providers import get_llm_provider
from ..database import (
    NewsItem, NewsletterRun, AISelection, AISummary,
    session_scope, get_session
)


logger = setup_logger(__name__)


class NewsGenerator:
    """Generate AI news digest using configurable LLM providers"""

    def __init__(
        self,
        provider_name: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_web_search: bool = False,
        prompts_dir: str = "prompts"
    ):
        """
        Initialize the NewsGenerator.

        Args:
            provider_name: Name of LLM provider to use ('claude' or 'deepseek')
            api_key: API key for the provider. If None, will read from environment
            model: Model name to use. If None, uses provider's default model
            enable_web_search: Whether to enable web search tool for fetching current news
            prompts_dir: Directory containing prompt markdown files

        Raises:
            ValueError: If provider is not recognized or API key is not provided
        """
        # Initialize LLM provider
        self.provider = get_llm_provider(
            provider_name=provider_name,
            api_key=api_key,
            model=model
        )

        self.enable_web_search = enable_web_search
        self.search_tool = WebSearchTool() if enable_web_search else None
        self.news_fetcher = NewsFetcher()
        self.prompts_dir = prompts_dir

        # Load prompts from markdown files
        self._load_prompts()

        logger.info(
            f"NewsGenerator initialized with {self.provider.provider_name} "
            f"(model: {self.provider.model}, web_search: {enable_web_search})"
        )

    def _load_prompts(self):
        """Load prompt templates from markdown files in prompts directory."""
        try:
            # Determine absolute path for prompts directory
            if not os.path.isabs(self.prompts_dir):
                # Get project root directory (2 levels up from this file)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))
                self.prompts_dir = os.path.join(project_root, self.prompts_dir)

            # Load Stage 1 prompt (selection)
            stage1_path = os.path.join(self.prompts_dir, "stage1_selection.md")
            with open(stage1_path, 'r', encoding='utf-8') as f:
                # Skip the first line (markdown header) and read the rest
                lines = f.readlines()
                self.stage1_template = ''.join(lines[2:]).strip()  # Skip "# Title" and empty line

            # Load Stage 2 prompt (summarization)
            stage2_path = os.path.join(self.prompts_dir, "stage2_summarization.md")
            with open(stage2_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.stage2_template = ''.join(lines[2:]).strip()

            logger.info(f"Loaded prompt templates from {self.prompts_dir}")

        except FileNotFoundError as e:
            logger.error(f"Prompt file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            raise

    def _hash_prompt(self, prompt: str) -> str:
        """
        Create hash van prompt voor A/B testing tracking.

        Args:
            prompt: Prompt text

        Returns:
            SHA256 hash (first 16 chars)
        """
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]

    def _create_newsletter_run(
        self,
        language: str,
        items_fetched: int
    ) -> NewsletterRun:
        """
        Create newsletter run record in database.

        Args:
            language: Language code
            items_fetched: Number of items fetched

        Returns:
            NewsletterRun object
        """
        try:
            with session_scope() as session:
                run = NewsletterRun(
                    run_date=datetime.utcnow(),
                    language=language,
                    provider=self.provider.provider_name,
                    model=self.provider.model,
                    items_fetched=items_fetched,
                    status='running'
                )
                session.add(run)
                session.flush()

                # Detach from session
                run_id = run.id
                session.expunge(run)

            logger.info(f"Created newsletter run #{run_id} (lang={language}, provider={self.provider.provider_name})")
            return run_id

        except Exception as e:
            logger.error(f"Error creating newsletter run: {e}", exc_info=True)
            raise

    def _update_run_stage1(
        self,
        run_id: int,
        prompt_hash: str,
        tokens: int,
        cost: float,
        items_selected: int
    ):
        """
        Update newsletter run met Stage 1 metrics.

        Args:
            run_id: Newsletter run ID
            prompt_hash: Hash van Stage 1 prompt
            tokens: Token usage
            cost: Cost in dollars
            items_selected: Number of items selected
        """
        try:
            with session_scope() as session:
                run = session.query(NewsletterRun).get(run_id)
                if run:
                    run.stage1_prompt_hash = prompt_hash
                    run.stage1_tokens = tokens
                    run.stage1_cost = cost
                    run.items_selected = items_selected

            logger.debug(f"Updated run #{run_id} Stage 1: {tokens} tokens, ${cost:.4f}")

        except Exception as e:
            logger.error(f"Error updating run Stage 1: {e}", exc_info=True)

    def _update_run_stage2(
        self,
        run_id: int,
        prompt_hash: str,
        tokens: int,
        cost: float
    ):
        """
        Update newsletter run met Stage 2 metrics.

        Args:
            run_id: Newsletter run ID
            prompt_hash: Hash van Stage 2 prompt
            tokens: Token usage
            cost: Cost in dollars
        """
        try:
            with session_scope() as session:
                run = session.query(NewsletterRun).get(run_id)
                if run:
                    run.stage2_prompt_hash = prompt_hash
                    run.stage2_tokens = tokens
                    run.stage2_cost = cost

                    # Update totals
                    run.total_cost = (run.stage1_cost or 0) + (run.stage2_cost or 0)

            logger.debug(f"Updated run #{run_id} Stage 2: {tokens} tokens, ${cost:.4f}")

        except Exception as e:
            logger.error(f"Error updating run Stage 2: {e}", exc_info=True)

    def _complete_run(self, run_id: int, status: str, error: str = None, runtime: float = None, items_summarized: int = None):
        """
        Mark newsletter run als compleet.

        Args:
            run_id: Newsletter run ID
            status: Status (success/failed)
            error: Error message (indien gefaald)
            runtime: Runtime in seconden
            items_summarized: Aantal items dat succesvol samengevat is
        """
        try:
            with session_scope() as session:
                run = session.query(NewsletterRun).get(run_id)
                if run:
                    run.status = status
                    run.error_message = error
                    run.runtime_seconds = runtime
                    if items_summarized is not None:
                        run.items_summarized = items_summarized

            runtime_str = f"{runtime:.2f}s" if runtime is not None else "unknown"
            logger.info(f"Completed run #{run_id}: status={status}, runtime={runtime_str}")

        except Exception as e:
            logger.error(f"Error completing run: {e}", exc_info=True)

    def get_digest_from_run(self, run_id: int, language: str = 'nl') -> str:
        """
        Haal newsletter digest op uit database voor een specifieke run.

        Args:
            run_id: Newsletter run ID
            language: Taalcode (nl/en/etc)

        Returns:
            Geformatteerde digest tekst
        """
        from .summary_parser import format_summaries_to_markdown
        from ..database.models import AISummary, AISelection

        try:
            with session_scope() as session:
                # Haal alle summaries op voor deze run
                summaries = session.query(AISummary).join(
                    AISelection,
                    AISummary.selection_id == AISelection.id
                ).filter(
                    AISelection.newsletter_run_id == run_id
                ).all()

                if not summaries:
                    logger.warning(f"No summaries found for run #{run_id}")
                    return ""

                # Converteer naar dict format
                summary_dicts = [{
                    'title': s.title,
                    'why_matters': s.why_matters,
                    'big_picture': s.big_picture,
                    'key_details': s.key_details,
                    'next_step': s.next_step,
                    'source_name': s.source_name,
                    'source_url': s.source_url
                } for s in summaries]

                # Format naar markdown
                digest = format_summaries_to_markdown(summary_dicts, language)
                return digest

        except Exception as e:
            logger.error(f"Error getting digest from run #{run_id}: {e}", exc_info=True)
            return ""

    def _format_news_with_ids(self, news_data: Dict) -> tuple:
        """
        Format news with unique IDs for selection stage.

        Args:
            news_data: Dictionary with 'international' and 'domestic' news lists

        Returns:
            Tuple of (formatted_text, news_items_dict)
        """
        formatted = "# Recent AI News Items for Selection\n\n"
        news_items = {}  # id -> full news item
        item_id = 1

        if news_data['international']:
            formatted += "## International News\n\n"
            for item in news_data['international']:
                news_id = f"INT-{item_id}"
                news_items[news_id] = item

                formatted += f"### [{news_id}] {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:400]}...\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"
                item_id += 1

        if news_data['domestic']:
            formatted += "## Domestic News\n\n"
            item_id = 1
            for item in news_data['domestic']:
                news_id = f"DOM-{item_id}"
                news_items[news_id] = item

                formatted += f"### [{news_id}] {item['title']}\n"
                formatted += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted += f"**Description:** {item['description'][:400]}...\n"
                if item['published']:
                    formatted += f"**Published:** {item['published']}\n"
                formatted += "\n"
                item_id += 1

        return formatted, news_items

    def _filter_recently_selected(
        self,
        news_items: Dict,
        formatted_news: str,
        news_data: Dict,
        language: str,
        dedup_days: int
    ) -> tuple:
        """
        Filter items die al geselecteerd zijn in recente nieuwsbrieven.

        Kijkt in de database naar items die in de afgelopen N dagen al
        door de AI geselecteerd en verstuurd zijn, en verwijdert ze uit
        de kandidatenlijst voor Stage 1.

        Args:
            news_items: Dict van news_id -> item data
            formatted_news: Geformatteerde tekst voor Stage 1
            news_data: Originele news_data dict (international/domestic)
            language: Taalcode
            dedup_days: Aantal dagen terugkijken

        Returns:
            Tuple van (filtered_formatted_news, filtered_news_items, removed_count)
        """
        if dedup_days <= 0:
            return formatted_news, news_items, 0

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=dedup_days)

            with session_scope() as session:
                # Haal links op van items die al geselecteerd zijn in recente succesvolle runs
                recent_selections = session.query(NewsItem.link).join(
                    AISelection, AISelection.news_item_id == NewsItem.id
                ).join(
                    NewsletterRun, NewsletterRun.id == AISelection.newsletter_run_id
                ).filter(
                    AISelection.selected == True,
                    NewsletterRun.run_date >= cutoff_date,
                    NewsletterRun.language == language,
                    NewsletterRun.status == 'success'
                ).all()

                recently_selected_links = {row[0] for row in recent_selections}

            if not recently_selected_links:
                logger.info("Dedup: geen eerder geselecteerde items gevonden")
                return formatted_news, news_items, 0

            # Filter items waarvan de link al eerder geselecteerd was
            filtered_items = {}
            removed_count = 0
            for news_id, item in news_items.items():
                if item.get('link') in recently_selected_links:
                    removed_count += 1
                    logger.debug(f"Dedup: verwijderd '{item['title'][:60]}' (eerder geselecteerd)")
                else:
                    filtered_items[news_id] = item

            if removed_count > 0:
                logger.info(f"Dedup: {removed_count} items gefilterd (al verstuurd in afgelopen {dedup_days} dagen)")

                # Herbouw formatted_news zonder gefilterde items
                # Splits news_data opnieuw op basis van gefilterde items
                filtered_international = [
                    item for item in news_data.get('international', [])
                    if item.get('link') not in recently_selected_links
                ]
                filtered_domestic = [
                    item for item in news_data.get('domestic', [])
                    if item.get('link') not in recently_selected_links
                ]

                filtered_data = {
                    'international': filtered_international,
                    'domestic': filtered_domestic
                }
                formatted_news, filtered_items = self._format_news_with_ids(filtered_data)

            return formatted_news, filtered_items, removed_count

        except Exception as e:
            logger.warning(f"Dedup filter fout (items worden niet gefilterd): {e}")
            return formatted_news, news_items, 0

    def generate_news_digest_from_sources(
        self,
        max_tokens: int = 8000,
        language: str = "en",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> int:
        """
        Fetch real-time news and generate a digest using two-stage prompt chaining:
        Stage 1: Analyze and select 15-20 high-quality news items
        Stage 2: Create detailed summaries for selected items

        Args:
            max_tokens: Maximum tokens in response
            language: Language code for the response
            max_items_per_source: Maximum items to fetch per source
            stage1_template: Optional Stage 1 prompt template (from config)
            stage2_template: Optional Stage 2 prompt template (from config)

        Returns:
            newsletter_run_id (int) for building HTML newsletter

        Raises:
            Exception: If fetching or generation fails
        """
        start_time = time.time()

        try:
            # Fetch real-time news
            logger.info("Fetching real-time AI news from sources...")
            news_data = self.news_fetcher.fetch_recent_news(
                language=language,
                max_items_per_source=max_items_per_source
            )

            if not news_data['international'] and not news_data['domestic']:
                error_msg = "No news items fetched from RSS sources. Please check your network connection or RSS feed availability."
                logger.error(error_msg)
                raise Exception(error_msg)

            # Format news with unique IDs for selection
            formatted_news, news_items = self._format_news_with_ids(news_data)
            total_items = len(news_items)

            # Deduplicatie: filter items die al in recente nieuwsbrieven stonden
            from ..config import Config
            try:
                config = Config()
                dedup_days = config.dedup_days
            except Exception:
                dedup_days = 3  # Fallback default

            formatted_news, news_items, dedup_removed = self._filter_recently_selected(
                news_items, formatted_news, news_data, language, dedup_days
            )
            if dedup_removed > 0:
                total_items = len(news_items)
                logger.info(f"Na dedup: {total_items} items over voor selectie")

            if total_items == 0:
                error_msg = f"Geen nieuwe items na deduplicatie ({dedup_removed} items gefilterd, allemaal al eerder verstuurd)"
                logger.warning(error_msg)
                raise Exception(error_msg)

            # Create newsletter run in database
            run_id = self._create_newsletter_run(language, total_items)

            logger.info(f"Starting two-stage prompt chaining with {total_items} news items")

            # ============================================================
            # STAGE 1: Selection - Analyze and select 15-20 best items
            # ============================================================
            logger.info(f"Stage 1: Analyzing and selecting high-quality news items...")

            # Use provided template or use loaded template from markdown file
            if stage1_template is None:
                stage1_template = self.stage1_template

            # Format Stage 1 prompt with placeholders
            selection_prompt = stage1_template.format(
                formatted_news=formatted_news,
                total_items=total_items
            )

            messages = [{"role": "user", "content": selection_prompt}]
            stage1_result = self.provider.generate(
                messages=messages,
                max_tokens=4000,  # give enough tokens for selection
                return_usage=True
            )

            # Extract text en usage data (veilig: werkt ook als provider geen dict teruggeeft)
            if isinstance(stage1_result, dict):
                selection_response = stage1_result['text']
                stage1_usage = stage1_result.get('usage', {})
                stage1_cost = stage1_result.get('cost', 0.0)
            else:
                selection_response = stage1_result
                stage1_usage = {}
                stage1_cost = 0.0

            # Parse selected IDs
            json_match = re.search(r'\[[\s\S]*?\]', selection_response)
            if not json_match:
                logger.warning("Could not parse JSON from selection response, using fallback")
                # Fallback: select first 18 items
                selected_ids = list(news_items.keys())[:18]
            else:
                try:
                    selected_ids = json.loads(json_match.group(0))
                    # Validate IDs
                    selected_ids = [id for id in selected_ids if id in news_items]

                    # Ensure we have 15-20 items
                    if len(selected_ids) < 15:
                        logger.warning(f"Only {len(selected_ids)} items selected, adding more")
                        remaining = [id for id in news_items.keys() if id not in selected_ids]
                        selected_ids.extend(remaining[:18 - len(selected_ids)])
                    elif len(selected_ids) > 20:
                        logger.warning(f"{len(selected_ids)} items selected, trimming to 20")
                        selected_ids = selected_ids[:20]

                except json.JSONDecodeError:
                    logger.warning("JSON parse error, using fallback selection")
                    selected_ids = list(news_items.keys())[:18]

            logger.info(f"Stage 1 completed: Selected {len(selected_ids)} news items")
            logger.debug(f"Selected IDs: {selected_ids}")

            # Track Stage 1 metrics in database
            stage1_prompt_hash = self._hash_prompt(selection_prompt)
            self._update_run_stage1(
                run_id=run_id,
                prompt_hash=stage1_prompt_hash,
                tokens=stage1_usage.get('total_tokens', 0),
                cost=stage1_cost,
                items_selected=len(selected_ids)
            )

            # ============================================================
            # STAGE 2: Summarization - Create detailed summaries
            # ============================================================
            logger.info(f"Stage 2: Creating detailed summaries for selected items...")

            # Format selected news for summarization
            formatted_selected = "# Selected High-Quality AI News Items\n\n"
            for news_id in selected_ids:
                item = news_items[news_id]
                formatted_selected += f"### [{news_id}] {item['title']}\n"
                formatted_selected += f"**Source:** {item['source']}\n"
                if item['description']:
                    formatted_selected += f"**Content:** {item['description']}\n"
                formatted_selected += f"**Link:** {item['link']}\n"
                if item['published']:
                    formatted_selected += f"**Published:** {item['published']}\n"
                formatted_selected += "\n"

            # Use provided template or use loaded template from markdown file
            if stage2_template is None:
                stage2_template = self.stage2_template

            # Format Stage 2 prompt with placeholders
            summarization_prompt = stage2_template.format(
                count=len(selected_ids),
                selected_news=formatted_selected
            )

            # Add language instruction if not English
            if language and language.lower() != "en":
                language_name = LANGUAGE_NAMES.get(language.lower(), language.upper())
                summarization_prompt += f"\n\nIMPORTANT: Please respond entirely in {language_name}."

            # Execute Stage 2: Generate detailed summaries
            messages = [{"role": "user", "content": summarization_prompt}]
            stage2_result = self.provider.generate(
                messages=messages,
                max_tokens=max_tokens,
                return_usage=True
            )

            # Extract text en usage data
            if isinstance(stage2_result, dict):
                response_text = stage2_result['text']
                stage2_usage = stage2_result.get('usage', {})
                stage2_cost = stage2_result.get('cost', 0.0)
            else:
                response_text = stage2_result
                stage2_usage = {}
                stage2_cost = 0.0

            logger.info("Stage 2 completed: News digest generated successfully")
            logger.debug(f"Response length: {len(response_text)} characters")

            # Track Stage 2 metrics in database
            stage2_prompt_hash = self._hash_prompt(summarization_prompt)
            self._update_run_stage2(
                run_id=run_id,
                prompt_hash=stage2_prompt_hash,
                tokens=stage2_usage.get('total_tokens', 0),
                cost=stage2_cost
            )

            # ============================================================
            # PARSE & SAVE: Extract structured data and save to database
            # ============================================================
            logger.info("Parsing summaries and saving to database...")

            # Parse LLM markdown output to structured data
            parsed_summaries = parse_summaries(response_text)

            if not parsed_summaries:
                logger.warning("No summaries parsed from LLM output")
                self._complete_run(run_id, 'failed', 'No summaries parsed from LLM output')
                raise Exception("Failed to parse summaries from LLM output")

            logger.info(f"Parsed {len(parsed_summaries)} summaries from LLM output")

            # Save each summary to database
            summaries_saved = 0
            seen_item_ids = set()  # Track al verwerkte news items om duplicaten te voorkomen
            with session_scope() as session:
                for summary_dict in parsed_summaries:
                    try:
                        # Find matching NewsItem by source_url
                        news_item = session.query(NewsItem).filter(
                            NewsItem.link == summary_dict['source_url']
                        ).first()

                        if not news_item:
                            logger.warning(f"No NewsItem found for URL: {summary_dict['source_url']}")
                            continue

                        # Skip duplicaten: zelfde news item al verwerkt in deze run
                        if news_item.id in seen_item_ids:
                            logger.info(f"Skipping duplicate news item {news_item.id} for '{summary_dict.get('title', 'unknown')}'")
                            continue
                        seen_item_ids.add(news_item.id)

                        # Check of er al een selectie bestaat in de database
                        existing = session.query(AISelection).filter(
                            AISelection.news_item_id == news_item.id,
                            AISelection.newsletter_run_id == run_id
                        ).first()
                        if existing:
                            logger.info(f"Selection already exists for news item {news_item.id}, skipping")
                            continue

                        # Create AISelection record
                        selection = AISelection(
                            news_item_id=news_item.id,
                            newsletter_run_id=run_id,
                            selected=True
                        )
                        session.add(selection)
                        session.flush()  # Get selection.id

                        # Create AISummary record with structured fields
                        # Generate plain text summary for backward compatibility
                        summary_parts = []
                        if summary_dict.get('why_matters'):
                            summary_parts.append(f"Waarom belangrijk: {summary_dict['why_matters']}")
                        if summary_dict.get('big_picture'):
                            summary_parts.append(f"Het grote plaatje: {summary_dict['big_picture']}")
                        summary_text = "\n\n".join(summary_parts) if summary_parts else summary_dict.get('title', '')

                        summary = AISummary(
                            selection_id=selection.id,
                            summary_text=summary_text,  # For backward compatibility with NOT NULL constraint
                            title=summary_dict['title'],
                            why_matters=summary_dict.get('why_matters', ''),
                            big_picture=summary_dict.get('big_picture', ''),
                            key_details=summary_dict.get('key_details', ''),
                            next_step=summary_dict.get('next_step', ''),
                            source_name=summary_dict.get('source_name', ''),
                            source_url=summary_dict.get('source_url', '')
                        )
                        session.add(summary)
                        summaries_saved += 1

                    except Exception as e:
                        logger.error(f"Error saving summary '{summary_dict.get('title', 'unknown')}': {e}")
                        session.rollback()  # Reset sessie zodat volgende saves niet ook falen
                        continue

            logger.info(f"Saved {summaries_saved}/{len(parsed_summaries)} summaries to database")

            # Update run status met runtime en items_summarized
            runtime = time.time() - start_time
            self._complete_run(run_id, 'success', runtime=runtime, items_summarized=summaries_saved)

            logger.info(f"Two-stage prompt chaining completed: {total_items} items → {len(selected_ids)} selected → {summaries_saved} summaries saved (runtime: {runtime:.1f}s)")

            return run_id

        except Exception as e:
            logger.error(f"Failed to generate news digest from sources: {str(e)}", exc_info=True)
            # Mark run as failed if we have run_id
            if 'run_id' in locals():
                runtime = time.time() - start_time
                self._complete_run(run_id, 'failed', str(e), runtime=runtime)
            raise
