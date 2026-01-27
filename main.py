#!/usr/bin/env python3
"""
AI News Bot - Main Application

Generates and distributes daily AI news digests using Anthropic's Claude API.
"""
import sys
import argparse
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from src.config import Config
from src.logger import setup_logger
from src.news import NewsGenerator
from src.newsletter import build_newsletter_html
from src.database import init_db
from src.notifiers import (
    EmailNotifier,
    ResendNotifier,
    WebhookNotifier,
    SlackNotifier,
    TelegramNotifier,
    DiscordNotifier
)


def save_preview(html_content, language, run_id):
    """
    Save newsletter preview to file and open in browser.

    Args:
        html_content: Newsletter HTML content
        language: Language code (nl, en, etc.)
        run_id: Newsletter run ID

    Returns:
        Path to saved file
    """
    # Create preview directory if it doesn't exist
    preview_dir = Path("preview")
    preview_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newsletter_preview_{language}_{run_id}_{timestamp}.html"
    filepath = preview_dir / filename

    # Wrap in complete HTML document for browser viewing
    full_html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Digest - Preview ({language.upper()})</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f5f5f5;
        }}
        .preview-banner {{
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .preview-banner h2 {{
            margin: 0 0 10px 0;
            color: #856404;
        }}
        .preview-banner p {{
            margin: 0;
            color: #856404;
        }}
        .newsletter-content {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        ul {{
            padding-left: 20px;
        }}
        .metadata {{
            font-size: 0.9em;
            color: #666;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="preview-banner">
        <h2>🔍 Newsletter Preview Mode</h2>
        <p><strong>Language:</strong> {language.upper()} | <strong>Run ID:</strong> {run_id} | <strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p style="margin-top: 10px;">This is a preview - no notifications were sent</p>
    </div>

    <div class="newsletter-content">
        {html_content}
    </div>
</body>
</html>"""

    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return filepath


def main():
    """Main application entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="AI News Bot - Generates and distributes daily AI news digests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal run (generate and send newsletters)
  python main.py

  # Dry-run mode (generate but don't send, preview in browser)
  python main.py --dry-run

  # Preview specific language only
  python main.py --dry-run --language nl

  # Preview with custom output directory
  python main.py --dry-run --output-dir /tmp/previews
        """
    )

    parser.add_argument(
        '--dry-run', '--preview',
        action='store_true',
        dest='dry_run',
        help='Generate newsletter without sending (preview mode)'
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        help='Process only specific language (e.g., nl, en, zh)',
        metavar='LANG'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory for preview files (default: ./preview)',
        metavar='DIR'
    )

    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Don\'t open browser in dry-run mode'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = Config()

        # Setup logger with config
        logger = setup_logger(
            "ai_news_bot",
            level=config.log_level,
            log_format=config.log_format
        )

        # Get list of languages to process
        languages = config.ai_response_languages

        # Override with single language if specified
        if args.language:
            if args.language.lower() in languages:
                languages = [args.language.lower()]
                logger.info(f"Language override: processing only {args.language.upper()}")
            else:
                logger.error(f"Invalid language '{args.language}'. Available: {', '.join(languages)}")
                return 1

        # Dry-run mode setup
        if args.dry_run:
            logger.info("=" * 60)
            logger.info("🔍 DRY-RUN MODE ENABLED")
            logger.info("Newsletter will be generated but NOT sent")
            logger.info("Preview will be saved to files and opened in browser")
            logger.info("=" * 60)

        logger.info("=" * 60)
        logger.info("AI News Bot Starting")
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Mode: {'DRY-RUN (Preview)' if args.dry_run else 'PRODUCTION (Send)'}")
        logger.info(f"LLM Provider: {config.llm_provider}")
        if config.llm_model:
            logger.info(f"LLM Model: {config.llm_model}")
        logger.info(f"Languages: {', '.join(languages)}")
        logger.info(f"Web Search: {config.enable_web_search}")
        logger.info("=" * 60)

        # Initialize database for caching and tracking
        logger.info("Initializing database...")
        db_url = config.database_url
        init_db(db_url=db_url)
        logger.info(f"Database initialized: {config.database_type}")

        # Initialize news generator once
        logger.info("Initializing news generator...")
        news_gen = NewsGenerator(
            provider_name=config.llm_provider,
            api_key=config.llm_api_key,
            model=config.llm_model,
            enable_web_search=config.enable_web_search
        )

        # Get enabled notification methods
        notification_methods = config.notification_methods
        logger.info(f"Enabled notification methods: {notification_methods}")

        # Track overall results
        overall_results = {"sent": [], "failed": []}
        
        # Process each language
        for language in languages:
            logger.info("=" * 60)
            logger.info(f"Processing language: {language.upper()}")
            logger.info("=" * 60)

            try:
                # Generate news digest for this language (returns run_id)
                logger.info(f"Generating AI news digest in {language.upper()} from real-time sources...")
                run_id = news_gen.generate_news_digest_from_sources(
                    language=language,
                    max_items_per_source=config.max_items_per_source,
                    max_tokens=config.llm_max_tokens
                )

                logger.info(f"Newsletter run #{run_id} completed for {language.upper()}")

                # Build HTML newsletter from database
                logger.info(f"Building HTML newsletter from database...")
                news_digest = build_newsletter_html(run_id)

                if not news_digest:
                    logger.warning(f"Failed to build newsletter HTML for run #{run_id}")
                    raise Exception(f"Failed to build newsletter HTML for run #{run_id}")

                logger.info(f"Newsletter HTML generated ({len(news_digest)} characters)")
                logger.info("-" * 60)
                logger.info(f"News Digest Preview ({language.upper()}):")
                logger.info("-" * 60)
                # Print first 500 characters as preview
                preview = news_digest[:500] + "..." if len(news_digest) > 500 else news_digest
                logger.info(preview)
                logger.info("-" * 60)

                # DRY-RUN MODE: Save preview and skip sending
                if args.dry_run:
                    logger.info(f"💾 Saving preview for {language.upper()}...")

                    # Set output directory
                    if args.output_dir:
                        output_path = Path(args.output_dir)
                        output_path.mkdir(parents=True, exist_ok=True)
                        # Temporarily change to output dir for save_preview
                        old_cwd = os.getcwd()
                        os.chdir(args.output_dir)
                        filepath = save_preview(news_digest, language, run_id)
                        os.chdir(old_cwd)
                        filepath = output_path / filepath.name
                    else:
                        filepath = save_preview(news_digest, language, run_id)

                    logger.info(f"✅ Preview saved: {filepath}")

                    # Open in browser unless --no-browser specified
                    if not args.no_browser:
                        logger.info(f"🌐 Opening preview in browser...")
                        webbrowser.open(f'file://{filepath.absolute()}')

                    # Mark as "sent" for dry-run (for summary)
                    overall_results["sent"].append(f"preview ({language.upper()})")

                    logger.info(f"Language {language.upper()} preview completed")
                    continue  # Skip to next language

                # Track notification results for this language
                lang_results = {"sent": [], "failed": []}

                # Send email notification if enabled
                if "email" in notification_methods:
                    logger.info(f"Sending email notification for {language.upper()}...")

                    # Select email provider based on config
                    email_provider = config.email_provider
                    if email_provider == "resend":
                        email_notifier = ResendNotifier()
                    else:
                        email_notifier = EmailNotifier()

                    if email_notifier.send(news_digest, language=language):
                        lang_results["sent"].append("email")
                        logger.info(f"Email notification sent successfully for {language.upper()}")
                    else:
                        lang_results["failed"].append("email")
                        logger.warning(f"Email notification failed for {language.upper()}")

                # Send webhook notification if enabled
                if "webhook" in notification_methods:
                    logger.info(f"Sending webhook notification for {language.upper()}...")
                    webhook_notifier = WebhookNotifier()
                    if webhook_notifier.send(news_digest, language=language):
                        lang_results["sent"].append("webhook")
                        logger.info(f"Webhook notification sent successfully for {language.upper()}")
                    else:
                        lang_results["failed"].append("webhook")
                        logger.warning(f"Webhook notification failed for {language.upper()}")

                # Send Slack notification if enabled
                if "slack" in notification_methods:
                    logger.info(f"Sending Slack notification for {language.upper()}...")
                    slack_notifier = SlackNotifier()
                    if slack_notifier.send(news_digest, language=language):
                        lang_results["sent"].append("slack")
                        logger.info(f"Slack notification sent successfully for {language.upper()}")
                    else:
                        lang_results["failed"].append("slack")
                        logger.warning(f"Slack notification failed for {language.upper()}")

                # Send Telegram notification if enabled
                if "telegram" in notification_methods:
                    logger.info(f"Sending Telegram notification for {language.upper()}...")
                    telegram_notifier = TelegramNotifier()
                    if telegram_notifier.send(news_digest, language=language):
                        lang_results["sent"].append("telegram")
                        logger.info(f"Telegram notification sent successfully for {language.upper()}")
                    else:
                        lang_results["failed"].append("telegram")
                        logger.warning(f"Telegram notification failed for {language.upper()}")

                # Send Discord notification if enabled
                if "discord" in notification_methods:
                    logger.info(f"Sending Discord notification for {language.upper()}...")
                    discord_notifier = DiscordNotifier()
                    if discord_notifier.send(news_digest, language=language):
                        lang_results["sent"].append("discord")
                        logger.info(f"Discord notification sent successfully for {language.upper()}")
                    else:
                        lang_results["failed"].append("discord")
                        logger.warning(f"Discord notification failed for {language.upper()}")

                # Update overall results
                for method in lang_results["sent"]:
                    result_key = f"{method} ({language.upper()})"
                    if result_key not in overall_results["sent"]:
                        overall_results["sent"].append(result_key)
                
                for method in lang_results["failed"]:
                    result_key = f"{method} ({language.upper()})"
                    if result_key not in overall_results["failed"]:
                        overall_results["failed"].append(result_key)

                logger.info(f"Language {language.upper()} completed successfully")

            except Exception as lang_error:
                logger.error(f"Error processing language {language.upper()}: {str(lang_error)}", exc_info=True)
                # Mark all notification methods as failed for this language
                for method in notification_methods:
                    result_key = f"{method} ({language.upper()})"
                    if result_key not in overall_results["failed"]:
                        overall_results["failed"].append(result_key)

        # Final Summary
        logger.info("=" * 60)
        logger.info("AI News Bot Completed")
        logger.info(f"Processed {len(languages)} language(s): {', '.join(lang.upper() for lang in languages)}")
        logger.info(f"Successfully sent: {', '.join(overall_results['sent']) if overall_results['sent'] else 'None'}")
        if overall_results["failed"]:
            logger.warning(f"Failed to send: {', '.join(overall_results['failed'])}")
        logger.info("=" * 60)

        # Return exit code based on results
        if notification_methods and not overall_results["sent"]:
            logger.error("All notifications failed")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
