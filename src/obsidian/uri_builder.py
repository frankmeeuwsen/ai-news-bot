"""
Build Obsidian URIs voor het opslaan van nieuwsitems in Obsidian vault.

Deze module genereert betrouwbare obsidian:// URIs uit database summaries,
zonder afhankelijkheid van LLM output.
"""
import urllib.parse
from typing import Optional
from ..database.models import AISummary
from ..logger import setup_logger


logger = setup_logger(__name__)


# Configuratie
VAULT_NAME = "frankopedia"
BASE_PATH = "4 - Resources/AI"


def sanitize_filename(title: str) -> str:
    r"""
    Sanitize titel voor gebruik als Obsidian bestandsnaam.

    Obsidian bestandsnamen kunnen NIET deze karakters bevatten: / \ : * ? " < > |

    Replace strategie:
    - `:` → ` -` (dubbele punt naar spatie-dash, vaak gebruikt in titels)
    - `/` → `-` (slash naar dash)
    - `\` → `-` (backslash naar dash)
    - `*` → `` (asterisk verwijderen)
    - `?` → `` (vraagteken verwijderen)
    - `"` → `'` (dubbele quote naar enkele quote)
    - `<` → `` (kleiner dan verwijderen)
    - `>` → `` (groter dan verwijderen)
    - `|` → `-` (pipe naar dash)

    Args:
        title: Originele titel die ongeldige karakters kan bevatten

    Returns:
        Gesanitizeerde titel safe voor gebruik als bestandsnaam

    Examples:
        >>> sanitize_filename("AI: De nieuwe revolutie")
        'AI - De nieuwe revolutie'
        >>> sanitize_filename("GPT-4/Claude vergelijking")
        'GPT-4-Claude vergelijking'
        >>> sanitize_filename('Wat is "prompt engineering"?')
        "Wat is 'prompt engineering'"
    """
    if not title:
        return ""

    # Replace karakters met equivalenten
    sanitized = title
    sanitized = sanitized.replace(':', ' -')  # Dubbele punt → spatie-dash
    sanitized = sanitized.replace('/', '-')   # Slash → dash
    sanitized = sanitized.replace('\\', '-')  # Backslash → dash
    sanitized = sanitized.replace('|', '-')   # Pipe → dash
    sanitized = sanitized.replace('"', "'")   # Dubbele quote → enkele quote

    # Verwijder karakters die geen goede vervanging hebben
    sanitized = sanitized.replace('*', '')
    sanitized = sanitized.replace('?', '')
    sanitized = sanitized.replace('<', '')
    sanitized = sanitized.replace('>', '')

    # Clean up multiple spaces/dashes
    while '  ' in sanitized:
        sanitized = sanitized.replace('  ', ' ')
    while '--' in sanitized:
        sanitized = sanitized.replace('--', '-')

    # Strip leading/trailing whitespace and dashes
    sanitized = sanitized.strip(' -')

    return sanitized


def build_obsidian_uri(summary: AISummary, vault_name: str = VAULT_NAME) -> str:
    """
    Bouw complete Obsidian URI uit database summary.

    Args:
        summary: AISummary database object met structured fields
        vault_name: Naam van de Obsidian vault (default: frankopedia)

    Returns:
        Volledig geformatteerde obsidian://new URI string

    Example:
        >>> summary = AISummary(
        ...     title="Google lanceert Gemini 3",
        ...     why_matters="Frontier AI tegen lagere kosten",
        ...     big_picture="Google DeepMind introduceert...",
        ...     key_details="Detail 1\\nDetail 2",
        ...     next_step="Beschikbaar via API",
        ...     source_name="DeepMind Blog",
        ...     source_url="https://..."
        ... )
        >>> uri = build_obsidian_uri(summary)
        >>> uri.startswith('obsidian://new?vault=frankopedia')
        True
    """
    if not summary.title:
        logger.error(f"Summary {summary.id} has no title, cannot build URI")
        return ""

    # Build markdown content
    content = _build_markdown_content(summary)

    # URL encode content
    encoded_content = urllib.parse.quote(content, safe='')

    # Sanitize titel voor gebruik als bestandsnaam (verwijder ongeldige karakters)
    safe_title = sanitize_filename(summary.title)

    # Construct file path
    file_path = f"{BASE_PATH}/{safe_title}"

    # Build complete URI (encode het hele file path als query parameter)
    uri = (
        f"obsidian://new"
        f"?vault={vault_name}"
        f"&file={urllib.parse.quote(file_path, safe='')}"
        f"&content={encoded_content}"
        f"&silent=true"
    )

    logger.debug(f"Built Obsidian URI for: {summary.title}")
    return uri


def _build_markdown_content(summary: AISummary) -> str:
    """
    Bouw markdown content voor Obsidian notitie.

    Args:
        summary: AISummary object

    Returns:
        Complete markdown string met frontmatter en content
    """
    # Build frontmatter with dynamic onderwerp
    frontmatter = f"""---
aliases:
context:
  - "[[Thema - Artificial Intelligence]]"
type:
  - "[[Artikel]]"
onderwerp: {summary.why_matters if summary.why_matters else ""}
---"""

    parts = [frontmatter, ""]

    # H1 Title
    parts.append(f"# {summary.title}")
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
        # key_details is newline-separated
        for detail in summary.key_details.split('\n'):
            if detail.strip():
                parts.append(f"- {detail.strip()}")
        parts.append("")

    # Volgende stap
    if summary.next_step:
        parts.append(f"**Volgende stap:** {summary.next_step}")
        parts.append("")

    # Bron
    if summary.source_name and summary.source_url:
        parts.append(f"**Bron:** [{summary.source_name}]({summary.source_url})")

    return "\n".join(parts)


def build_uri_from_dict(summary_dict: dict, vault_name: str = VAULT_NAME) -> str:
    """
    Build Obsidian URI uit dictionary (voor testing zonder database).

    Args:
        summary_dict: Dictionary met summary fields
        vault_name: Naam van de Obsidian vault

    Returns:
        Obsidian URI string
    """
    # Create mock AISummary object
    class MockSummary:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    mock = MockSummary(
        id=summary_dict.get('id', 0),
        title=summary_dict.get('title', ''),
        why_matters=summary_dict.get('why_matters', ''),
        big_picture=summary_dict.get('big_picture', ''),
        key_details=summary_dict.get('key_details', ''),
        next_step=summary_dict.get('next_step', ''),
        source_name=summary_dict.get('source_name', ''),
        source_url=summary_dict.get('source_url', '')
    )

    return build_obsidian_uri(mock, vault_name)
