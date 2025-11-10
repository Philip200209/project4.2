from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from utils.db import get_db_connection
from utils.audit_utils import log_action

# BLUEPRINT DEFINITION - THIS WAS MISSING
alerts_bp = Blueprint('alerts_bp', __name__, url_prefix='/alerts')

@alerts_bp.route('/')
@login_required
def alerts_dashboard():
    """Main alerts dashboard showing all alerts across the system"""
    print("🎯 [DEBUG] Alerts dashboard route called!")
    print(f"👤 [DEBUG] Current user: {current_user.username}, Role: {current_user.role.name}")
    
    if current_user.role.name not in ['admin', 'loan_officer']:
        print("❌ [DEBUG] User not authorized")
        flash("You don't have permission to view alerts.", "error")
        return render_template('unauthorized.html')

    print("✅ [DEBUG] User authorized - proceeding with database query")
    
    conn = get_db_connection()
    if not conn:
        print("❌ [DEBUG] Database connection failed")
        return "Database connection failed"
    
    cursor = conn.cursor(dictionary=True)

    try:
        print("🔍 [DEBUG] Testing simple query first...")
        
        # Test 1: Simple query without JOIN
        cursor.execute("SELECT COUNT(*) as count FROM alerts")
        simple_count = cursor.fetchone()
        print(f"📊 [DEBUG] Simple count query result: {simple_count}")
        
        # Test 2: Get alerts without JOIN
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10")
        simple_alerts = cursor.fetchall()
        print(f"📊 [DEBUG] Simple alerts query found {len(simple_alerts)} alerts")
        
        # Test 3: The actual JOIN query
        print("🔍 [DEBUG] Testing JOIN query...")
        cursor.execute("""
            SELECT 
                a.id,
                a.client_id,
                a.type, 
                a.message, 
                a.severity, 
                a.created_at, 
                a.status,
                c.name as client_name
            FROM alerts a
            LEFT JOIN clients c ON a.client_id = c.id
            ORDER BY a.created_at DESC
            LIMIT 50
        """)
        alerts = cursor.fetchall()
        print(f"📊 [DEBUG] JOIN query found {len(alerts)} alerts")
        
        if len(alerts) > 0:
            print("📄 [DEBUG] First alert from JOIN query:", alerts[0])
        else:
            print("📭 [DEBUG] No alerts found in JOIN query")

        # Get alert statistics - SIMPLIFIED VERSION
        cursor.execute("""
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_priority,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_priority,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_priority,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_alerts,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_alerts
            FROM alerts
        """)
        stats = cursor.fetchone()
        
        print(f"📈 [DEBUG] Alert stats: {stats}")

    except Exception as e:
        print(f"❌ [DEBUG] Database error: {e}")
        import traceback
        traceback.print_exc()
        alerts = []
        stats = {
            'total_alerts': 0,
            'high_priority': 0,
            'medium_priority': 0,
            'low_priority': 0,
            'active_alerts': 0,
            'resolved_alerts': 0
        }

    finally:
        cursor.close()
        conn.close()

    print("🎨 [DEBUG] Rendering template with data...")
    print(f"🎨 [DEBUG] Sending {len(alerts)} alerts to template")
    
    # Debug: Check what data we actually have
    if alerts:
        print("🔍 [DEBUG] Sample alert data structure:")
        for i, alert in enumerate(alerts[:2]):  # Show first 2 alerts
            print(f"   Alert {i}: {dict(alert)}")
    
    # If JOIN query failed but simple query worked, use simple data with client names
    if not alerts and simple_alerts:
        print("🔄 [DEBUG] Using simple alerts data since JOIN failed")
        alerts = simple_alerts
        
        # Try to get client names for simple alerts
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            client_names = {}
            
            # Get client names for all client_ids in alerts
            client_ids = list(set(alert['client_id'] for alert in alerts if alert.get('client_id')))
            if client_ids:
                format_strings = ','.join(['%s'] * len(client_ids))
                cursor.execute(f"SELECT id, name FROM clients WHERE id IN ({format_strings})", tuple(client_ids))
                clients = cursor.fetchall()
                client_names = {client['id']: client['name'] for client in clients}
            
            # Add client_name to each alert
            for alert in alerts:
                alert['client_name'] = client_names.get(alert.get('client_id'), 'No client')
                
        except Exception as e:
            print(f"❌ [DEBUG] Error getting client names: {e}")
            for alert in alerts:
                alert['client_name'] = 'Unknown client'
        finally:
            cursor.close()
            conn.close()
        
        # Create stats for fallback data
        stats = {
            'total_alerts': len(simple_alerts),
            'high_priority': sum(1 for alert in simple_alerts if alert.get('severity') == 'high'),
            'medium_priority': sum(1 for alert in simple_alerts if alert.get('severity') == 'medium'),
            'low_priority': sum(1 for alert in simple_alerts if alert.get('severity') == 'low'),
            'active_alerts': sum(1 for alert in simple_alerts if alert.get('status') == 'active'),
            'resolved_alerts': sum(1 for alert in simple_alerts if alert.get('status') == 'resolved')
        }
    
    return render_template(
        'alerts_dashboard.html', 
        alerts=alerts, 
        stats=stats,
        alert_types=[],
        username=current_user.username
    )

# ... rest of your routes remain the same ...