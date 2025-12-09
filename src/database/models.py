"""
SQLAlchemy database models for AI News Bot

Schema design:
- NewsItem: Opgehaalde RSS feed items (met caching)
- AISelection: Stage 1 selectie resultaten
- AISummary: Stage 2 gegenereerde samenvattingen
- NewsletterRun: Metadata per bot run (kosten, tokens, timing)
- RSSHealth: RSS feed monitoring en health checks
- UserFeedback: User feedback voor ML/serendipity (toekomstig)
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    DateTime, ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class NewsItem(Base):
    """
    Opgehaalde RSS feed items met caching support.

    Uniek per link (of GUID als beschikbaar) om duplicaten te voorkomen.
    Wordt hergebruikt binnen cache TTL (36 uur).
    """
    __tablename__ = 'news_items'

    id = Column(Integer, primary_key=True)

    # RSS feed metadata
    source = Column(String(255), nullable=False, index=True)  # bijv. "TechCrunch"
    title = Column(Text, nullable=False)
    link = Column(String(2048), nullable=False, unique=True, index=True)  # Primaire unique identifier
    guid = Column(String(2048), nullable=True, index=True)  # GUID indien beschikbaar in RSS
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)  # Publicatiedatum uit RSS

    # Bot metadata
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    language = Column(String(10), nullable=False, index=True)  # en/nl/zh/etc.
    category = Column(String(50), nullable=False)  # international/domestic

    # Raw data voor debugging/reference
    raw_data = Column(JSON, nullable=True)  # Volledige RSS entry als JSON

    # Relationships
    selections = relationship("AISelection", back_populates="news_item", cascade="all, delete-orphan")

    # Indexes voor performance
    __table_args__ = (
        Index('idx_fetched_lang_cat', 'fetched_at', 'language', 'category'),
        Index('idx_source_fetched', 'source', 'fetched_at'),
    )

    def __repr__(self):
        return f"<NewsItem(id={self.id}, source='{self.source}', title='{self.title[:50]}...')>"


class NewsletterRun(Base):
    """
    Metadata voor elke newsletter run.

    Tracked kosten, tokens, timing en status per editie.
    """
    __tablename__ = 'newsletter_runs'

    id = Column(Integer, primary_key=True)

    # Run metadata
    run_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    language = Column(String(10), nullable=False, index=True)

    # LLM provider info
    provider = Column(String(50), nullable=False)  # claude/deepseek/openrouter/etc.
    model = Column(String(100), nullable=False)

    # Stage 1 metrics
    stage1_prompt_hash = Column(String(64), nullable=True)  # Voor A/B testing
    stage1_tokens = Column(Integer, nullable=True)
    stage1_cost = Column(Float, nullable=True)

    # Stage 2 metrics
    stage2_prompt_hash = Column(String(64), nullable=True)
    stage2_tokens = Column(Integer, nullable=True)
    stage2_cost = Column(Float, nullable=True)

    # Totals
    total_cost = Column(Float, nullable=True)
    runtime_seconds = Column(Float, nullable=True)

    # Counts
    items_fetched = Column(Integer, nullable=True)
    items_selected = Column(Integer, nullable=True)
    items_summarized = Column(Integer, nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, default='running')  # running/success/failed
    error_message = Column(Text, nullable=True)

    # Relationships
    selections = relationship("AISelection", back_populates="newsletter_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NewsletterRun(id={self.id}, date={self.run_date}, lang='{self.language}', status='{self.status}')>"


class AISelection(Base):
    """
    Stage 1 selectie resultaten.

    Tracked welke items AI selecteerde/negeerde en waarom.
    """
    __tablename__ = 'ai_selections'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    news_item_id = Column(Integer, ForeignKey('news_items.id'), nullable=False, index=True)
    newsletter_run_id = Column(Integer, ForeignKey('newsletter_runs.id'), nullable=False, index=True)

    # Selection data
    selected = Column(Boolean, nullable=False, default=False, index=True)
    selection_reason = Column(Text, nullable=True)  # Waarom AI het selecteerde (als beschikbaar)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    news_item = relationship("NewsItem", back_populates="selections")
    newsletter_run = relationship("NewsletterRun", back_populates="selections")
    summary = relationship("AISummary", back_populates="selection", uselist=False, cascade="all, delete-orphan")

    # Ensure one selection per item per run
    __table_args__ = (
        UniqueConstraint('news_item_id', 'newsletter_run_id', name='uq_item_run'),
    )

    def __repr__(self):
        return f"<AISelection(id={self.id}, selected={self.selected}, item_id={self.news_item_id})>"


class AISummary(Base):
    """
    Stage 2 gegenereerde samenvattingen.

    Bevat geformatteerde tekst en metadata over token gebruik.
    """
    __tablename__ = 'ai_summaries'

    id = Column(Integer, primary_key=True)

    # Foreign key
    selection_id = Column(Integer, ForeignKey('ai_selections.id'), nullable=False, unique=True, index=True)

    # Summary content
    summary_text = Column(Text, nullable=False)  # Plain text versie
    summary_html = Column(Text, nullable=True)  # HTML geformatteerd (toekomstig)

    # Metadata
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    selection = relationship("AISelection", back_populates="summary")
    feedbacks = relationship("UserFeedback", back_populates="summary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AISummary(id={self.id}, selection_id={self.selection_id}, length={len(self.summary_text)})>"


class RSSHealth(Base):
    """
    RSS feed health monitoring.

    Tracked success/failure rates en auto-disable broken feeds.
    """
    __tablename__ = 'rss_health'

    id = Column(Integer, primary_key=True)

    # Feed identifiers
    source_name = Column(String(255), nullable=False, unique=True, index=True)
    feed_url = Column(String(2048), nullable=False)
    language = Column(String(10), nullable=True, index=True)

    # Health tracking
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    consecutive_fails = Column(Integer, nullable=False, default=0)
    total_fetches = Column(Integer, nullable=False, default=0)
    total_failures = Column(Integer, nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    error_details = Column(Text, nullable=True)  # Laatste error message

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RSSHealth(source='{self.source_name}', active={self.is_active}, fails={self.consecutive_fails})>"


class UserFeedback(Base):
    """
    User feedback voor ML/serendipity algoritme.

    Tracked thumbs up/down en clicks voor personalisatie.
    (Toekomstig: voor serendipity en feedback loops)
    """
    __tablename__ = 'user_feedback'

    id = Column(Integer, primary_key=True)

    # Foreign key
    summary_id = Column(Integer, ForeignKey('ai_summaries.id'), nullable=False, index=True)

    # User identification (voor multi-user later)
    user_id = Column(String(255), nullable=True, index=True)  # Email of UUID

    # Feedback data
    feedback_type = Column(String(50), nullable=False, index=True)  # thumbs_up/thumbs_down/click/open
    feedback_value = Column(Integer, nullable=True)  # -1, 0, +1 of dwell time

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    summary = relationship("AISummary", back_populates="feedbacks")

    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type='{self.feedback_type}', summary_id={self.summary_id})>"
