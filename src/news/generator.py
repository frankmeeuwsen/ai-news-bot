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
import hashlib
from datetime import datetime
from ..logger import setup_logger
from ..config import LANGUAGE_NAMES
from .web_search import WebSearchTool, get_search_tool_definition
from .fetcher import NewsFetcher
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

    def _complete_run(self, run_id: int, status: str, error: str = None, runtime: float = None):
        """
        Mark newsletter run als compleet.

        Args:
            run_id: Newsletter run ID
            status: Status (success/failed)
            error: Error message (indien gefaald)
            runtime: Runtime in seconden
        """
        try:
            with session_scope() as session:
                run = session.query(NewsletterRun).get(run_id)
                if run:
                    run.status = status
                    run.error_message = error
                    run.runtime_seconds = runtime

            logger.info(f"Completed run #{run_id}: status={status}, runtime={runtime:.2f}s")

        except Exception as e:
            logger.error(f"Error completing run: {e}", exc_info=True)

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

    def generate_news_digest_from_sources(
        self,
        max_tokens: int = 8000,
        language: str = "en",
        max_items_per_source: int = 5,
        stage1_template: Optional[str] = None,
        stage2_template: Optional[str] = None
    ) -> str:
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
            Generated news digest as string

        Raises:
            Exception: If fetching or generation fails
        """
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
            selection_response = self.provider.generate(
                messages=messages,
                max_tokens=4000 # give enough tokens for selection
            )

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
            response_text = self.provider.generate(
                messages=messages,
                max_tokens=max_tokens
            )

            # Add footer with GitHub link
            footer = "\n\n---\n\n*Generated by [AI News Bot](https://github.com/giftedunicorn/ai-news-bot) - Your AI-powered news assistant*"
            response_text += footer

            logger.info("Stage 2 completed: News digest generated successfully")
            logger.info(f"Two-stage prompt chaining completed: {total_items} items → {len(selected_ids)} selected → full digest")
            logger.debug(f"Response length: {len(response_text)} characters")

            return response_text

        except Exception as e:
            logger.error(f"Failed to generate news digest from sources: {str(e)}", exc_info=True)
            raise
