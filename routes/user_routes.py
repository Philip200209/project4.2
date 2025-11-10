from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_utils import login_required, role_required
from database import get_db_connection
from werkzeug.security import generate_password_hash

users_bp = Blueprint('users_bp', __name__)

# View all users
@users_bp.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_users.html', users=users)

# Add new user
@users_bp.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, password_hash, role))
        conn.commit()
        cursor.close()
        conn.close()

        flash('User added successfully.', 'success')
        return redirect(url_for('users_bp.manage_users'))

    return render_template('add_user.html')

# Edit user
@users_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        cursor.execute("""
            UPDATE users SET username = %s, role = %s WHERE id = %s
        """, (username, role, user_id))
        conn.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('users_bp.manage_users'))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_user.html', user=user)

# Delete user
@users_bp.route('/admin/users/delete/<int:user_id>')
@login_required
@role_required('admin')
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('users_bp.manage_users'))
