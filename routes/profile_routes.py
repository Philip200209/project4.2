from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    print(f"👤 Profile accessed by user: {current_user.username}")
    
    # Initialize empty loan applications list since model might not exist
    loan_applications = []
    
    return render_template('profile.html', 
                         user=current_user, 
                         loan_applications=loan_applications,
                         active_page='profile')

@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        print(f"🔄 Updating profile for user: {current_user.username}")
        
        # Update basic info
        if username and username != current_user.username:
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('profile_bp.profile'))
            current_user.username = username
            print(f"📝 Updated username to: {username}")
        
        if email and email != current_user.email:
            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already exists. Please use a different email.', 'error')
                return redirect(url_for('profile_bp.profile'))
            current_user.email = email
            print(f"📝 Updated email to: {email}")
        
        # Update password if provided
        if current_password and new_password:
            # Verify current password
            if check_password_hash(current_user.password_hash, current_password):
                current_user.password_hash = generate_password_hash(new_password)
                flash('Password updated successfully!', 'success')
                print("🔑 Password updated successfully")
            else:
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('profile_bp.profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        print("✅ Profile updated successfully")
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile. Please try again.', 'error')
        print(f"❌ Profile update error: {str(e)}")
    
    return redirect(url_for('profile_bp.profile'))

@profile_bp.route('/profile/loan-history')
@login_required
def loan_history():
    """Full loan history page - placeholder for now"""
    flash('Loan history feature is coming soon!', 'info')
    return redirect(url_for('profile_bp.profile'))

# 🆕 Simple debug route
@profile_bp.route('/profile/debug')
@login_required
def debug_profile():
    """Debug route to check profile data"""
    return {
        'status': 'success',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role
        },
        'message': 'Profile system is working!'
    }