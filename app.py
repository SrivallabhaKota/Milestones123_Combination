# ============================================================
#  FinSight – app.py
#  Main Flask Application Entry Point
#  Author : B.Tech Major Project
#  Tech   : Flask + MySQL + bcrypt + Sessions
# ============================================================

import pymysql
pymysql.install_as_MySQLdb()

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
import bcrypt
import re
from datetime import datetime
from config import Config
from functools import wraps

# ── App Initialisation ────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# ── Database Connection & Auto Setup ─────────────────────────
def init_db():
    """Ensure database 'finsight' and table 'users' exist."""
    try:
        # First connect without DB specified to create DB if missing
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            autocommit=True
        )
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS finsight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        # Connect to finsight DB and create users table
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            autocommit=True
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(100)  NOT NULL,
                  email       VARCHAR(100)  NOT NULL UNIQUE,
                  password    VARCHAR(255)  NOT NULL,
                  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
        conn.close()
        print("Database 'finsight' and table 'users' are verified and ready!")
    except Exception as e:
        print("Database auto-init error:", e)

# Run DB setup on start
init_db()

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# ══════════════════════════════════════════════════════════════
#  Helper: Login Required Decorator
# ══════════════════════════════════════════════════════════════
def login_required(f):
    """Protect routes – redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
#  Helper: Email Validation
# ══════════════════════════════════════════════════════════════
def is_valid_email(email: str) -> bool:
    pattern = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ══════════════════════════════════════════════════════════════
#  Helper: Password Strength Validation
# ══════════════════════════════════════════════════════════════
def is_strong_password(password: str) -> bool:
    """
    Rules:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-\[\]\/\\]', password):
        return False
    return True


# ══════════════════════════════════════════════════════════════
#  ROUTE  /  →  Login Page (default landing)
# ══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    """Root URL redirects to login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))


# ══════════════════════════════════════════════════════════════
#  ROUTE  /login  →  Show Login Form (GET) + Authenticate (POST)
# ══════════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Display login form on GET; authenticate on POST."""
    # Already logged in → go to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')

        # ── Frontend sanity checks on backend too ────────────
        if not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('login.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html')

        # ── Query database ───────────────────────────────────
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
            conn.close()
        except Exception as e:
            flash('Database error. Please try again later.', 'danger')
            app.logger.error(f'DB Error during login: {e}')
            return render_template('login.html')

        # ── Verify credentials ───────────────────────────────
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['user_email']= user['email']

            if remember:
                from datetime import timedelta
                app.permanent_session_lifetime = timedelta(days=30)
                session.permanent = True

            flash(f"Welcome back, {user['name']}! 🎉", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


# ══════════════════════════════════════════════════════════════
#  ROUTE  /register  →  Show Register Form (GET) + Create Account (POST)
# ══════════════════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Display registration form on GET; create account on POST."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name            = request.form.get('name', '').strip()
        email           = request.form.get('email', '').strip().lower()
        password        = request.form.get('password', '').strip()
        confirm_password= request.form.get('confirm_password', '').strip()

        errors = []

        # ── Field validations ────────────────────────────────
        if not name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email address is required.')
        elif not is_valid_email(email):
            errors.append('Please enter a valid email address.')
        if not password:
            errors.append('Password is required.')
        elif not is_strong_password(password):
            errors.append('Password must be at least 8 characters with uppercase, lowercase, number, and special character.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html')

        # ── Check duplicate email & insert user ─────────────
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing = cur.fetchone()

                if existing:
                    conn.close()
                    flash('An account with this email already exists. Please log in.', 'warning')
                    return render_template('register.html')

                # ── Hash password with bcrypt ────────────────────
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

                # ── Insert new user ──────────────────────────────
                cur.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_pw.decode('utf-8'))
                )
            conn.close()

        except Exception as e:
            print("DB ERROR DURING REGISTRATION:", e)
            flash(f'Registration failed: {e}', 'danger')
            app.logger.error(f'DB Error during registration: {e}')
            return render_template('register.html')

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login_page'))

    return render_template('register.html')


# ══════════════════════════════════════════════════════════════
#  ROUTE  /dashboard  →  Protected Dashboard
# ══════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    """Protected dashboard – only accessible when logged in."""
    user_name  = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    now_hour   = datetime.now().hour
    return render_template('dashboard.html',
                           user_name=user_name,
                           user_email=user_email,
                           now_hour=now_hour)


# ══════════════════════════════════════════════════════════════
#  ROUTE  /logout  →  Destroy Session
# ══════════════════════════════════════════════════════════════
@app.route('/logout')
@login_required
def logout():
    """Destroy session and redirect to login."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login_page'))


# ══════════════════════════════════════════════════════════════
#  ROUTE  /forgot-password  →  Dummy Forgot Password Page
# ══════════════════════════════════════════════════════════════
@app.route('/forgot-password')
def forgot_password():
    """Placeholder for forgot password (future enhancement)."""
    flash('Password reset feature coming soon. Contact support for help.', 'info')
    return redirect(url_for('login_page'))


# ══════════════════════════════════════════════════════════════
#  Error Handlers
# ══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return render_template('login.html'), 404

@app.errorhandler(500)
def server_error(e):
    flash('An internal server error occurred.', 'danger')
    return render_template('login.html'), 500


# ══════════════════════════════════════════════════════════════
#  Run
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
