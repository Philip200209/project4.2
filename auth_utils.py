from functools import wraps
from flask import session, redirect, url_for, flash

# Require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# Require specific role
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != required_role:
                flash('Access denied: insufficient permissions.', 'danger')
                return redirect(url_for('dashboard_bp.user_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
