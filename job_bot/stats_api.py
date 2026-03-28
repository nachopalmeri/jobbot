"""
stats_api.py - API HTTP mínima para servir estadísticas del bot.
Usada por la landing page para mostrar datos en vivo.

Corre en un thread separado junto al bot. Puerto configurable en .env.
"""

import json
import logging
import threading
import hashlib
import hmac
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# Imports tolerantes al contexto de ejecución
try:
    import config
except ImportError:
    from job_bot import config

try:
    from database import Database
except ImportError:
    from job_bot.database import Database

logger = logging.getLogger(__name__)


class StatsHandler(BaseHTTPRequestHandler):
    """Handler HTTP que sirve /api/stats con CORS habilitado."""

    db = None  # Se setea antes de arrancar el server

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/stats":
            self._serve_stats()
        elif path == "/api/health":
            self._serve_health()
        elif path == "/api/dashboard":
            self._serve_dashboard(parsed_path.query)
        elif path == "/api/preferences":
            self._serve_preferences(parsed_path.query)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/preferences":
            self._update_preferences()
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

    def _serve_dashboard(self, query):
        params = parse_qs(query)
        tid_list = params.get('telegram_id')
        
        # Validacion hiper-basica para la prueba
        if not tid_list:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing telegram_id"}).encode())
            return
            
        tid = int(tid_list[0])
        try:
            # Obtener datos usando la base de datos ya conectada
            profile = self.db.get_user_profile(tid)
            if not profile:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "User not found"}).encode())
                return
                
            apps = self.db.get_user_applications(tid)
            
            # Resumen del funnel
            funnel = {
                "applied": len([a for a in apps if a['status'] == 'aplicado']),
                "interview": len([a for a in apps if a['status'] == 'entrevista']),
                "rejected": len([a for a in apps if a['status'] == 'rechazado']),
                "offer": len([a for a in apps if a['status'] == 'oferta'])
            }

            weekly_goal = self.db.get_weekly_goal(tid)
            weekly_applied = self.db.get_weekly_applications_count(tid)
            digest_mode = self.db.get_digest_mode(tid)
            company_filters = self.db.get_company_filters(tid)
            
            payload = {
                "user_level": profile.get('experience_level', 'junior'),
                "user_role": profile.get('role_type'),
                "funnel": funnel,
                "applications": apps,
                "weekly_goal": weekly_goal,
                "weekly_applied": weekly_applied,
                "digest_mode": digest_mode,
                "blocked_companies": company_filters.get("blocked_raw", ""),
                "preferred_companies": company_filters.get("preferred_raw", ""),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            
        except Exception as e:
            logger.error("Error sirviendo dashboard: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Dashboard internal error"}).encode())

    def _serve_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def _serve_preferences(self, query: str):
        params = parse_qs(query)
        tid_list = params.get("telegram_id")

        if not tid_list:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing telegram_id"}).encode())
            return

        try:
            tid = int(tid_list[0])
        except ValueError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid telegram_id"}).encode())
            return

        try:
            user = self.db.get_user(tid) if self.db else None
            if not user:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "User not found"}).encode())
                return

            schedule = self.db.get_user_schedule(tid)
            channel = self.db.get_alert_channel(tid)
            weekly_goal = self.db.get_weekly_goal(tid)
            digest_mode = self.db.get_digest_mode(tid)
            company_filters = self.db.get_company_filters(tid)

            payload = {
                "telegram_id": tid,
                "alert_channel": channel,
                "check_interval_hours": schedule.get("check_interval_hours"),
                "alert_start_hour": schedule.get("alert_start_hour"),
                "alert_end_hour": schedule.get("alert_end_hour"),
                "timezone": schedule.get("timezone"),
                "weekly_goal": weekly_goal,
                "digest_mode": digest_mode,
                "blocked_companies": company_filters.get("blocked_raw", ""),
                "preferred_companies": company_filters.get("preferred_raw", ""),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        except Exception as e:
            logger.error("Error sirviendo preferencias: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Preferences internal error"}).encode())

    def _update_preferences(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0

        raw_body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            data = {}

        telegram_id = data.get("telegram_id")
        channel = data.get("alert_channel") or data.get("channel")
        digest_mode = data.get("digest_mode")
        weekly_goal = data.get("weekly_goal") or data.get("weekly_goal_apps")
        blocked_companies = data.get("blocked_companies")
        preferred_companies = data.get("preferred_companies")

        if telegram_id is None:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing telegram_id"}).encode())
            return

        try:
            tid = int(telegram_id)
        except (TypeError, ValueError):
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid telegram_id"}).encode())
            return

        allowed = {"telegram", "web", "email", "whatsapp", "twitter"}
        channel_str = None
        if channel is not None:
            channel_str = str(channel).lower()
            if channel_str not in allowed:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid alert_channel"}).encode())
                return

        try:
            user = self.db.get_user(tid) if self.db else None
            if not user:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "User not found"}).encode())
                return

            # Actualizar canal de alertas si vino en el payload
            if channel_str is not None:
                self.db.set_alert_channel(tid, channel_str)

            # Actualizar modo de digest si está presente
            if digest_mode is not None:
                self.db.set_digest_mode(tid, str(digest_mode))

            # Actualizar objetivo semanal si está presente
            if weekly_goal is not None:
                self.db.set_weekly_goal(tid, weekly_goal)

            # Actualizar filtros de empresas si están presentes
            if blocked_companies is not None or preferred_companies is not None:
                # Si alguno viene como None, mantener el valor actual de DB
                current_filters = self.db.get_company_filters(tid)
                blocked_raw = (
                    blocked_companies
                    if blocked_companies is not None
                    else current_filters.get("blocked_raw", "")
                )
                preferred_raw = (
                    preferred_companies
                    if preferred_companies is not None
                    else current_filters.get("preferred_raw", "")
                )
                self.db.set_company_filters(tid, blocked_raw, preferred_raw)

            # Construir payload actualizado
            schedule = self.db.get_user_schedule(tid)
            weekly_goal_val = self.db.get_weekly_goal(tid)
            digest_mode_val = self.db.get_digest_mode(tid)
            filters = self.db.get_company_filters(tid)

            response = {
                "ok": True,
                "telegram_id": tid,
                "alert_channel": self.db.get_alert_channel(tid),
                "check_interval_hours": schedule.get("check_interval_hours"),
                "digest_mode": digest_mode_val,
                "weekly_goal": weekly_goal_val,
                "blocked_companies": filters.get("blocked_raw", ""),
                "preferred_companies": filters.get("preferred_raw", ""),
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            logger.error("Error actualizando preferencias: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Preferences internal error"}).encode())

    def _send_cors_headers(self):
        """Envía headers CORS para permitir fetch desde la landing en Vercel."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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
