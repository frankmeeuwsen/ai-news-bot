#!/usr/bin/env python3
"""
AI News Bot Preview Server

Run the preview server to test newsletters without sending them.

Usage:
    python preview.py                    # Start server on http://localhost:5000
    python preview.py --port 8080        # Use custom port
    python preview.py --host 0.0.0.0     # Bind to all interfaces
"""
import argparse
import sys
from src.preview import run_preview_server


def main():
    parser = argparse.ArgumentParser(
        description='AI News Bot Preview Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python preview.py                    Start server on http://localhost:5000
    python preview.py --port 8080        Use custom port
    python preview.py --host 0.0.0.0     Bind to all interfaces (network access)
    python preview.py --no-debug         Disable debug mode (for production)
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )

    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Disable debug mode'
    )

    args = parser.parse_args()

    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║           AI News Bot Preview Server                 ║
    ╠═══════════════════════════════════════════════════════╣
    ║  URL: http://{args.host}:{args.port:<24}     ║
    ║  Debug: {'Off' if args.no_debug else 'On ':<40}     ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    run_preview_server(
        host=args.host,
        port=args.port,
        debug=not args.no_debug
    )


if __name__ == '__main__':
    main()
