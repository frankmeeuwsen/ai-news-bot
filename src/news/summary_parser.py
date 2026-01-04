"""
Parse LLM-generated newsletter markdown naar structured data.

Extraheert title, why_matters, big_picture, key_details, next_step en source info
uit de markdown output van Stage 2 summarization.
"""
import re
from typing import List, Dict, Optional
from ..logger import setup_logger


logger = setup_logger(__name__)


def parse_summaries(markdown_text: str) -> List[Dict[str, str]]:
    """
    Parse LLM markdown output naar lijst van structured summaries.

    Args:
        markdown_text: Complete markdown output van LLM Stage 2

    Returns:
        List van dictionaries met keys:
        - title: H3 koptekst
        - why_matters: "Waarom belangrijk" sectie
        - big_picture: "Het grote plaatje" sectie
        - key_details: Newline-separated bulletpoints
        - next_step: "Volgende stap" sectie
        - source_name: Bron naam (uit markdown link)
        - source_url: Bron URL

    Example:
        >>> text = '''
        ... ### Google lanceert Gemini 3
        ... **Waarom het belangrijk is:** Frontier AI tegen lagere kosten
        ... **Het grote plaatje:** Google DeepMind introduceert...
        ... **Belangrijkste details:**
        ... - Detail 1
        ... - Detail 2
        ... **Volgende stap:** Beschikbaar via API
        ... [Bron: DeepMind](https://...)
        ... '''
        >>> summaries = parse_summaries(text)
        >>> summaries[0]['title']
        'Google lanceert Gemini 3'
    """
    summaries = []

    # Split op H3 headers (### Title)
    # Pattern: ### gevolgd door tekst tot volgende ### of einde
    h3_pattern = r'###\s+([^\n]+)'
    h3_matches = list(re.finditer(h3_pattern, markdown_text))

    if not h3_matches:
        logger.warning("No H3 headers found in markdown")
        return summaries

    logger.info(f"Found {len(h3_matches)} H3 headers to parse")

    for i, match in enumerate(h3_matches):
        # Extract block content (from this H3 to next H3 or end)
        start_pos = match.start()
        end_pos = h3_matches[i+1].start() if i+1 < len(h3_matches) else len(markdown_text)
        block = markdown_text[start_pos:end_pos]

        try:
            summary = _parse_single_summary(block)
            if summary:
                summaries.append(summary)
        except Exception as e:
            logger.error(f"Error parsing summary block: {e}", exc_info=True)
            logger.debug(f"Problematic block (first 200 chars): {block[:200]}")
            continue

    logger.info(f"Successfully parsed {len(summaries)} summaries")
    return summaries


def _parse_single_summary(block: str) -> Optional[Dict[str, str]]:
    """
    Parse een enkel H3 block naar structured data.

    Args:
        block: Markdown text van één nieuwsitem

    Returns:
        Dictionary met summary data, of None bij parse fouten
    """
    summary = {}

    # Extract title (eerste regel na ###)
    title_match = re.search(r'###\s+([^\n]+)', block)
    if not title_match:
        logger.warning("No title found in block")
        return None
    summary['title'] = title_match.group(1).strip()

    # Extract "Waarom het belangrijk is"
    why_match = re.search(
        r'\*\*Waarom het belangrijk is:?\*\*\s*([^\n*]+)',
        block,
        re.IGNORECASE
    )
    summary['why_matters'] = why_match.group(1).strip() if why_match else ""

    # Extract "Het grote plaatje"
    big_match = re.search(
        r'\*\*Het grote plaatje:?\*\*\s*([^\n*]+(?:\n(?!\*\*)[^\n]+)*)',
        block,
        re.IGNORECASE
    )
    summary['big_picture'] = big_match.group(1).strip() if big_match else ""

    # Extract "Belangrijkste details" (bulletpoints)
    details_match = re.search(
        r'\*\*Belangrijkste details:?\*\*\s*\n((?:[-•]\s*[^\n]+\n?)+)',
        block,
        re.IGNORECASE
    )
    if details_match:
        # Extract bullets and clean them
        bullets_text = details_match.group(1)
        bullets = re.findall(r'[-•]\s*([^\n]+)', bullets_text)
        summary['key_details'] = '\n'.join(b.strip() for b in bullets)
    else:
        summary['key_details'] = ""

    # Extract "Volgende stap"
    next_match = re.search(
        r'\*\*Volgende stap:?\*\*\s*([^\n*]+)',
        block,
        re.IGNORECASE
    )
    summary['next_step'] = next_match.group(1).strip() if next_match else ""

    # Extract source (bronlink)
    # Pattern: [Bron: Name](URL) of [Name](URL)
    source_match = re.search(
        r'\[(?:Bron:\s*)?([^\]]+)\]\(([^)]+)\)',
        block
    )
    if source_match:
        summary['source_name'] = source_match.group(1).strip()
        summary['source_url'] = source_match.group(2).strip()
    else:
        logger.warning(f"No source link found for: {summary['title']}")
        summary['source_name'] = ""
        summary['source_url'] = ""

    # Validation: Moet minstens title en one content field hebben
    has_content = any([
        summary.get('why_matters'),
        summary.get('big_picture'),
        summary.get('key_details')
    ])

    if not has_content:
        logger.warning(f"Summary for '{summary['title']}' has no content fields")
        return None

    logger.debug(f"Parsed summary: {summary['title']}")
    return summary


def parse_source_link(markdown_link: str) -> tuple[str, str]:
    """
    Parse een markdown link naar (name, url) tuple.

    Args:
        markdown_link: Markdown formatted link zoals "[Name](URL)"

    Returns:
        Tuple van (source_name, source_url)

    Example:
        >>> parse_source_link("[DeepMind Blog](https://deepmind.google/blog/...)")
        ('DeepMind Blog', 'https://deepmind.google/blog/...')
    """
    match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', markdown_link)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", ""


def format_summaries_to_markdown(summaries: List[Dict[str, str]], language: str = 'nl') -> str:
    """
    Format lijst van summaries terug naar markdown digest.

    Args:
        summaries: List van summary dictionaries
        language: Taalcode (nl/en/etc)

    Returns:
        Geformatteerde markdown digest tekst
    """
    output = []

    for summary in summaries:
        # Title als H3
        output.append(f"### {summary['title']}\n")

        # Why matters
        if summary.get('why_matters'):
            output.append(f"**Waarom het belangrijk is:** {summary['why_matters']}\n")

        # Big picture
        if summary.get('big_picture'):
            output.append(f"**Het grote plaatje:** {summary['big_picture']}\n")

        # Key details als bullets
        if summary.get('key_details'):
            output.append("**Belangrijkste details:**\n")
            for detail in summary['key_details'].split('\n'):
                if detail.strip():
                    output.append(f"- {detail.strip()}\n")

        # Next step
        if summary.get('next_step'):
            output.append(f"**Volgende stap:** {summary['next_step']}\n")

        # Source link
        if summary.get('source_url') and summary.get('source_name'):
            output.append(f"[Bron: {summary['source_name']}]({summary['source_url']})\n")

        # Separator tussen items
        output.append("\n")

    return ''.join(output)
