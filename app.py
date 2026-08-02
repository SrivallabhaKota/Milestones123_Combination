# ============================================================
#  FinSight – Personal Finance & Investment Intelligence Platform
#  File       : app.py
#  Description: Main Flask Application Entry Point
#  Team Contributions:
#    - Home Page Module       : Meghna
#    - Authentication Module  : Vallabha (Login & Registration)
#    - Dashboard UI & Charts  : Monisha (Dashboard & Analytics)
#    - Database REST APIs     : Navaneeth (Income, Expenses, Budget APIs)
#    - Input Forms & Balance  : Deepika (Income, Expense, Budget Forms & Balance Math)
#  Tech Stack : Python, Flask, PyMySQL, bcrypt, Flask Sessions
# ============================================================

# ── Import PyMySQL and register as MySQLdb driver ─────────────
# PyMySQL is a pure-Python driver that connects to MySQL without 
# requiring C++ compiler headers (mysql.h) on Windows systems.
import pymysql
pymysql.install_as_MySQLdb()

# ── Standard Flask and Utility Imports ─────────────────────────
from flask import (
    Flask,           # Main Web Application Class
    render_template, # Renders Jinja2 HTML templates from /templates
    request,         # Handles incoming HTTP request data (GET params, POST form data)
    redirect,        # Redirects user browser to another URL route
    url_for,         # Dynamically builds URLs based on view function names
    session,         # Manages encrypted server-side user sessions (cookies)
    flash,           # Sends one-time alert notifications across HTTP requests
    jsonify          # Converts Python dictionaries to JSON responses
)
import bcrypt        # Industry-standard password hashing algorithm (Blowfish-based)
import re            # Regular expressions library for email and password validation
from datetime import datetime, timedelta # Time utilities for session expiration and dynamic greetings
from config import Config                 # Custom application configuration class
from functools import wraps               # Decorator factory tool to preserve function metadata

# ── App Initialisation ────────────────────────────────────────
# Initialize the Flask application instance and load settings from Config class
app = Flask(__name__)
app.config.from_object(Config)


# ══════════════════════════════════════════════════════════════
#  AUTOMATIC DATABASE & TABLE SETUP
# ══════════════════════════════════════════════════════════════
def init_db():
    """
    Automatically verifies and initializes the MySQL database schema on startup.
    1. Connects to MySQL server without specifying a database.
    2. Creates the 'finsight' database if it does not exist.
    3. Creates ALL required tables: users, income, expenses, budget.

    Table Ownership:
    - users   : Core authentication table (used by entire team)
    - income  : Developed by Navaneeth (REST API) & Deepika (HTML Form Input)
    - expenses: Developed by Navaneeth (REST API) & Deepika (HTML Form Input)
    - budget  : Developed by Navaneeth (REST API) & Deepika (HTML Form Input)
    """
    try:
        # Step A: Connect to MySQL host to create database 'finsight' if missing
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            autocommit=True
        )
        with conn.cursor() as cur:
            # SQL command to create database with utf8mb4 encoding for full Unicode support
            cur.execute("CREATE DATABASE IF NOT EXISTS finsight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        # Step B: Connect directly to 'finsight' database to create tables
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            autocommit=True
        )
        with conn.cursor() as cur:

            # -- USERS TABLE (Core Authentication - used by the entire team) --------
            # id        : Primary key, auto-incrementing integer
            # name      : User's full name (max 100 chars)
            # email     : Unique email address used for authentication
            # password  : Bcrypt encrypted password hash (255 chars)
            # created_at: Auto-generated registration timestamp
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(100)  NOT NULL,
                  email       VARCHAR(100)  NOT NULL UNIQUE,
                  password    VARCHAR(255)  NOT NULL,
                  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # -- INCOME TABLE (Navaneeth: REST API Endpoints | Deepika: HTML Forms) --
            # Stores income entries that users add through the Add Income form or API.
            # user_id    : Links each income record to the user who added it (Foreign Key)
            # source     : Source of the income (e.g. 'Salary', 'Freelance', 'Bonus')
            # amount     : The monetary value of the income entry (e.g. 50000.00)
            # income_date: The actual date when the income was received
            # notes      : Optional extra description or remarks by the user
            # created_at : Timestamp automatically set when the record is inserted
            cur.execute("""
                CREATE TABLE IF NOT EXISTS income (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  user_id     INT           NOT NULL,
                  source      VARCHAR(100)  NOT NULL,
                  amount      DECIMAL(10,2) NOT NULL,
                  income_date DATE          NOT NULL,
                  notes       VARCHAR(255),
                  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # -- EXPENSES TABLE (Navaneeth: REST API Endpoints | Deepika: HTML Forms) -
            # Stores expense entries that users add through the Add Expense form or API.
            # user_id     : Links each expense record to the user who added it (Foreign Key)
            # category    : Spending category (e.g. 'Groceries', 'Travel', 'Utilities')
            # amount      : The monetary value of the expense entry (e.g. 1200.50)
            # expense_date: The actual date when the expense occurred
            # notes       : Optional extra description or remarks by the user
            # created_at  : Timestamp automatically set when the record is inserted
            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                  id           INT AUTO_INCREMENT PRIMARY KEY,
                  user_id      INT           NOT NULL,
                  category     VARCHAR(100)  NOT NULL,
                  amount       DECIMAL(10,2) NOT NULL,
                  expense_date DATE          NOT NULL,
                  notes        VARCHAR(255),
                  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # -- BUDGET TABLE (Navaneeth: REST API Endpoints | Deepika: HTML Forms) ---
            # Stores monthly category-wise budget limits that users define.
            # user_id     : Links each budget record to the user who created it (Foreign Key)
            # category    : Budget category name (e.g. 'Food', 'Housing', 'Transport')
            # limit_amount: Maximum amount the user plans to spend in this category
            # month       : Month number the budget applies to (1 = Jan, 12 = Dec)
            # year        : 4-digit year the budget applies to (e.g. 2026)
            # created_at  : Timestamp automatically set when the budget is created
            # UNIQUE KEY  : Prevents creating two budgets for the same category/month/year
            cur.execute("""
                CREATE TABLE IF NOT EXISTS budget (
                  id           INT AUTO_INCREMENT PRIMARY KEY,
                  user_id      INT           NOT NULL,
                  category     VARCHAR(100)  NOT NULL,
                  limit_amount DECIMAL(10,2) NOT NULL,
                  month        INT           NOT NULL,
                  year         INT           NOT NULL,
                  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                  UNIQUE KEY unique_budget_per_month (user_id, category, month, year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

        conn.close()
        print("✅ Database 'finsight' and all tables (users, income, expenses, budget) verified successfully!")
    except Exception as e:
        print("❌ Database initialization error:", e)

# Trigger automatic database initialization upon importing app.py
init_db()


# ══════════════════════════════════════════════════════════════
#  DATABASE CONNECTION HELPER
# ══════════════════════════════════════════════════════════════
def get_db_connection():
    """
    Creates and returns a new PyMySQL database connection instance.
    Uses settings defined in config.py (Host, Port, User, Password, DB Name).
    DictCursor formats SQL rows as Python dictionaries {'id': 1, 'email': '...'}
    """
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
#  DECORATOR: LOGIN REQUIRED ROUTE GUARD
# ══════════════════════════════════════════════════════════════
def login_required(f):
    """
    Custom decorator for route security.
    Checks if 'user_id' exists in the active Flask session.
    If missing (unauthenticated user):
      - Flashes a warning message
      - Redirects user to the login page immediately
    Prevents unauthorized direct URL access to protected routes like /dashboard.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
#  VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════
def is_valid_email(email: str) -> bool:
    """
    Validates email syntax using standard RFC Regular Expressions.
    Checks for: <name>@<domain>.<tld>
    """
    pattern = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_strong_password(password: str) -> bool:
    """
    Enforces strict security criteria for passwords:
    1. Minimum length of 8 characters
    2. At least one uppercase letter (A-Z)
    3. At least one lowercase letter (a-z)
    4. At least one numeric digit (0-9)
    5. At least one special character (!@#$%^&* etc.)
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


# ════════════════════════════════════════════════════════════
#  MODULE: HOME PAGE (Developed by: Meghna)
# ════════════════════════════════════════════════════════════
@app.route('/')
@app.route('/home')
def home():
    """
    Default entry route for the application.
    - If user is logged in (session exists) -> Redirects to Dashboard.
    - Otherwise -> Renders the Home landing page.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


# Alias so existing references to url_for('index') still resolve
def index():
    return home()


# ══════════════════════════════════════════════════════════════
#  MODULE: AUTHENTICATION - LOGIN & REGISTER (Developed by: Vallabha)
# ══════════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """
    Handles user login flow.
    GET  : Renders the login page HTML form.
    POST : Processes login credentials submitted by the user.
    """
    # Step 1: If user is already authenticated, redirect straight to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    # Step 2: Handle form submission when user clicks "Sign In" button
    if request.method == 'POST':
        # Retrieve form data from request object and sanitize inputs
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') # Checkbox value for persistent session

        # Backend Validation Step A: Check for empty input fields
        if not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('login.html')

        # Backend Validation Step B: Validate email format
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html')

        # Backend Verification Step C: Fetch user record from database
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # Parameterized query (%s) prevents SQL Injection attacks
                cur.execute("SELECT id, name, email, password FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
            conn.close()
        except Exception as e:
            print("DB Error during login:", e)
            flash(f'Database connection error: {e}', 'danger')
            return render_template('login.html')

        # Backend Verification Step D: Compare submitted password with bcrypt hash stored in DB
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Password matches! Create user session variables
            session['user_id']    = user['id']
            session['user_name']  = user['name']
            session['user_email'] = user['email']

            # Handle "Remember Me" checkbox: Set long-term session cookie (30 days)
            if remember:
                app.permanent_session_lifetime = timedelta(days=30)
                session.permanent = True

            flash(f"Welcome back, {user['name']}! 🎉", 'success')
            return redirect(url_for('dashboard'))
        else:
            # Login failure: Invalid credentials
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')

    # Default GET request: Render the login template
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles new user registration flow.
    GET  : Renders the registration form page.
    POST : Validates input, hashes password with bcrypt, and inserts user into MySQL.
    """
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Sanitize and extract incoming form fields
        name             = request.form.get('name', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        errors = [] # List to collect validation errors

        # Field Validation Rules
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

        # If any validation rule failed, flash error alerts back to user
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html')

        # Database Check: Check for existing account with the same email address
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing = cur.fetchone()

                if existing:
                    conn.close()
                    flash('An account with this email already exists. Please log in.', 'warning')
                    return render_template('register.html')

                # Password Encryption: Hash plain text password using bcrypt with 12 salt rounds
                # Plain text passwords are NEVER stored in the database!
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

                # Insert new user into MySQL database
                cur.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_pw.decode('utf-8'))
                )
            conn.close()

        except Exception as e:
            print("DB ERROR DURING REGISTRATION:", e)
            flash(f'Registration failed: {e}', 'danger')
            return render_template('register.html')

        # Successful Registration! Flash success alert and redirect to Login page
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login_page'))

    return render_template('register.html')


# ══════════════════════════════════════════════════════════════
#  MODULE: DASHBOARD & ANALYTICS (Developed by: Monisha)
# ══════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required # Route is protected! Only accessible if session['user_id'] exists
def dashboard():
    """
    Displays the protected user dashboard.
    Retrieves user name and email from session data and passes current hour for dynamic greetings.
    """
    user_name  = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    now_hour   = datetime.now().hour # Gets current hour (0-23) for time-based greeting (Morning/Afternoon/Evening)
    
    return render_template('dashboard.html',
                           user_name=user_name,
                           user_email=user_email)


# ════════════════════════════════════════════════════════════
#  ROUTE: LOGOUT (/logout)
# ════════════════════════════════════════════════════════════
@app.route('/logout')
@login_required
def logout():
    """
    Destroys active Flask user session and redirects to home page.
    Clears all server-side session variables.
    """
    session.clear() # Removes all stored session data (user_id, user_name, user_email)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))


# ════════════════════════════════════════════════════════════
#  ROUTE: BUDGET PAGE (/budget)
# ════════════════════════════════════════════════════════════
@app.route('/budget')
@login_required
def budget():
    """
    Renders the protected Budget management page.
    Only accessible to logged-in users.
    """
    user_name  = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    return render_template('dashboard.html',
                           user_name=user_name,
                           user_email=user_email)


# ══════════════════════════════════════════════════════════════
#  ROUTE: FORGOT PASSWORD PLACEHOLDER (/forgot-password)
# ══════════════════════════════════════════════════════════════
@app.route('/forgot-password')
def forgot_password():
    """Placeholder route for future email password reset integration."""
    flash('Password reset feature coming soon. Contact support for help.', 'info')
    return redirect(url_for('login_page'))


# ══════════════════════════════════════════════════════════════
#  DASHBOARD API ROUTES (integrated from finsight/insight)
#  These endpoints serve JSON data consumed by dashboard.js
# ══════════════════════════════════════════════════════════════

@app.route('/api/dashboard-summary')
@login_required
def api_dashboard_summary():
    """Returns dynamic income, expenses, savings totals and chart segments from database."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get total income
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s", (user_id,))
            total_income = float(cur.fetchone()['total'])

            # Get total expenses
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s", (user_id,))
            total_expenses = float(cur.fetchone()['total'])
        conn.close()

        # Calculate savings and chart percentages
        total_savings = total_income - total_expenses if total_income > total_expenses else 0
        total_value = total_income + total_expenses + total_savings
        
        if total_value > 0:
            income_pct = round((total_income / total_value) * 100)
            expenses_pct = round((total_expenses / total_value) * 100)
            savings_pct = round((total_savings / total_value) * 100)
        else:
            income_pct = expenses_pct = savings_pct = 0

        return jsonify({
            'income':      {'total': total_income, 'change': 0},
            'expenses':    {'total': total_expenses, 'change': 0},
            'savings':     {'total': total_savings, 'change': 0},
            'investments': {'total': 0, 'change': 0},
            'chart_segments': {'income': income_pct, 'expenses': expenses_pct, 'savings': savings_pct, 'investments': 0},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user-profile')
@login_required
def api_user_profile():
    """Returns the logged-in user's profile details from session."""
    return jsonify({
        'name':                  session.get('user_name', 'User'),
        'email':                 session.get('user_email', ''),
        'role':                  'Premium User',
        'member_since':          'Active',
        'account_status':        'Verified',
        'financial_health_score': 100,
    })


@app.route('/api/recent-transactions')
@login_required
def api_recent_transactions():
    """Returns a dynamic list of recent financial transactions from DB."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Fetch income records
            cur.execute("SELECT id, source AS title, 'Income' AS category, amount, income_date AS date, 'income' AS type, created_at FROM income WHERE user_id = %s", (user_id,))
            incomes = cur.fetchall()

            # Fetch expense records
            cur.execute("SELECT id, category AS title, 'Expense' AS category, amount, expense_date AS date, 'expense' AS type, created_at FROM expenses WHERE user_id = %s", (user_id,))
            expenses = cur.fetchall()
        conn.close()

        # Combine, sort by date descending, and take top 5
        transactions = incomes + expenses
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        recent = transactions[:5]

        # Format for JSON response
        result = []
        for t in recent:
            result.append({
                'title': t['title'],
                'category': t['category'],
                'amount': float(t['amount']),
                'type': t['type'],
                'date': str(t['date'])
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/monthly-spending')
@login_required
def api_monthly_spending():
    """Returns dynamic monthly spending values for the line chart."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MONTHNAME(expense_date) AS month, SUM(amount) AS total 
                FROM expenses 
                WHERE user_id = %s AND expense_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY month 
                ORDER BY MIN(expense_date) ASC
            """, (user_id,))
            rows = cur.fetchall()
        conn.close()

        labels = [r['month'][:3] for r in rows] if rows else ['No Data']
        values = [float(r['total']) for r in rows] if rows else [0]

        return jsonify({
            'labels': labels,
            'values': values,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/insights')
@login_required
def api_insights():
    """Returns dynamic financial insight cards based on user data."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Monthly Spending Insight
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s AND MONTH(expense_date) = MONTH(CURDATE()) AND YEAR(expense_date) = YEAR(CURDATE())", (user_id,))
            monthly_spent = float(cur.fetchone()['total'])

            # Budget Status Insight
            cur.execute("SELECT COALESCE(SUM(limit_amount), 0) AS total_budget FROM budget WHERE user_id = %s AND month = MONTH(CURDATE()) AND year = YEAR(CURDATE())", (user_id,))
            total_budget = float(cur.fetchone()['total_budget'])

            # Total Income (for savings rate)
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s AND MONTH(income_date) = MONTH(CURDATE()) AND YEAR(income_date) = YEAR(CURDATE())", (user_id,))
            monthly_income = float(cur.fetchone()['total'])
        conn.close()

        # Logic for Budget Status
        if total_budget > 0:
            budget_pct = min(100, round((monthly_spent / total_budget) * 100))
            if budget_pct > 100:
                budget_status = 'Over Budget'
                budget_desc = f'Spending is {budget_pct - 100}% over plan'
                budget_color = '#EF4444' # Red
            else:
                budget_status = 'On Track'
                budget_desc = f'Spending is {100 - budget_pct}% below plan'
                budget_color = '#2563EB'
        else:
            budget_pct = 0
            budget_status = 'No Budget Set'
            budget_desc = 'Create a budget to track spending'
            budget_color = '#94A3B8'

        # Logic for Savings Rate
        if monthly_income > 0:
            savings = max(0, monthly_income - monthly_spent)
            savings_rate = round((savings / monthly_income) * 100)
            savings_status = f'{savings_rate}% Saved'
            savings_desc = 'Savings rate this month'
        else:
            savings_rate = 0
            savings_status = '0% Saved'
            savings_desc = 'No income recorded this month'

        return jsonify([
            {'title': 'Budget Status',     'status': budget_status,            'description': budget_desc,             'percentage': budget_pct, 'color': budget_color},
            {'title': 'Savings Rate',      'status': savings_status,           'description': savings_desc,            'percentage': savings_rate, 'color': '#10B981'},
            {'title': 'Investment Growth', 'status': '+0%',                    'description': 'Tracking coming soon',  'percentage': 0, 'color': '#8B5CF6'},
            {'title': 'Monthly Spending',  'status': f'₹{monthly_spent:,.0f}', 'description': 'Total spent this month','percentage': min(100, (monthly_spent/(max(1,monthly_income)))*100) if monthly_income > 0 else 0, 'color': '#3B82F6'},
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/view-all')
@login_required
def view_all():
    """Placeholder – Expense Management view."""
    return jsonify({'message': 'Recent transactions view is ready for the next step.'})


@app.route('/view-detailed-report')
@login_required
def view_detailed_report():
    """Placeholder – Detailed Report view."""
    return jsonify({'message': 'The detailed report page is ready to be expanded.'})


@app.route('/quick-actions/expense')
@login_required
def quick_action_expense():
    """Placeholder – Add Expense action."""
    return jsonify({'message': 'Expense tracking action placeholder'})


@app.route('/quick-actions/budget')
@login_required
def quick_action_budget():
    """Placeholder – Create Budget action."""
    return jsonify({'message': 'Budget creation action placeholder'})


@app.route('/quick-actions/investment')
@login_required
def quick_action_investment():
    """Placeholder – Add Investment action."""
    return jsonify({'message': 'Investment entry action placeholder'})


@app.route('/quick-actions/report')
@login_required
def quick_action_report():
    """Placeholder – Generate Report action."""
    return jsonify({'message': 'Report generation action placeholder'})


# ══════════════════════════════════════════════════════════════
#  MODULE: INCOME, EXPENSES & BUDGET - REST APIs (Developed by: Navaneeth)
#  Source: C:\Users\Vaishnavi\Desktop\Sample\finance-app
#
#  These are pure REST API endpoints that accept and return JSON data.
#  They are used when the frontend JavaScript (dashboard.js) needs to
#  fetch or submit data without reloading the page (AJAX-style calls).
#
#  All routes are protected with @login_required so only logged-in
#  users can access them. The logged-in user's ID is pulled from the
#  Flask session to filter records specific to that user.
# ══════════════════════════════════════════════════════════════

# ── Navaneeth: GET /api/income ─────────────────────────────────────────────
# Fetches all income records for the currently logged-in user from the database.
# The user_id is taken from Flask session (set at login time).
# Returns a JSON list of income records sorted by creation date (newest first).
@app.route('/api/income', methods=['GET'])
@login_required
def api_get_income():
    """
    Navaneeth – REST API: Retrieve all income records for the logged-in user.
    Returns: JSON array of income rows [{id, source, amount, income_date, notes, created_at}, ...]
    """
    user_id = session.get('user_id')  # Get the logged-in user's ID from session
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # SELECT all income records where user_id matches the session user
            # ORDER BY created_at DESC means newest records appear first
            cur.execute(
                "SELECT id, source, amount, income_date, notes, created_at FROM income WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()  # Fetch all matching rows as list of dicts
        conn.close()
        # Convert date/datetime objects to string so they can be serialized to JSON
        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'source': row['source'],
                'amount': float(row['amount']),          # Convert Decimal to float for JSON
                'income_date': str(row['income_date']),  # Convert date object to string
                'notes': row['notes'],
                'created_at': str(row['created_at'])
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Navaneeth: POST /api/income ────────────────────────────────────────────
# Accepts a JSON body with income details and inserts a new record into the
# income table in MySQL. The user_id is automatically taken from the session.
# Required JSON fields: source, amount, income_date
# Optional JSON field:  notes
@app.route('/api/income', methods=['POST'])
@login_required
def api_create_income():
    """
    Navaneeth – REST API: Add a new income record for the logged-in user.
    Expected JSON body: { "source": "Salary", "amount": 50000, "income_date": "2026-07-01", "notes": "" }
    Returns: JSON with the new record's ID and a success message.
    """
    data = request.get_json()  # Parse incoming JSON request body
    required = ['source', 'amount', 'income_date']  # Mandatory fields

    # Validation: Check all required fields are present in the request
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    user_id = session.get('user_id')  # Auto-assign logged-in user's ID
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Insert the new income record into the database
            # %s placeholders prevent SQL injection attacks
            cur.execute(
                "INSERT INTO income (user_id, source, amount, income_date, notes) VALUES (%s, %s, %s, %s, %s)",
                (user_id, data['source'], data['amount'], data['income_date'], data.get('notes', ''))
            )
            new_id = cur.lastrowid  # Get the auto-generated ID of the inserted row
        conn.close()
        return jsonify({'id': new_id, 'message': 'Income record created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Navaneeth: GET /api/expenses ───────────────────────────────────────────
# Fetches all expense records for the currently logged-in user from the database.
@app.route('/api/expenses', methods=['GET'])
@login_required
def api_get_expenses():
    """
    Navaneeth – REST API: Retrieve all expense records for the logged-in user.
    Returns: JSON array of expense rows [{id, category, amount, expense_date, notes, created_at}, ...]
    """
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, category, amount, expense_date, notes, created_at FROM expenses WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'category': row['category'],
                'amount': float(row['amount']),
                'expense_date': str(row['expense_date']),
                'notes': row['notes'],
                'created_at': str(row['created_at'])
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Navaneeth: POST /api/expenses ──────────────────────────────────────────
# Accepts a JSON body with expense details and inserts a new record into the
# expenses table. user_id is automatically taken from the session.
# Required JSON fields: category, amount, expense_date
# Optional JSON field:  notes
@app.route('/api/expenses', methods=['POST'])
@login_required
def api_create_expense():
    """
    Navaneeth – REST API: Add a new expense record for the logged-in user.
    Expected JSON body: { "category": "Groceries", "amount": 1200, "expense_date": "2026-07-24", "notes": "" }
    Returns: JSON with the new record's ID and a success message.
    """
    data = request.get_json()
    required = ['category', 'amount', 'expense_date']

    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses (user_id, category, amount, expense_date, notes) VALUES (%s, %s, %s, %s, %s)",
                (user_id, data['category'], data['amount'], data['expense_date'], data.get('notes', ''))
            )
            new_id = cur.lastrowid
        conn.close()
        return jsonify({'id': new_id, 'message': 'Expense record created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Navaneeth: GET /api/budget ─────────────────────────────────────────────
# Fetches all budget records for the currently logged-in user.
@app.route('/api/budget', methods=['GET'])
@login_required
def api_get_budget():
    """
    Navaneeth – REST API: Retrieve all budget records for the logged-in user.
    Returns: JSON array of budget rows [{id, category, limit_amount, month, year, created_at}, ...]
    """
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, category, limit_amount, month, year, created_at FROM budget WHERE user_id = %s ORDER BY year DESC, month DESC",
                (user_id,)
            )
            rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'category': row['category'],
                'limit_amount': float(row['limit_amount']),
                'month': row['month'],
                'year': row['year'],
                'created_at': str(row['created_at'])
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Navaneeth: POST /api/budget ────────────────────────────────────────────
# Accepts a JSON body with budget details and inserts a new monthly budget
# record. The UNIQUE KEY on (user_id, category, month, year) prevents duplicates.
# Required JSON fields: category, limit_amount, month, year
@app.route('/api/budget', methods=['POST'])
@login_required
def api_create_budget():
    """
    Navaneeth – REST API: Create a new monthly budget record for the logged-in user.
    Expected JSON body: { "category": "Food", "limit_amount": 5000, "month": 7, "year": 2026 }
    Returns: JSON with the new record's ID and a success message.
    """
    data = request.get_json()
    required = ['category', 'limit_amount', 'month', 'year']

    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO budget (user_id, category, limit_amount, month, year) VALUES (%s, %s, %s, %s, %s)",
                (user_id, data['category'], data['limit_amount'], data['month'], data['year'])
            )
            new_id = cur.lastrowid
        conn.close()
        return jsonify({'id': new_id, 'message': 'Budget record created successfully'}), 201
    except Exception as e:
        # Catches the UNIQUE KEY violation if budget already exists for same category/month/year
        return jsonify({'error': str(e)}), 400


# ══════════════════════════════════════════════════════════════
#  MODULE: INCOME, EXPENSES & BUDGET - HTML FORM PAGES (Developed by: Deepika)
#  Source: C:\Users\Vaishnavi\Desktop\Sample\Deepika\Smart-Finance-Insights-main
#
#  These are HTML page routes that render input forms (income.html,
#  expense.html, budget.html) where users can type in their data
#  and submit it through a regular HTML form POST request.
#
#  On GET request  : The empty form page is displayed to the user.
#  On POST request : The form data is validated, saved to MySQL, and
#                    the user is redirected back to the dashboard.
#
#  Balance Calculation Logic (Deepika):
#    total_income   = sum of all income records for this user
#    total_expenses = sum of all expense records for this user
#    balance        = total_income - total_expenses  (Net savings)
# ══════════════════════════════════════════════════════════════

# ── Deepika: GET & POST /add-income ───────────────────────────────────────
# Renders the Add Income HTML form (income.html) when user opens the page.
# When the form is submitted (POST), validates the data and saves to MySQL.
@app.route('/add-income', methods=['GET', 'POST'])
@login_required
def add_income():
    """
    Deepika – HTML Form Page: Display and process the Add Income form.
    GET  : Renders the income.html form template.
    POST : Reads amount, source, income_date, notes from the submitted form.
           Validates that amount is a positive number and required fields are filled.
           Inserts the record into the income table linked to the current user.
           Redirects back to /dashboard on success, or shows an error message.
    """
    error = None  # Holds any validation error message to show the user

    if request.method == 'POST':
        # Read form fields submitted by the user
        source      = request.form.get('source', '').strip()       # Income source name
        amount_str  = request.form.get('amount', '').strip()       # Amount as text (needs conversion)
        income_date = request.form.get('income_date', '').strip()  # Date string e.g. "2026-07-01"
        notes       = request.form.get('notes', '').strip()        # Optional notes

        # Validation: Check all required fields are provided and non-empty
        if not source or not amount_str or not income_date:
            error = 'Source, Amount, and Date are required fields.'
        else:
            try:
                amount = float(amount_str)  # Convert text to number (raises ValueError if invalid)
                if amount <= 0:
                    error = 'Amount must be a positive number greater than zero.'
            except ValueError:
                error = 'Please enter a valid numeric amount.'

        # If no validation errors, save to database and redirect to dashboard
        if not error:
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    # Insert income record linked to the logged-in user's ID
                    cur.execute(
                        "INSERT INTO income (user_id, source, amount, income_date, notes) VALUES (%s, %s, %s, %s, %s)",
                        (session.get('user_id'), source, amount, income_date, notes)
                    )
                conn.close()
                flash('Income record added successfully!', 'success')
                return redirect(url_for('dashboard'))  # Go back to dashboard after saving
            except Exception as e:
                error = f'Database error: {str(e)}'

    # Render the form page (on GET or if there was a validation error on POST)
    return render_template('income.html', error=error, user_name=session.get('user_name', 'User'))


# ── Deepika: GET & POST /add-expense ──────────────────────────────────────
# Renders the Add Expense HTML form (expense.html) when user opens the page.
# When the form is submitted (POST), validates the data and saves to MySQL.
@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """
    Deepika – HTML Form Page: Display and process the Add Expense form.
    GET  : Renders the expense.html form template.
    POST : Reads category, amount, expense_date, notes from the submitted form.
           Validates required fields and positive amount.
           Inserts the record into the expenses table linked to the current user.
           Redirects back to /dashboard on success, or shows an error message.
    """
    error = None

    if request.method == 'POST':
        # Read form fields submitted by the user
        category     = request.form.get('category', '').strip()     # Expense category
        amount_str   = request.form.get('amount', '').strip()       # Amount as text
        expense_date = request.form.get('expense_date', '').strip() # Date string
        notes        = request.form.get('notes', '').strip()        # Optional notes

        # Validation: All required fields must be non-empty
        if not category or not amount_str or not expense_date:
            error = 'Category, Amount, and Date are required fields.'
        else:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    error = 'Amount must be a positive number greater than zero.'
            except ValueError:
                error = 'Please enter a valid numeric amount.'

        if not error:
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO expenses (user_id, category, amount, expense_date, notes) VALUES (%s, %s, %s, %s, %s)",
                        (session.get('user_id'), category, amount, expense_date, notes)
                    )
                conn.close()
                flash('Expense record added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f'Database error: {str(e)}'

    return render_template('expense.html', error=error, user_name=session.get('user_name', 'User'))


# ── Deepika: GET & POST /add-budget ───────────────────────────────────────
# Renders the Create Budget HTML form (budget.html) when user opens the page.
# When the form is submitted (POST), validates the data and saves to MySQL.
@app.route('/add-budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    """
    Deepika – HTML Form Page: Display and process the Create Budget form.
    GET  : Renders the budget.html form template.
    POST : Reads category, limit_amount, month, year from the submitted form.
           Validates required fields and positive amount.
           Inserts the record into the budget table (UNIQUE KEY prevents duplicates).
           Redirects back to /dashboard on success, or shows an error message.
    """
    error = None

    if request.method == 'POST':
        # Read form fields submitted by the user
        category     = request.form.get('category', '').strip()     # Budget category
        amount_str   = request.form.get('limit_amount', '').strip() # Max spending limit
        month_str    = request.form.get('month', '').strip()        # Month number (1-12)
        year_str     = request.form.get('year', '').strip()         # 4-digit year

        # Validation: All required fields must be non-empty
        if not category or not amount_str or not month_str or not year_str:
            error = 'Category, Limit Amount, Month, and Year are all required.'
        else:
            try:
                limit_amount = float(amount_str)
                month        = int(month_str)
                year         = int(year_str)
                # Month must be between 1 (January) and 12 (December)
                if limit_amount <= 0:
                    error = 'Limit amount must be greater than zero.'
                elif not (1 <= month <= 12):
                    error = 'Month must be a number between 1 and 12.'
            except ValueError:
                error = 'Please enter valid numeric values for amount, month, and year.'

        if not error:
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO budget (user_id, category, limit_amount, month, year) VALUES (%s, %s, %s, %s, %s)",
                        (session.get('user_id'), category, limit_amount, month, year)
                    )
                conn.close()
                flash('Budget record created successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                # The UNIQUE KEY on (user_id, category, month, year) will raise error if duplicate
                error = f'Could not create budget (it may already exist for this category/month): {str(e)}'

    return render_template('budget.html', error=error, user_name=session.get('user_name', 'User'))


# ── Deepika: Balance Summary API ───────────────────────────────────────────
# This logic was developed by Deepika in her Smart Finance Insights project.
# It calculates: total_income, total_expenses, and net balance for the user.
# Used by the dashboard to show live financial summary numbers.
@app.route('/api/balance-summary')
@login_required
def api_balance_summary():
    """
    Deepika – Dynamic Balance Calculation:
    Fetches income and expense totals for the logged-in user and calculates net balance.
    Formula: balance = total_income - total_expenses

    Returns JSON:
    {
        "total_income"  : 50000.00,   (Sum of all income entries)
        "total_expenses": 20000.00,   (Sum of all expense entries)
        "balance"       : 30000.00    (Net savings = income minus expenses)
    }
    """
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Query total income: SUM all amount values for this user
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s", (user_id,))
            total_income = float(cur.fetchone()['total'])

            # Query total expenses: SUM all amount values for this user
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s", (user_id,))
            total_expenses = float(cur.fetchone()['total'])

        conn.close()

        # Deepika's balance formula: remaining money after all expenses
        balance = total_income - total_expenses

        return jsonify({
            'total_income'  : total_income,
            'total_expenses': total_expenses,
            'balance'       : balance
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  GLOBAL HTTP ERROR HANDLERS
# ══════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    """Handles 404 Page Not Found errors by redirecting to login page."""
    return render_template('login.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handles 500 Internal Server errors gracefully."""
    flash('An internal server error occurred.', 'danger')
    return render_template('login.html'), 500


# ══════════════════════════════════════════════════════════════
#  APPLICATION EXECUTION ENTRY
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    # Runs local Flask development server on port 5000 with Debug mode active
    app.run(debug=True, host='0.0.0.0', port=5000)
