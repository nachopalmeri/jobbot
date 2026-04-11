"""
Admin panel routes.
Métricas de billing, usuarios y revenue para operadores internos.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import get_authenticated_user, get_db

try:
    from job_bot.database import Database
except ImportError:
    from database import Database

logger = logging.getLogger(__name__)
router = APIRouter()
PAID_STATUSES = ("paid", "completed")

def verify_admin_access(current_user: dict):
    """Verifica acceso admin real desde el flag persistido en users."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores"
        )


@router.get("/metrics")
async def get_admin_metrics(
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Métricas de billing y usuarios."""
    verify_admin_access(current_user)
    
    # Obtener métricas de usuarios
    if db.db_type == "supabase":
        # Total usuarios Telegram
        telegram_users = db._fetchone("SELECT COUNT(*) as count FROM users")
        # Total usuarios Web
        web_users = db._fetchone("SELECT COUNT(*) as count FROM web_users")
        # Usuarios activos hoy (que iniciaron sesión o usaron bot)
        active_today = db._fetchone(
            "SELECT COUNT(DISTINCT telegram_id) as count FROM ai_analyses WHERE created_at >= NOW() - INTERVAL '1 day'"
        )
        # Nuevos usuarios esta semana
        new_this_week = db._fetchone(
            "SELECT COUNT(*) as count FROM web_users WHERE created_at >= NOW() - INTERVAL '7 days'"
        )
        # Pagos totales
        total_revenue = db._fetchone(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status IN ('paid', 'completed')"
        )
        # Pagos del mes
        monthly_revenue = db._fetchone(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status IN ('paid', 'completed') AND created_at >= NOW() - INTERVAL '30 days'"
        )
        # Suscripciones activas por plan
        plan_distribution = db._fetchall(
            "SELECT plan, COUNT(*) as count FROM web_users GROUP BY plan"
        )
        # Créditos vendidos
        credits_sold = db._fetchone(
            "SELECT COALESCE(SUM(credits_total), 0) as total FROM credit_packs WHERE status = 'active'"
        )
        # Créditos restantes en circulación
        credits_remaining = db._fetchone(
            "SELECT COALESCE(SUM(credits_remaining), 0) as total FROM credit_packs WHERE status = 'active'"
        )
    else:
        # SQLite queries
        telegram_users = db._fetchone("SELECT COUNT(*) as count FROM users")
        web_users = db._fetchone("SELECT COUNT(*) as count FROM web_users")
        active_today = db._fetchone(
            "SELECT COUNT(DISTINCT telegram_id) as count FROM ai_analyses WHERE created_at >= datetime('now', '-1 day')"
        )
        new_this_week = db._fetchone(
            "SELECT COUNT(*) as count FROM web_users WHERE created_at >= datetime('now', '-7 days')"
        )
        total_revenue = db._fetchone(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status IN ('paid', 'completed')"
        )
        monthly_revenue = db._fetchone(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status IN ('paid', 'completed') AND created_at >= datetime('now', '-30 days')"
        )
        plan_distribution = db._fetchall(
            "SELECT plan, COUNT(*) as count FROM web_users GROUP BY plan"
        )
        credits_sold = db._fetchone(
            "SELECT COALESCE(SUM(credits_total), 0) as total FROM credit_packs WHERE status = 'active'"
        )
        credits_remaining = db._fetchone(
            "SELECT COALESCE(SUM(credits_remaining), 0) as total FROM credit_packs WHERE status = 'active'"
        )
    
    # Últimos pagos
    recent_payments = db._fetchall(
        """SELECT p.*, w.email 
           FROM payments p 
           LEFT JOIN web_users w ON p.telegram_id = w.telegram_id 
           ORDER BY p.created_at DESC 
           LIMIT 10"""
    ) if db.db_type == "supabase" else db._fetchall(
        """SELECT p.*, w.email 
           FROM payments p 
           LEFT JOIN web_users w ON p.telegram_id = w.telegram_id 
           ORDER BY p.created_at DESC 
           LIMIT 10""")
    
    return {
        "users": {
            "telegram_total": telegram_users["count"] if telegram_users else 0,
            "web_total": web_users["count"] if web_users else 0,
            "active_today": active_today["count"] if active_today else 0,
            "new_this_week": new_this_week["count"] if new_this_week else 0,
        },
        "revenue": {
            "total_usd": float(total_revenue["total"] if total_revenue else 0),
            "monthly_usd": float(monthly_revenue["total"] if monthly_revenue else 0),
        },
        "plans": [
            {"plan": row["plan"], "count": row["count"]} for row in plan_distribution
        ] if plan_distribution else [],
        "credits": {
            "total_sold": int(credits_sold["total"] if credits_sold else 0),
            "remaining": int(credits_remaining["total"] if credits_remaining else 0),
            "consumed": int((credits_sold["total"] if credits_sold else 0) - (credits_remaining["total"] if credits_remaining else 0)),
        },
        "recent_payments": [
            {
                "id": p["id"],
                "email": p.get("email", "N/A"),
                "amount": float(p["amount"]),
                "currency": p["currency"],
                "provider": p["provider"],
                "status": p["status"],
                "created_at": p["created_at"],
            }
            for p in (recent_payments or [])
        ],
    }


@router.get("/users")
async def get_admin_users(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_authenticated_user),
    db: Database = Depends(get_db),
):
    """Lista de usuarios con sus planes."""
    verify_admin_access(current_user)
    
    users = db._fetchall(
        """SELECT w.id, w.telegram_id, w.email, w.plan, u.is_admin,
                  w.created_at, w.ai_analyses_used, w.ai_analyses_limit,
                  w.searches_used, w.searches_limit,
                  COALESCE(SUM(c.credits_remaining), 0) as credits
           FROM web_users w
           LEFT JOIN users u ON w.telegram_id = u.telegram_id
           LEFT JOIN credit_packs c ON w.telegram_id = c.telegram_id AND c.status = 'active'
           GROUP BY w.id, u.is_admin
           ORDER BY w.created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset)
    ) if db.db_type != "supabase" else db._fetchall(
        """SELECT w.id, w.telegram_id, w.email, w.plan, u.is_admin,
                  w.created_at, w.ai_analyses_used, w.ai_analyses_limit,
                  w.searches_used, w.searches_limit,
                  COALESCE(SUM(c.credits_remaining), 0) as credits
           FROM web_users w
           LEFT JOIN users u ON w.telegram_id = u.telegram_id
           LEFT JOIN credit_packs c ON w.telegram_id = c.telegram_id AND c.status = 'active'
           GROUP BY w.id, u.is_admin
           ORDER BY w.created_at DESC
           LIMIT %s OFFSET %s""",
        (limit, offset)
    )
    
    return {
        "users": [
            {
                "id": u["id"],
                "telegram_id": u["telegram_id"],
                "email": u["email"],
                "plan": u["plan"],
                "is_admin": bool(u["is_admin"]),
                "created_at": u["created_at"],
                "usage": {
                    "ai_analyses": f"{u['ai_analyses_used']}/{u['ai_analyses_limit']}",
                    "searches": f"{u['searches_used']}/{u['searches_limit']}",
                },
                "credits": int(u["credits"]),
            }
            for u in (users or [])
        ],
        "total": len(users) if users else 0,
    }
