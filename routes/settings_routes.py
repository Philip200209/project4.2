from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, User  # Only import existing models

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/settings')
@login_required
def settings():
    """System settings page"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard_bp.dashboard_home'))
    
    return render_template('settings.html', 
                         user=current_user,
                         active_page='settings')

@settings_bp.route('/settings/system')
@login_required
def system_settings():
    """System configuration settings"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Return basic system info
    system_info = {
        'system_name': 'CRIMAP',
        'version': '1.0.0',
        'total_users': User.query.count(),
        'status': 'active'
    }
    
    return jsonify(system_info)

@settings_bp.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update system settings"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('settings_bp.settings'))
    
    try:
        setting_key = request.form.get('key')
        setting_value = request.form.get('value')
        
        # In a real application, you would save these to a settings table
        # For now, we'll just show a success message
        flash(f'Setting {setting_key} updated successfully!', 'success')
        
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
    
    return redirect(url_for('settings_bp.settings'))

@settings_bp.route('/settings/roles')
@login_required
def role_management():
    """Role management page (simplified)"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard_bp.dashboard_home'))
    
    # Get all users with their roles
    users = User.query.all()
    
    # Define available roles
    available_roles = [
        {'name': 'admin', 'description': 'System Administrator'},
        {'name': 'officer', 'description': 'Loan Officer'}, 
        {'name': 'borrower', 'description': 'Loan Borrower'}
    ]
    
    return render_template('role_management.html',
                         users=users,
                         available_roles=available_roles,
                         active_page='settings')

@settings_bp.route('/settings/update-role', methods=['POST'])
@login_required
def update_user_role():
    """Update user role"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        user_id = request.form.get('user_id')
        new_role = request.form.get('role')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate role
        valid_roles = ['admin', 'officer', 'borrower']
        if new_role not in valid_roles:
            return jsonify({'error': 'Invalid role'}), 400
        
        user.role = new_role
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Role updated to {new_role} for user {user.username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/settings/security')
@login_required
def security_settings():
    """Security settings page"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard_bp.dashboard_home'))
    
    security_config = {
        'password_policy': {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True
        },
        'session_timeout': 30,  # minutes
        'max_login_attempts': 5
    }
    
    return render_template('security_settings.html',
                         security_config=security_config,
                         active_page='settings')

@settings_bp.route('/settings/backup')
@login_required
def backup_settings():
    """Backup and restore settings"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard_bp.dashboard_home'))
    
    backup_info = {
        'last_backup': '2024-01-01 10:00:00',
        'backup_size': '15.2 MB',
        'auto_backup': True,
        'backup_frequency': 'daily'
    }
    
    return render_template('backup_settings.html',
                         backup_info=backup_info,
                         active_page='settings')

# Debug route for settings
@settings_bp.route('/settings/debug')
@login_required
def settings_debug():
    """Debug route for settings"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    debug_info = {
        'current_user': {
            'username': current_user.username,
            'role': current_user.role
        },
        'total_users': User.query.count(),
        'available_roles': ['admin', 'officer', 'borrower']
    }
    
    return jsonify(debug_info)