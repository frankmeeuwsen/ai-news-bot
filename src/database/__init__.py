"""
Database module for AI News Bot

Provides SQLAlchemy models and database connections for:
- News items caching
- AI selection tracking
- Newsletter run statistics
- RSS feed health monitoring
"""
from .models import (
    NewsItem,
    AISelection,
    AISummary,
    NewsletterRun,
    RSSHealth,
    UserFeedback
)
from .db import get_session, init_db, session_scope

__all__ = [
    'NewsItem',
    'AISelection',
    'AISummary',
    'NewsletterRun',
    'RSSHealth',
    'UserFeedback',
    'get_session',
    'init_db',
    'session_scope'
]
