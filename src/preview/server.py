"""
Flask Preview Server for AI News Bot

Provides web interface for:
- Viewing generated newsletters
- Generating test newsletters from database items
- Providing feedback on content quality
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
import markdown
from ..database import init_db, session_scope, NewsletterRun, AISummary, AISelection, UserFeedback
from ..config import Config
from ..logger import setup_logger
from .loader import TestDataLoader
from .test_generator import TestNewsGenerator


logger = setup_logger(__name__)


def create_app(config: Config = None) -> Flask:
    """
    Create Flask application for preview server.

    Args:
        config: Config object (creates new one if None)

    Returns:
        Flask application
    """
    # Get template directory
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')

    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = os.urandom(24)

    # Store config
    if config is None:
        config = Config()
    app.config['NEWS_CONFIG'] = config

    # Initialize database
    init_db(db_url=config.database_url)

    # Initialize components
    loader = TestDataLoader()

    @app.route('/')
    def index():
        """Home page with test run overview"""
        # Get stats
        stats = loader.get_stats(language='nl')

        # Get recent test runs
        with session_scope() as session:
            runs = session.query(NewsletterRun).filter(
                NewsletterRun.status.in_(['test_run', 'success'])
            ).order_by(
                NewsletterRun.run_date.desc()
            ).limit(10).all()

            test_runs = []
            for run in runs:
                test_runs.append({
                    'id': run.id,
                    'date': run.run_date.strftime('%Y-%m-%d %H:%M'),
                    'language': run.language,
                    'provider': run.provider,
                    'model': run.model or 'default',
                    'items': run.items_summarized or 0,
                    'tokens': run.stage2_tokens or 0,
                    'cost': run.total_cost or 0,
                    'status': run.status
                })

        return render_template('index.html', stats=stats, test_runs=test_runs)

    @app.route('/generate', methods=['GET', 'POST'])
    def generate():
        """Generate new test newsletter"""
        if request.method == 'GET':
            # Show form with available items
            items = loader.get_recent_items(language='nl', hours=48, limit=50)
            return render_template('generate.html', items=items)

        # POST - generate newsletter
        item_ids = request.form.getlist('items')
        if not item_ids:
            # Use random sample if no selection
            items = loader.get_random_sample(language='nl', count=15)
        else:
            items = loader.get_items_by_ids([int(id) for id in item_ids])

        if not items:
            return render_template('error.html', message="No items available for generation")

        # Generate newsletter
        try:
            generator = TestNewsGenerator()
            result = generator.generate_from_items(
                items=items,
                language='nl',
                save_to_db=True
            )
            return redirect(url_for('view_run', run_id=result['run_id']))
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            return render_template('error.html', message=str(e))

    @app.route('/run/<int:run_id>')
    def view_run(run_id: int):
        """View a specific newsletter run"""
        with session_scope() as session:
            run = session.query(NewsletterRun).get(run_id)
            if not run:
                return render_template('error.html', message="Run not found")

            # Get the summary (newsletter content)
            summary = session.query(AISummary).join(AISelection).filter(
                AISelection.newsletter_run_id == run_id
            ).first()

            newsletter_text = summary.summary_text if summary else "No content available"

            # Convert markdown to HTML
            newsletter_html = markdown.markdown(
                newsletter_text,
                extensions=['tables', 'fenced_code', 'nl2br']
            )

            # Get feedback for this run
            feedbacks = []
            if summary:
                fb_list = session.query(UserFeedback).filter(
                    UserFeedback.summary_id == summary.id
                ).all()
                for fb in fb_list:
                    feedbacks.append({
                        'type': fb.feedback_type,
                        'value': fb.feedback_value,
                        'timestamp': fb.timestamp.strftime('%Y-%m-%d %H:%M')
                    })

            run_data = {
                'id': run.id,
                'date': run.run_date.strftime('%Y-%m-%d %H:%M'),
                'language': run.language,
                'provider': run.provider,
                'model': run.model or 'default',
                'items': run.items_summarized or 0,
                'tokens': run.stage2_tokens or 0,
                'cost': run.total_cost or 0,
                'runtime': run.runtime_seconds or 0,
                'prompt_hash': run.stage2_prompt_hash or 'unknown',
                'status': run.status
            }

            return render_template(
                'view_run.html',
                run=run_data,
                newsletter_html=newsletter_html,
                newsletter_text=newsletter_text,
                feedbacks=feedbacks,
                summary_id=summary.id if summary else None
            )

    @app.route('/api/feedback', methods=['POST'])
    def submit_feedback():
        """Submit feedback for a newsletter"""
        data = request.json
        summary_id = data.get('summary_id')
        feedback_type = data.get('type')  # thumbs_up, thumbs_down, comment
        feedback_value = data.get('value', 0)

        if not summary_id or not feedback_type:
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            with session_scope() as session:
                feedback = UserFeedback(
                    summary_id=summary_id,
                    feedback_type=feedback_type,
                    feedback_value=feedback_value,
                    timestamp=datetime.utcnow()
                )
                session.add(feedback)

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Feedback error: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/stats')
    def api_stats():
        """Get database stats as JSON"""
        stats = loader.get_stats(language='nl')
        return jsonify(stats)

    @app.route('/api/items')
    def api_items():
        """Get recent items as JSON"""
        hours = request.args.get('hours', 48, type=int)
        limit = request.args.get('limit', 50, type=int)
        language = request.args.get('language', 'nl')

        items = loader.get_recent_items(language=language, hours=hours, limit=limit)
        return jsonify(items)

    @app.route('/compare')
    def compare():
        """Compare multiple newsletter runs"""
        with session_scope() as session:
            runs = session.query(NewsletterRun).filter(
                NewsletterRun.status.in_(['test_run', 'success'])
            ).order_by(
                NewsletterRun.run_date.desc()
            ).limit(20).all()

            comparisons = []
            for run in runs:
                summary = session.query(AISummary).join(AISelection).filter(
                    AISelection.newsletter_run_id == run.id
                ).first()

                comparisons.append({
                    'id': run.id,
                    'date': run.run_date.strftime('%Y-%m-%d %H:%M'),
                    'prompt_hash': run.stage2_prompt_hash or 'unknown',
                    'items': run.items_summarized or 0,
                    'tokens': run.stage2_tokens or 0,
                    'cost': run.total_cost or 0,
                    'preview': summary.summary_text[:500] if summary else 'No content'
                })

        return render_template('compare.html', comparisons=comparisons)

    return app


def run_preview_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = True):
    """
    Run the preview server.

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    app = create_app()
    logger.info(f"Starting preview server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
