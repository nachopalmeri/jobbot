"""
stats_api.py - API HTTP mínima para servir estadísticas del bot.
Usada por la landing page para mostrar datos en vivo.

Corre en un thread separado junto al bot. Puerto configurable en .env.
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import config
from database import Database

logger = logging.getLogger(__name__)


class StatsHandler(BaseHTTPRequestHandler):
    """Handler HTTP que sirve /api/stats con CORS habilitado."""

    db = None  # Se setea antes de arrancar el server

    def do_GET(self):
        if self.path == "/api/stats":
            self._serve_stats()
        elif self.path == "/api/health":
            self._serve_health()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _serve_stats(self):
        try:
            stats = self.db.get_stats() if self.db else {}
            # Agregar fuentes activas desde config
            sources_count = sum(1 for v in config.SOURCES_ENABLED.values() if v)
            stats["sources_count"] = sources_count
            stats["check_interval_hours"] = config.CHECK_INTERVAL_HOURS

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
        except Exception as e:
            logger.error("Error sirviendo stats: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Internal error"}).encode())

    def _serve_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def _send_cors_headers(self):
        """Envía headers CORS para permitir fetch desde la landing en Vercel."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        self.send_header("Cache-Control", "public, max-age=60")

    def log_message(self, format, *args):
        """Silenciar logs de acceso HTTP (demasiado verboso)."""
        pass


def run_stats_api(db: Database, port: int = 8080):
    """
    Corre el servidor HTTP de stats en un thread separado.
    Se llama desde bot.py al arrancar.
    """
    StatsHandler.db = db
    server = HTTPServer(("0.0.0.0", port), StatsHandler)
    logger.info("📊 Stats API activa en http://0.0.0.0:%d/api/stats", port)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="StatsAPI",
    )
    thread.start()
    return server
