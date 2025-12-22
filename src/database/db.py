"""
Database connection and session management voor AI News Bot

Provides:
- Database initialization (create tables)
- Session factory voor database operations
- Context manager voor safe session handling
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from ..logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """
    Singleton database manager voor AI News Bot.

    Handles database connection, session management en initialization.
    """

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        """Singleton pattern om één database connectie te garanderen."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def init_db(self, db_url: str = None, echo: bool = False):
        """
        Initialize database connection en create tables.

        Args:
            db_url: SQLAlchemy database URL. Als None, gebruikt SQLite default.
            echo: Enable SQL query logging (voor debugging)
        """
        if self._engine is not None:
            logger.warning("Database already initialized, skipping re-initialization")
            return

        # Default naar SQLite als geen URL opgegeven
        if db_url is None:
            data_dir = self._get_data_dir()
            db_path = os.path.join(data_dir, 'newsbot.db')
            db_url = f'sqlite:///{db_path}'
            logger.info(f"Using SQLite database at: {db_path}")

        # Zorg dat directory bestaat voor SQLite databases (voordat engine wordt aangemaakt)
        if db_url.startswith('sqlite:///'):
            db_file_path = db_url.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_file_path)
            if db_dir:  # Alleen als er een directory pad is
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Ensured database directory exists: {db_dir}")

        # Create engine
        self._engine = create_engine(
            db_url,
            echo=echo,
            # SQLite specific optimizations
            connect_args={'check_same_thread': False} if db_url.startswith('sqlite') else {}
        )

        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(self._engine)
        logger.info("Database initialized successfully")

    def _get_data_dir(self) -> str:
        """
        Get data directory path (project_root/data).

        Returns:
            Absolute path naar data directory
        """
        # Get project root (3 levels up from this file: src/database/db.py -> src/database -> src -> root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, 'data')
        return data_dir

    def get_session(self) -> Session:
        """
        Get nieuwe database session.

        Returns:
            SQLAlchemy Session object

        Raises:
            RuntimeError: Als database niet geïnitialiseerd is
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Database not initialized. Call init_db() first."
            )
        return self._session_factory()

    @contextmanager
    def session_scope(self):
        """
        Context manager voor safe session handling.

        Automatically commits on success, rolls back on error.

        Usage:
            with db_manager.session_scope() as session:
                session.add(news_item)
                # auto-commit on exit
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection (voor cleanup)."""
        if self._engine is not None:
            self._engine.dispose()
            logger.info("Database connection closed")
            self._engine = None
            self._session_factory = None


# Global database manager instance
_db_manager = DatabaseManager()


def init_db(db_url: str = None, echo: bool = False):
    """
    Initialize database connection en create tables.

    Args:
        db_url: SQLAlchemy database URL. Als None, gebruikt SQLite default.
        echo: Enable SQL query logging (voor debugging)

    Example:
        # SQLite (default)
        init_db()

        # PostgreSQL
        init_db("postgresql://user:pass@localhost/newsbot")

        # Debug mode (logs alle queries)
        init_db(echo=True)
    """
    _db_manager.init_db(db_url=db_url, echo=echo)


def get_session() -> Session:
    """
    Get nieuwe database session.

    Returns:
        SQLAlchemy Session object

    Example:
        session = get_session()
        news_items = session.query(NewsItem).filter_by(language='en').all()
        session.close()
    """
    return _db_manager.get_session()


@contextmanager
def session_scope():
    """
    Context manager voor safe session handling.

    Example:
        with session_scope() as session:
            news_item = NewsItem(title="Test", link="http://example.com")
            session.add(news_item)
            # auto-commit on exit
    """
    with _db_manager.session_scope() as session:
        yield session


def close_db():
    """Close database connection (voor cleanup)."""
    _db_manager.close()
