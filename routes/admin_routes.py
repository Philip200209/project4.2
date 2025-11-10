# routes/admin_routes.py

from flask import Blueprint, render_template, session
from auth_utils import login_required, role_required
from database import get_db_connection
from data_manager import log_action

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# 🛡️ Admin Dashboard
@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 📊 Live stats
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    cursor.execute("SELECT COUNT(*) AS total_clients FROM clients")
    total_clients = cursor.fetchone()['total_clients']

    cursor.execute("SELECT COUNT(*) AS total_loans FROM loans")
    total_loans = cursor.fetchone()['total_loans']

    cursor.execute("SELECT COUNT(*) AS defaulted_loans FROM loans WHERE repayment_status = 'defaulted'")
    defaulted_loans = cursor.fetchone()['defaulted_loans']

    cursor.close()
    conn.close()

    log_action(session.get('user_id'), session.get('username'), "Viewed admin dashboard", "Admin")

    return render_template(
        'admin_dashboard.html',
        username=session.get('username'),
        total_users=total_users,
        total_clients=total_clients,
        total_loans=total_loans,
        defaulted_loans=defaulted_loans
    )

# 👥 View Users
@admin_bp.route('/view_users')
@login_required
@role_required('admin')
def view_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    log_action(session.get('user_id'), session.get('username'), "Viewed user list", "Admin")

    return render_template('view_users.html', users=users)
