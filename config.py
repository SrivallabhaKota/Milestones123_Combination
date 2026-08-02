# ============================================================
#  FinSight – Personal Finance & Investment Intelligence Platform
#  File       : config.py
#  Description: Application and MySQL Database Configuration
# ============================================================

import os

class Config:
    """
    Central Configuration class for Flask and Database settings.
    Reads environment variables if available, or falls back to defaults.
    """
    
    # ── Flask Secret Key ──────────────────────────────────────
    # Used by Flask to cryptographically sign session cookies.
    # Keep this key confidential in production!
    SECRET_KEY = os.environ.get('SECRET_KEY', 'finsight_ultra_secret_key_2024_change_in_production')

    # ── MySQL Database Credentials ────────────────────────────
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')  # MySQL server host IP/domain
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3307))       # MySQL server port (default 3307 or 3306)
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')       # MySQL user account username
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root@123')   # MySQL user account password
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'finsight')   # Database schema name
    MYSQL_CURSORCLASS = 'DictCursor'                                # Returns rows as dictionaries instead of tuples

    # ── Security & Session Cookie Settings ─────────────────────
    SESSION_COOKIE_HTTPONLY = True  # Prevents client-side JavaScript from reading session cookies (Mitigates XSS)
    SESSION_COOKIE_SAMESITE = 'Lax' # Protects against Cross-Site Request Forgery (CSRF) attacks

    # ── Debug Mode ─────────────────────────────────────────────
    DEBUG = True # Enables automatic reload on code changes and detailed error stack traces
