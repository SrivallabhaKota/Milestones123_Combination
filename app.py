import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import bcrypt
import re
from datetime import datetime, timedelta
from config import Config
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

# Starts database and tables
def init_db():
    try:
        conn = pymysql.connect(host=app.config['MYSQL_HOST'], port=app.config['MYSQL_PORT'], user=app.config['MYSQL_USER'], password=app.config['MYSQL_PASSWORD'], autocommit=True)
        with conn.cursor() as cur:
            cur.execute('CREATE DATABASE IF NOT EXISTS finsight CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
        conn.close()
        conn = pymysql.connect(host=app.config['MYSQL_HOST'], port=app.config['MYSQL_PORT'], user=app.config['MYSQL_USER'], password=app.config['MYSQL_PASSWORD'], database=app.config['MYSQL_DB'], autocommit=True)
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                  id          INT AUTO_INCREMENT PRIMARY KEY,
                  name        VARCHAR(100)  NOT NULL,
                  email       VARCHAR(100)  NOT NULL UNIQUE,
                  password    VARCHAR(255)  NOT NULL,
                  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            ''')
            cur.execute('''
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
            ''')
            cur.execute('''
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
            ''')
            cur.execute('''
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
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS investments (
                  id            INT AUTO_INCREMENT PRIMARY KEY,
                  user_id       INT           NOT NULL,
                  source        VARCHAR(100)  NOT NULL,
                  amount        DECIMAL(10,2) NOT NULL,
                  invest_date   DATE          NOT NULL,
                  invest_type   VARCHAR(50)   DEFAULT 'General',
                  notes         VARCHAR(255),
                  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            ''')
        conn.close()
        print("✅ Database 'finsight' and all tables (users, income, expenses, budget, investments) verified!")
    except Exception as e:
        print('❌ Database initialization error:', e)

init_db()


# Gets database connection
def get_db_connection():
    return pymysql.connect(host=app.config['MYSQL_HOST'], port=app.config['MYSQL_PORT'], user=app.config['MYSQL_USER'], password=app.config['MYSQL_PASSWORD'], database=app.config['MYSQL_DB'], cursorclass=pymysql.cursors.DictCursor, autocommit=True)

# Checks if user is logged in
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# Checks if email is valid
def is_valid_email(email: str) -> bool:
    pattern = '^[\\w\\.\\+\\-]+@[\\w\\-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Checks if password is strong
def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search('[A-Z]', password):
        return False
    if not re.search('[a-z]', password):
        return False
    if not re.search('\\d', password):
        return False
    if not re.search('[!@#$%^&*(),.?":{}|<>_\\-\\[\\]\\/\\\\]', password):
        return False
    return True

@app.route('/')
@app.route('/home')
# Shows home page
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Alias for home page
def index():
    return home()

@app.route('/login', methods=['GET', 'POST'])
# Handles user login
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember')
        if not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('login.html')
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('login.html')
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT id, name, email, password FROM users WHERE email = %s', (email,))
                user = cur.fetchone()
            conn.close()
        except Exception as e:
            print('DB Error during login:', e)
            flash(f'Database connection error: {e}', 'danger')
            return render_template('login.html')
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            if remember:
                app.permanent_session_lifetime = timedelta(days=30)
                session.permanent = True
            flash(f"Welcome back, {user['name']}! 🎉", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
# Handles user registration
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        errors = []
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
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM users WHERE email = %s', (email,))
                existing = cur.fetchone()
                if existing:
                    conn.close()
                    flash('An account with this email already exists. Please log in.', 'warning')
                    return render_template('register.html')
                hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
                cur.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_pw.decode('utf-8')))
            conn.close()
        except Exception as e:
            print('DB ERROR DURING REGISTRATION:', e)
            flash(f'Registration failed: {e}', 'danger')
            return render_template('register.html')
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login_page'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
# Shows dashboard page
def dashboard():
    user_name = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    return render_template('dashboard.html', user_name=user_name, user_email=user_email)

@app.route('/logout')
@login_required
# Logs out the user
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route('/budget')
@login_required
# Alias for budget view
def budget():
    user_name = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    return render_template('dashboard.html', user_name=user_name, user_email=user_email)

@app.route('/forgot-password')
# Forgot password link
def forgot_password():
    flash('Password reset feature coming soon. Contact support for help.', 'info')
    return redirect(url_for('login_page'))

@app.route('/api/dashboard-summary')
@login_required
# API: gets dashboard stats
def api_dashboard_summary():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s', (user_id,))
            total_income = float(cur.fetchone()['total'])
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s', (user_id,))
            total_expenses = float(cur.fetchone()['total'])
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM investments WHERE user_id = %s', (user_id,))
            total_investments = float(cur.fetchone()['total'])
        conn.close()
        total_savings = min(total_income * 0.25, max(0, total_income - total_expenses - total_investments))
        remaining_balance = max(0, total_income - total_expenses - total_investments - total_savings)
        
        if total_income > 0:
            expenses_pct = round(total_expenses / total_income * 100)
            savings_pct = round(total_savings / total_income * 100)
            investments_pct = round(total_investments / total_income * 100)
            remaining_pct = max(0, 100 - expenses_pct - savings_pct - investments_pct)
        else:
            expenses_pct = savings_pct = investments_pct = remaining_pct = 0
            
        prev_month = datetime.now().replace(day=1) - timedelta(days=1)
        try:
            conn2 = get_db_connection()
            with conn2.cursor() as cur:
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM income WHERE user_id=%s AND MONTH(income_date)=MONTH(CURDATE()) AND YEAR(income_date)=YEAR(CURDATE())', (user_id,))
                cur_income = float(cur.fetchone()['t'])
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM income WHERE user_id=%s AND MONTH(income_date)=%s AND YEAR(income_date)=%s', (user_id, prev_month.month, prev_month.year))
                prev_income = float(cur.fetchone()['t'])
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s AND MONTH(expense_date)=MONTH(CURDATE()) AND YEAR(expense_date)=YEAR(CURDATE())', (user_id,))
                cur_expenses = float(cur.fetchone()['t'])
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s AND MONTH(expense_date)=%s AND YEAR(expense_date)=%s', (user_id, prev_month.month, prev_month.year))
                prev_expenses = float(cur.fetchone()['t'])
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM investments WHERE user_id=%s AND MONTH(invest_date)=MONTH(CURDATE()) AND YEAR(invest_date)=YEAR(CURDATE())', (user_id,))
                cur_invest = float(cur.fetchone()['t'])
                cur.execute('SELECT COALESCE(SUM(amount),0) AS t FROM investments WHERE user_id=%s AND MONTH(invest_date)=%s AND YEAR(invest_date)=%s', (user_id, prev_month.month, prev_month.year))
                prev_invest = float(cur.fetchone()['t'])
            conn2.close()
            def pct_change(cur_val, prev_val):
                if prev_val > 0:
                    return round((cur_val - prev_val) / prev_val * 100, 1)
                return 0
            income_change = pct_change(cur_income, prev_income)
            expenses_change = pct_change(cur_expenses, prev_expenses)
            invest_change = pct_change(cur_invest, prev_invest)
            cur_savings = min(cur_income * 0.25, max(0, cur_income - cur_expenses - cur_invest))
            prev_savings = min(prev_income * 0.25, max(0, prev_income - prev_expenses - prev_invest))
            savings_change = pct_change(cur_savings, prev_savings)
        except:
            income_change = expenses_change = savings_change = invest_change = 0
        return jsonify({
            'income':      {'total': total_income,      'change': income_change},
            'expenses':    {'total': total_expenses,    'change': expenses_change},
            'savings':     {'total': total_savings,     'change': savings_change},
            'investments': {'total': total_investments, 'change': invest_change},
            'remaining':   {'total': remaining_balance},
            'chart_segments': {
                'expenses': expenses_pct,
                'savings': savings_pct,
                'investments': investments_pct,
                'remaining': remaining_pct
            }
        })
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/user-profile')
@login_required
# API: gets user profile
def api_user_profile():
    return jsonify({'name': session.get('user_name', 'User'), 'email': session.get('user_email', ''), 'role': 'Premium User', 'member_since': 'Active', 'account_status': 'Verified', 'financial_health_score': 100})

@app.route('/api/recent-transactions')
@login_required
# API: gets recent transactions
def api_recent_transactions():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, source AS title, 'Income' AS category, amount, income_date AS date, 'income' AS type, created_at FROM income WHERE user_id = %s", (user_id,))
            incomes = cur.fetchall()
            cur.execute("SELECT id, category AS title, 'Expense' AS category, amount, expense_date AS date, 'expense' AS type, created_at FROM expenses WHERE user_id = %s", (user_id,))
            expenses = cur.fetchall()
            cur.execute("SELECT id, source AS title, invest_type AS category, amount, invest_date AS date, 'investment' AS type, created_at FROM investments WHERE user_id = %s", (user_id,))
            investments = cur.fetchall()
        conn.close()
        transactions = incomes + expenses + investments
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        recent = transactions[:8]
        result = []
        for t in recent:
            result.append({'title': t['title'], 'category': t['category'], 'amount': float(t['amount']), 'type': t['type'], 'date': str(t['date'])})
        return jsonify(result)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/monthly-spending')
@login_required
# API: gets monthly spending data
def api_monthly_spending():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
                SELECT MONTHNAME(expense_date) AS month, SUM(amount) AS total 
                FROM expenses 
                WHERE user_id = %s AND expense_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY month 
                ORDER BY MIN(expense_date) ASC
            ''', (user_id,))
            rows = cur.fetchall()
        conn.close()
        labels = [r['month'][:3] for r in rows] if rows else ['No Data']
        values = [float(r['total']) for r in rows] if rows else [0]
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/insights')
@login_required
# API: gets smart insights
def api_insights():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s AND MONTH(expense_date) = MONTH(CURDATE()) AND YEAR(expense_date) = YEAR(CURDATE())', (user_id,))
            monthly_spent = float(cur.fetchone()['total'])
            cur.execute('SELECT COALESCE(SUM(limit_amount), 0) AS total_budget FROM budget WHERE user_id = %s AND month = MONTH(CURDATE()) AND year = YEAR(CURDATE())', (user_id,))
            total_budget = float(cur.fetchone()['total_budget'])
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s AND MONTH(income_date) = MONTH(CURDATE()) AND YEAR(income_date) = YEAR(CURDATE())', (user_id,))
            monthly_income = float(cur.fetchone()['total'])
        conn.close()
        if total_budget > 0:
            budget_pct = min(100, round(monthly_spent / total_budget * 100))
            if budget_pct > 100:
                budget_status = 'Over Budget'
                budget_desc = f'Spending is {budget_pct - 100}% over plan'
                budget_color = '#EF4444'
            else:
                budget_status = 'On Track'
                budget_desc = f'Spending is {100 - budget_pct}% below plan'
                budget_color = '#2563EB'
        else:
            budget_pct = 0
            budget_status = 'No Budget Set'
            budget_desc = 'Create a budget to track spending'
            budget_color = '#94A3B8'
        if monthly_income > 0:
            savings = max(0, monthly_income - monthly_spent)
            savings_rate = round(savings / monthly_income * 100)
            savings_status = f'{savings_rate}% Saved'
            savings_desc = 'Savings rate this month'
        else:
            savings_rate = 0
            savings_status = '0% Saved'
            savings_desc = 'No income recorded this month'
        return jsonify([{'title': 'Budget Status', 'status': budget_status, 'description': budget_desc, 'percentage': budget_pct, 'color': budget_color}, {'title': 'Savings Rate', 'status': savings_status, 'description': savings_desc, 'percentage': savings_rate, 'color': '#10B981'}, {'title': 'Investment Growth', 'status': '+0%', 'description': 'Tracking coming soon', 'percentage': 0, 'color': '#8B5CF6'}, {'title': 'Monthly Spending', 'status': f'₹{monthly_spent:,.0f}', 'description': 'Total spent this month', 'percentage': min(100, monthly_spent / max(1, monthly_income) * 100) if monthly_income > 0 else 0, 'color': '#3B82F6'}])
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/view-all')
@login_required
# Placeholder: view transactions
def view_all():
    return jsonify({'message': 'Recent transactions view is ready for the next step.'})

@app.route('/view-detailed-report')
@login_required
# Placeholder: view reports
def view_detailed_report():
    return jsonify({'message': 'The detailed report page is ready to be expanded.'})

@app.route('/quick-actions/expense')
@login_required
# Placeholder: add expense
def quick_action_expense():
    return jsonify({'message': 'Expense tracking action placeholder'})

@app.route('/quick-actions/budget')
@login_required
# Placeholder: add budget
def quick_action_budget():
    return jsonify({'message': 'Budget creation action placeholder'})

@app.route('/quick-actions/investment')
@login_required
# Placeholder: add investment
def quick_action_investment():
    return jsonify({'message': 'Investment entry action placeholder'})

@app.route('/quick-actions/report')
@login_required
# Placeholder: get reports
def quick_action_report():
    return jsonify({'message': 'Report generation action placeholder'})

@app.route('/api/income', methods=['GET'])
@login_required
# API: gets income list
def api_get_income():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT id, source, amount, income_date, notes, created_at FROM income WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
            rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({'id': row['id'], 'source': row['source'], 'amount': float(row['amount']), 'income_date': str(row['income_date']), 'notes': row['notes'], 'created_at': str(row['created_at'])})
        return (jsonify(result), 200)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/income', methods=['POST'])
@login_required
# API: adds new income
def api_create_income():
    data = request.get_json()
    required = ['source', 'amount', 'income_date']
    if not all((k in data for k in required)):
        return (jsonify({'error': f'Missing required fields: {required}'}), 400)
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('INSERT INTO income (user_id, source, amount, income_date, notes) VALUES (%s, %s, %s, %s, %s)', (user_id, data['source'], data['amount'], data['income_date'], data.get('notes', '')))
            new_id = cur.lastrowid
        conn.close()
        return (jsonify({'id': new_id, 'message': 'Income record created successfully'}), 201)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/expenses', methods=['GET'])
@login_required
# API: gets expense list
def api_get_expenses():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT id, category, amount, expense_date, notes, created_at FROM expenses WHERE user_id = %s ORDER BY created_at DESC', (user_id,))
            rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({'id': row['id'], 'category': row['category'], 'amount': float(row['amount']), 'expense_date': str(row['expense_date']), 'notes': row['notes'], 'created_at': str(row['created_at'])})
        return (jsonify(result), 200)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/expenses', methods=['POST'])
@login_required
# API: adds new expense
def api_create_expense():
    data = request.get_json()
    required = ['category', 'amount', 'expense_date']
    if not all((k in data for k in required)):
        return (jsonify({'error': f'Missing required fields: {required}'}), 400)
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('INSERT INTO expenses (user_id, category, amount, expense_date, notes) VALUES (%s, %s, %s, %s, %s)', (user_id, data['category'], data['amount'], data['expense_date'], data.get('notes', '')))
            new_id = cur.lastrowid
        conn.close()
        return (jsonify({'id': new_id, 'message': 'Expense record created successfully'}), 201)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/budget', methods=['GET'])
@login_required
# API: gets budget list
def api_get_budget():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT id, category, limit_amount, month, year, created_at FROM budget WHERE user_id = %s ORDER BY year DESC, month DESC', (user_id,))
            rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({'id': row['id'], 'category': row['category'], 'limit_amount': float(row['limit_amount']), 'month': row['month'], 'year': row['year'], 'created_at': str(row['created_at'])})
        return (jsonify(result), 200)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/budget', methods=['POST'])
@login_required
# API: adds new budget
def api_create_budget():
    data = request.get_json()
    required = ['category', 'limit_amount', 'month', 'year']
    if not all((k in data for k in required)):
        return (jsonify({'error': f'Missing required fields: {required}'}), 400)
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('INSERT INTO budget (user_id, category, limit_amount, month, year) VALUES (%s, %s, %s, %s, %s)', (user_id, data['category'], data['limit_amount'], data['month'], data['year']))
            new_id = cur.lastrowid
        conn.close()
        return (jsonify({'id': new_id, 'message': 'Budget record created successfully'}), 201)
    except Exception as e:
        return (jsonify({'error': str(e)}), 400)

@app.route('/add-income', methods=['GET', 'POST'])
@login_required
# Form page: adds income
def add_income():
    error = None
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        amount_str = request.form.get('amount', '').strip()
        income_date = request.form.get('income_date', '').strip()
        notes = request.form.get('notes', '').strip()
        if not source or not amount_str or not income_date:
            error = 'Source, Amount, and Date are required fields.'
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
                    cur.execute('INSERT INTO income (user_id, source, amount, income_date, notes) VALUES (%s, %s, %s, %s, %s)', (session.get('user_id'), source, amount, income_date, notes))
                conn.close()
                flash('Income record added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('income.html', error=error, user_name=session.get('user_name', 'User'))

@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
# Form page: adds expense
def add_expense():
    error = None
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        amount_str = request.form.get('amount', '').strip()
        expense_date = request.form.get('expense_date', '').strip()
        notes = request.form.get('notes', '').strip()
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
                    cur.execute('INSERT INTO expenses (user_id, category, amount, expense_date, notes) VALUES (%s, %s, %s, %s, %s)', (session.get('user_id'), category, amount, expense_date, notes))
                conn.close()
                flash('Expense record added successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('expense.html', error=error, user_name=session.get('user_name', 'User'))

@app.route('/add-budget', methods=['GET', 'POST'])
@login_required
# Form page: adds budget
def add_budget():
    error = None
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        amount_str = request.form.get('limit_amount', '').strip()
        month_str = request.form.get('month', '').strip()
        year_str = request.form.get('year', '').strip()
        if not category or not amount_str or not month_str or not year_str:
            error = 'Category, Limit Amount, Month, and Year are all required.'
        else:
            try:
                limit_amount = float(amount_str)
                month = int(month_str)
                year = int(year_str)
                if limit_amount <= 0:
                    error = 'Limit amount must be greater than zero.'
                elif not 1 <= month <= 12:
                    error = 'Month must be a number between 1 and 12.'
            except ValueError:
                error = 'Please enter valid numeric values for amount, month, and year.'
        if not error:
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO budget (user_id, category, limit_amount, month, year) VALUES (%s, %s, %s, %s, %s)', (session.get('user_id'), category, limit_amount, month, year))
                conn.close()
                flash('Budget record created successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f'Could not create budget (it may already exist for this category/month): {str(e)}'
    return render_template('budget.html', error=error, user_name=session.get('user_name', 'User'))

@app.route('/add-investment', methods=['GET', 'POST'])
@login_required
# Form page: adds investment
def add_investment():
    error = None
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        amount_str = request.form.get('amount', '').strip()
        invest_date = request.form.get('invest_date', '').strip()
        invest_type = request.form.get('invest_type', 'General').strip()
        notes = request.form.get('notes', '').strip()
        if not source or not amount_str or not invest_date:
            error = 'Source, Amount, and Date are required fields.'
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
                        'INSERT INTO investments (user_id, source, amount, invest_date, invest_type, notes) VALUES (%s, %s, %s, %s, %s, %s)',
                        (session.get('user_id'), source, amount, invest_date, invest_type, notes)
                    )
                conn.close()
                flash('Investment record added successfully! 📈', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('investment.html', error=error, user_name=session.get('user_name', 'User'))

@app.route('/api/balance-summary')
@login_required
# API: gets total balance
def api_balance_summary():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s', (user_id,))
            total_income = float(cur.fetchone()['total'])
            cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s', (user_id,))
            total_expenses = float(cur.fetchone()['total'])
        conn.close()
        balance = total_income - total_expenses
        return (jsonify({'total_income': total_income, 'total_expenses': total_expenses, 'balance': balance}), 200)
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

@app.route('/api/reset-data', methods=['POST'])
@login_required
# API: resets all data to 0
def api_reset_data():
    user_id = session.get('user_id')
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM income WHERE user_id = %s', (user_id,))
            cur.execute('DELETE FROM expenses WHERE user_id = %s', (user_id,))
            cur.execute('DELETE FROM budget WHERE user_id = %s', (user_id,))
            cur.execute('DELETE FROM investments WHERE user_id = %s', (user_id,))
        conn.close()
        return jsonify({'status': 'success', 'message': 'All your data has been reset to 0.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
# Handles 404 error
def not_found(e):
    return (render_template('login.html'), 404)

@app.errorhandler(500)
# Handles 500 error
def server_error(e):
    flash('An internal server error occurred.', 'danger')
    return (render_template('login.html'), 500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
