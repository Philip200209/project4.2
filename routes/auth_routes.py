from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
from models.role import Role

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

# 🔐 Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print("✅ /auth/login route hit")

    if current_user.is_authenticated:
        print("🔁 User already logged in")
        role_name = current_user.role  # FIXED: Use direct attribute access
        print(f"🔀 Redirecting to dashboard for role: {role_name}")
        return redirect_to_dashboard(role_name)

    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        print(f"🔐 Login attempt: '{username_or_email}'")

        try:
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email.lower())
            ).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Login successful', 'success')
                role_name = user.role  # FIXED: Use direct attribute access
                print(f"✅ Login successful for '{username_or_email}', role: {role_name}")
                return redirect_to_dashboard(role_name)
            else:
                print(f"❌ Login failed for '{username_or_email}'")
                flash('Invalid username or password', 'danger')
        except Exception as e:
            print(f"❌ Database error during login: {e}")
            flash('System error during login', 'danger')

    return render_template('login.html')

# 🚪 Logout Route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_bp.login'))

# 📝 Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role_name = request.form.get('role', 'borrower').strip().lower()

        print(f"📝 Registration attempt: username='{username}', email='{email}', role='{role_name}'")

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return redirect(url_for('auth_bp.register'))

        try:
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                flash('Username or email already exists.', 'warning')
                return redirect(url_for('auth_bp.register'))

            # Map form roles to database ENUM values
            role_mapping = {
                'admin': 'admin',
                'officer': 'loan_officer',
                'borrower': 'borrower'
            }
            
            database_role = role_mapping.get(role_name)
            
            if not database_role:
                flash(f"Invalid role: '{role_name}'. Must be one of: admin, officer, borrower", 'danger')
                return redirect(url_for('auth_bp.register'))

            # Create user with just the role string
            new_user = User(
                username=username,
                email=email,
                role=database_role  # Use the ENUM column directly
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()

            print(f"✅ SUCCESS: User '{username}' registered with role '{database_role}'")
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth_bp.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('System error during registration', 'danger')
            print(f"❌ Registration error: {e}")
            import traceback
            traceback.print_exc()

    return render_template('register.html')

# 🔁 Helper: Safe dashboard redirect
def redirect_to_dashboard(role_name):
    if not role_name:
        flash("No role assigned to this user.", "danger")
        return redirect(url_for('auth_bp.login'))

    role_name = role_name.strip().lower()
    print(f"🔀 Redirecting to dashboard for role: {role_name}")

    # Map database role names to dashboard endpoints
    role_mapping = {
        'admin': 'dashboard_bp.admin_dashboard',
        'loan_officer': 'dashboard_bp.officer_dashboard',
        'borrower': 'dashboard_bp.borrower_dashboard'
    }

    dashboard_endpoint = role_mapping.get(role_name)
    
    if dashboard_endpoint:
        try:
            return redirect(url_for(dashboard_endpoint))
        except Exception as e:
            print(f"❌ Error redirecting to {dashboard_endpoint}: {e}")
            flash(f"Dashboard for role '{role_name}' is not available.", 'danger')
            return redirect(url_for('auth_bp.login'))
    else:
        flash(f"Unknown role: '{role_name}' — no dashboard available.", 'danger')
        return redirect(url_for('auth_bp.login'))

# 🧪 Test Route
@auth_bp.route('/test-login')
def test_login():
    return "<h1 style='color:green'>✅ Login route is working</h1>"

# 🔍 Debug route to check users
@auth_bp.route('/debug-users')
def debug_users():
    """Debug route to check existing users"""
    try:
        users = User.query.all()
        user_list = []
        
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,  # Direct attribute access
                'role_id': user.role_id,
                'has_password': bool(user.password_hash)
            })
        
        return {
            'total_users': len(users),
            'users': user_list
        }
    except Exception as e:
        return {'error': str(e)}

# 🔍 Debug route to check roles
@auth_bp.route('/debug-roles')
def debug_roles():
    """Debug route to check existing roles"""
    try:
        roles = Role.query.all()
        role_list = []
        
        for role in roles:
            role_list.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'user_count': len(role.users)
            })
        
        return {
            'total_roles': len(roles),
            'roles': role_list
        }
    except Exception as e:
        return {'error': str(e)}