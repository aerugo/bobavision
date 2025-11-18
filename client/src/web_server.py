"""
Web server for serving UI assets (HTML/CSS/JS).

This module provides a Flask-based HTTP server that serves the kid-friendly
UI screens (splash, loading, error, all done) along with static assets.
"""
import os
import threading
from pathlib import Path
from flask import Flask, send_from_directory, send_file


class WebServer:
    """HTTP server for serving UI assets to Chromium."""

    def __init__(self, port=5000):
        """
        Initialize the web server.

        Args:
            port: Port number to run the server on (default: 5000)
        """
        self.port = port
        self.running = False
        self.thread = None

        # Get path to UI directory
        client_dir = Path(__file__).parent.parent
        self.ui_dir = client_dir / 'ui'

        # Create Flask app
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        """Set up Flask routes for serving UI files."""

        @self.app.route('/')
        def splash():
            """Serve splash screen at root."""
            return send_file(self.ui_dir / 'splash.html')

        @self.app.route('/<path:filename>')
        def serve_file(filename):
            """Serve static files from UI directory."""
            return send_from_directory(self.ui_dir, filename)

        @self.app.route('/styles/<path:filename>')
        def serve_styles(filename):
            """Serve CSS files from styles directory."""
            return send_from_directory(self.ui_dir / 'styles', filename)

        @self.app.route('/scripts/<path:filename>')
        def serve_scripts(filename):
            """Serve JavaScript files from scripts directory."""
            return send_from_directory(self.ui_dir / 'scripts', filename)

        @self.app.route('/assets/<path:filename>')
        def serve_assets(filename):
            """Serve asset files (images, fonts, etc.) from assets directory."""
            return send_from_directory(self.ui_dir / 'assets', filename)

    def start(self):
        """
        Start the web server in a background thread.

        The server runs in daemon mode so it will automatically
        shut down when the main program exits.
        """
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.thread.start()

    def _run_server(self):
        """Internal method to run Flask server."""
        self.app.run(
            host='0.0.0.0',
            port=self.port,
            debug=False,
            use_reloader=False
        )

    def stop(self):
        """
        Stop the web server gracefully.

        Note: Flask's built-in server doesn't have a clean shutdown
        mechanism, so we just mark it as not running. In production,
        consider using a WSGI server like Gunicorn.
        """
        self.running = False

    def get_url(self):
        """
        Get the base URL of the web server.

        Returns:
            str: Base URL (e.g., "http://localhost:5000")
        """
        return f"http://localhost:{self.port}"
