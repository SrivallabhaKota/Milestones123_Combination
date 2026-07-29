# ============================================================
#  FinSight – config.py
#  Database & App Configuration
# ============================================================

import os

class Config:
    # ── Flask Secret Key ──────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'finsight_ultra_secret_key_2024_change_in_production')

    # ── MySQL Database ────────────────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3307))       # ← Port 3307
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root@123')   # ← Password root@123
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'finsight')
    MYSQL_CURSORCLASS = 'DictCursor'

    # ── Session ───────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ── Debug ─────────────────────────────────────────────────
    DEBUG = True
