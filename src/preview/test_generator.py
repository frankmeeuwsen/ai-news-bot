"""
Test News Generator - Generate newsletter from database items

Applies prompts to existing database items without RSS fetching.
Stores generated newsletters in database for comparison.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import hashlib
from ..logger import setup_logger
from ..config import Config, LANGUAGE_NAMES
from ..llm_providers import get_llm_provider
from ..database import session_scope, NewsletterRun, AISummary, AISelection, NewsItem


logger = setup_logger(__name__)


class TestNewsGenerator:
    """Generate test newsletters from database items"""

    def __init__(
        self,
        provider_name: str = None,
        api_key: str = None,
        model: str = None
    ):
        """
        Initialize the test generator.

        Args:
            provider_name: LLM provider name (uses config if None)
            api_key: API key (uses config if None)
            model: Model name (uses config if None)
        """
        # Load config
        self.config = Config()

        # Use config values as defaults
        provider_name = provider_name or self.config.llm_provider
        api_key = api_key or self.config.llm_api_key
        model = model or self.config.llm_model

        # Initialize LLM provider
        self.provider = get_llm_provider(
            provider_name=provider_name,
            api_key=api_key,
            model=model
        )

        # Load prompts
        self._load_prompts()

        logger.info(f"TestNewsGenerator initialized with {self.provider.provider_name}")

    def _load_prompts(self):
        """Load prompt templates from markdown files."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompts_dir = os.path.join(project_root, "prompts")

        # Load Stage 2 prompt (summarization) - we skip Stage 1 for testing
        stage2_path = os.path.join(prompts_dir, "stage2_summarization.md")
        with open(stage2_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.stage2_template = ''.join(lines[2:]).strip()

        logger.info(f"Loaded prompt template from {prompts_dir}")

    def _hash_prompt(self, prompt: str) -> str:
        """Create hash of prompt for tracking."""
        return hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]

    def _format_items_for_prompt(self, items: List[Dict[str, Any]]) -> str:
        """
        Format news items for the Stage 2 prompt.

        Args:
            items: List of news item dictionaries

        Returns:
            Formatted text for prompt
        """
        formatted = "# Selected High-Quality AI News Items\n\n"

        for i, item in enumerate(items, 1):
            formatted += f"### [ITEM-{i}] {item['title']}\n"
            formatted += f"**Source:** {item['source']}\n"
            if item.get('description'):
                formatted += f"**Content:** {item['description']}\n"
            formatted += f"**Link:** {item['link']}\n"
            if item.get('published'):
                formatted += f"**Published:** {item['published']}\n"
            formatted += "\n"

        return formatted

    def generate_from_items(
        self,
        items: List[Dict[str, Any]],
        language: str = "nl",
        max_tokens: int = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Generate newsletter from provided items.

        Args:
            items: List of news item dictionaries
            language: Language for output
            max_tokens: Max output tokens (uses config if None)
            save_to_db: Whether to save result to database

        Returns:
            Dictionary with:
            - newsletter: Generated newsletter text
            - run_id: Database run ID (if saved)
            - tokens: Token usage
            - cost: Cost estimate
            - prompt_hash: Hash of prompt used
        """
        max_tokens = max_tokens or self.config.llm_max_tokens
        start_time = datetime.utcnow()

        # Format items for prompt
        formatted_items = self._format_items_for_prompt(items)

        # Build prompt
        prompt = self.stage2_template.format(
            count=len(items),
            selected_news=formatted_items
        )

        # Add language instruction
        if language and language.lower() != "en":
            language_name = LANGUAGE_NAMES.get(language.lower(), language.upper())
            prompt += f"\n\nIMPORTANT: Please respond entirely in {language_name}."

        prompt_hash = self._hash_prompt(prompt)

        logger.info(f"Generating newsletter for {len(items)} items (lang={language}, max_tokens={max_tokens})")

        # Call LLM
        result = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            return_usage=True
        )

        # Parse result
        if isinstance(result, dict):
            newsletter = result.get('text', '')
            usage = result.get('usage', {})
            tokens = usage.get('total_tokens', 0)
            cost = usage.get('cost', 0.0)
        else:
            newsletter = result
            tokens = 0
            cost = 0.0

        # Add footer
        footer = "\n\n---\n\n*Generated by AI News Bot Test Suite*"
        newsletter += footer

        runtime = (datetime.utcnow() - start_time).total_seconds()

        # Save to database
        run_id = None
        if save_to_db:
            run_id = self._save_test_run(
                items=items,
                newsletter=newsletter,
                language=language,
                prompt_hash=prompt_hash,
                tokens=tokens,
                cost=cost,
                runtime=runtime
            )

        logger.info(f"Newsletter generated: {len(newsletter)} chars, {tokens} tokens, ${cost:.4f}")

        return {
            'newsletter': newsletter,
            'run_id': run_id,
            'tokens': tokens,
            'cost': cost,
            'prompt_hash': prompt_hash,
            'runtime': runtime,
            'item_count': len(items)
        }

    def _save_test_run(
        self,
        items: List[Dict[str, Any]],
        newsletter: str,
        language: str,
        prompt_hash: str,
        tokens: int,
        cost: float,
        runtime: float
    ) -> int:
        """
        Save test run to database.

        Returns:
            Newsletter run ID
        """
        with session_scope() as session:
            # Create newsletter run
            run = NewsletterRun(
                run_date=datetime.utcnow(),
                language=language,
                provider=self.provider.provider_name,
                model=self.provider.model,
                stage2_prompt_hash=prompt_hash,
                stage2_tokens=tokens,
                stage2_cost=cost,
                total_cost=cost,
                runtime_seconds=runtime,
                items_fetched=len(items),
                items_selected=len(items),
                items_summarized=len(items),
                status='test_run'  # Mark as test run
            )
            session.add(run)
            session.flush()
            run_id = run.id

            # Create selections for each item (if they have database IDs)
            for item in items:
                if item.get('id'):
                    selection = AISelection(
                        news_item_id=item['id'],
                        newsletter_run_id=run_id,
                        selected=True,
                        selection_reason="Test run - pre-selected"
                    )
                    session.add(selection)
                    session.flush()

                    # Create summary
                    summary = AISummary(
                        selection_id=selection.id,
                        summary_text=newsletter,  # Full newsletter for now
                        tokens_used=tokens,
                        cost=cost
                    )
                    session.add(summary)

            logger.info(f"Saved test run #{run_id} to database")
            return run_id

    def get_test_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent test runs from database.

        Args:
            limit: Maximum runs to return

        Returns:
            List of test run dictionaries
        """
        with session_scope() as session:
            runs = session.query(NewsletterRun).filter(
                NewsletterRun.status == 'test_run'
            ).order_by(
                NewsletterRun.run_date.desc()
            ).limit(limit).all()

            result = []
            for run in runs:
                result.append({
                    'id': run.id,
                    'date': run.run_date.isoformat(),
                    'language': run.language,
                    'provider': run.provider,
                    'model': run.model,
                    'items': run.items_summarized,
                    'tokens': run.stage2_tokens,
                    'cost': run.total_cost,
                    'runtime': run.runtime_seconds,
                    'prompt_hash': run.stage2_prompt_hash
                })

            return result
