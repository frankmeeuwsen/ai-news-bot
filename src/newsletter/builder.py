"""
Build HTML newsletter from database summaries.

Queries ai_summaries for a given newsletter run and generates complete HTML
with embedded Obsidian links.
"""
from typing import List
from sqlalchemy.orm import Session
from ..database.models import AISummary, AISelection, NewsletterRun
from ..database import get_session
from ..obsidian import build_obsidian_uri
from ..logger import setup_logger


logger = setup_logger(__name__)


def build_newsletter_html(newsletter_run_id: int) -> str:
    """
    Build complete HTML newsletter from database summaries.

    Args:
        newsletter_run_id: ID of the newsletter run to build

    Returns:
        Complete HTML string ready for email

    Example:
        >>> run_id = generator.generate_news_digest_from_sources(...)
        >>> html = build_newsletter_html(run_id)
        >>> notifier.send(html, ...)
    """
    session = get_session()

    try:
        # Query all summaries for this run
        summaries = (
            session.query(AISummary)
            .join(AISelection)
            .filter(AISelection.newsletter_run_id == newsletter_run_id)
            .filter(AISelection.selected == True)
            .all()
        )

        if not summaries:
            logger.warning(f"No summaries found for run {newsletter_run_id}")
            return ""

        logger.info(f"Building newsletter with {len(summaries)} summaries")

        # Build HTML blocks
        html_blocks = []
        for summary in summaries:
            block = _build_summary_html(summary)
            if block:
                html_blocks.append(block)

        # Combine into complete newsletter
        newsletter_html = "\n\n".join(html_blocks)

        logger.info(f"Newsletter HTML built successfully ({len(newsletter_html)} chars)")
        return newsletter_html

    except Exception as e:
        logger.error(f"Error building newsletter: {e}", exc_info=True)
        return ""
    finally:
        session.close()


def _build_summary_html(summary: AISummary) -> str:
    """
    Build HTML block for a single summary with Obsidian link.

    Args:
        summary: AISummary database object

    Returns:
        HTML string for this summary
    """
    if not summary.title:
        logger.warning(f"Summary {summary.id} has no title, skipping")
        return ""

    parts = []

    # H3 Title
    parts.append(f"<h3>{summary.title}</h3>")

    # Waarom belangrijk
    if summary.why_matters:
        parts.append(f"<p><strong>Waarom het belangrijk is:</strong> {summary.why_matters}</p>")

    # Het grote plaatje
    if summary.big_picture:
        parts.append(f"<p><strong>Het grote plaatje:</strong> {summary.big_picture}</p>")

    # Belangrijkste details
    if summary.key_details:
        parts.append("<p><strong>Belangrijkste details:</strong></p>")
        parts.append("<ul>")
        for detail in summary.key_details.split('\n'):
            if detail.strip():
                parts.append(f"<li>{detail.strip()}</li>")
        parts.append("</ul>")

    # Volgende stap
    if summary.next_step:
        parts.append(f"<p><strong>Volgende stap:</strong> {summary.next_step}</p>")

    # Bron + Obsidian link
    if summary.source_name and summary.source_url:
        obs_uri = build_obsidian_uri(summary)

        if obs_uri:
            # Build source link with pipe separator and Obs button
            parts.append(
                f'<p><strong>Bron:</strong> '
                f'<a href="{summary.source_url}">{summary.source_name}</a> | '
                f'<a href="{obs_uri}">[Obs]</a></p>'
            )
        else:
            # Fallback: alleen bron link als Obsidian URI faalt
            parts.append(
                f'<p><strong>Bron:</strong> '
                f'<a href="{summary.source_url}">{summary.source_name}</a></p>'
            )
            logger.warning(f"Failed to build Obsidian URI for summary {summary.id}")

    # Horizontal rule
    parts.append("<hr>")

    return "\n".join(parts)


def build_newsletter_text(newsletter_run_id: int) -> str:
    """
    Build plain text newsletter from database summaries.

    Legacy fallback for email clients that don't support HTML.

    Args:
        newsletter_run_id: ID of the newsletter run to build

    Returns:
        Plain text string
    """
    session = get_session()

    try:
        summaries = (
            session.query(AISummary)
            .join(AISelection)
            .filter(AISelection.newsletter_run_id == newsletter_run_id)
            .filter(AISelection.selected == True)
            .all()
        )

        if not summaries:
            return ""

        text_blocks = []
        for summary in summaries:
            block = _build_summary_text(summary)
            if block:
                text_blocks.append(block)

        return "\n\n---\n\n".join(text_blocks)

    except Exception as e:
        logger.error(f"Error building text newsletter: {e}", exc_info=True)
        return ""
    finally:
        session.close()


def _build_summary_text(summary: AISummary) -> str:
    """
    Build plain text block for a single summary.

    Args:
        summary: AISummary database object

    Returns:
        Plain text string for this summary
    """
    if not summary.title:
        return ""

    parts = []

    # Title
    parts.append(f"### {summary.title}")
    parts.append("")

    # Waarom belangrijk
    if summary.why_matters:
        parts.append(f"**Waarom het belangrijk is:** {summary.why_matters}")
        parts.append("")

    # Het grote plaatje
    if summary.big_picture:
        parts.append(f"**Het grote plaatje:** {summary.big_picture}")
        parts.append("")

    # Belangrijkste details
    if summary.key_details:
        parts.append("**Belangrijkste details:**")
        for detail in summary.key_details.split('\n'):
            if detail.strip():
                parts.append(f"- {detail.strip()}")
        parts.append("")

    # Volgende stap
    if summary.next_step:
        parts.append(f"**Volgende stap:** {summary.next_step}")
        parts.append("")

    # Bron (plain text - no Obsidian link in text version)
    if summary.source_name and summary.source_url:
        parts.append(f"**Bron:** [{summary.source_name}]({summary.source_url})")

    return "\n".join(parts)
