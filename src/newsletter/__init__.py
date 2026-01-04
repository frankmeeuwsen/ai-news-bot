"""
Newsletter building module.

Generates HTML newsletters from database summaries with Obsidian integration.
"""
from .builder import build_newsletter_html

__all__ = ['build_newsletter_html']
