from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from utils.db import get_db_connection
from utils.audit_utils import log_action

# Blueprint definition
interventions_bp = Blueprint('interventions_bp', __name__, url_prefix='/interventions')

@interventions_bp.route('/')
@login_required
def interventions_dashboard():
    """Main interventions dashboard"""
    print("🎯 [DEBUG] Interventions dashboard route called!")
    print(f"👤 [DEBUG] Current user: {current_user.username}, Role: {current_user.role.name}")
    
    # Check authorization
    if current_user.role.name not in ['admin', 'loan_officer']:
        flash("You don't have permission to view interventions.", "error")
        return render_template('unauthorized.html')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        print("🔍 [DEBUG] Querying interventions...")
        
        # First, check if interventions table exists
        cursor.execute("SHOW TABLES LIKE 'interventions'")
        table_exists = cursor.fetchone()
        print(f"📊 [DEBUG] Interventions table exists: {table_exists is not None}")
        
        if not table_exists:
            print("❌ [DEBUG] Interventions table doesn't exist!")
            interventions = []
        else:
            # Try to get interventions with JOINs
            cursor.execute("""
                SELECT 
                    i.id,
                    i.client_id,
                    i.loan_id,
                    i.type,
                    i.description,
                    i.priority,
                    i.status,
                    i.created_at,
                    i.assigned_to,
                    c.name as client_name,
                    l.loan_amount,
                    u.username as assigned_officer
                FROM interventions i
                LEFT JOIN clients c ON i.client_id = c.id
                LEFT JOIN loans l ON i.loan_id = l.id  
                LEFT JOIN users u ON i.assigned_to = u.id
                ORDER BY i.created_at DESC
                LIMIT 50
            """)
            interventions = cursor.fetchall()
            
            print(f"📊 [DEBUG] Found {len(interventions)} interventions")
            
            if interventions:
                print("📄 [DEBUG] First intervention:", interventions[0])
            else:
                print("📭 [DEBUG] No interventions found - table is empty")

    except Exception as e:
        print(f"❌ [DEBUG] Database error: {e}")
        import traceback
        traceback.print_exc()
        interventions = []

    finally:
        cursor.close()
        conn.close()

    print("🎨 [DEBUG] Rendering template...")
    return render_template(
        'interventions.html', 
        interventions=interventions, 
        username=current_user.username
    )

@interventions_bp.route('/debug')
@login_required
def debug_interventions():
    """Debug route to check interventions data"""
    print("🎯 [DEBUG] Interventions debug route called")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    result = {
        'table_exists': False,
        'interventions_count': 0,
        'sample_data': [],
        'tables': {}
    }
    
    try:
        # Test 1: Check if interventions table exists
        cursor.execute("SHOW TABLES LIKE 'interventions'")
        table_exists = cursor.fetchone()
        result['table_exists'] = table_exists is not None
        print(f"📊 [DEBUG] Interventions table exists: {result['table_exists']}")
        
        if result['table_exists']:
            # Test 2: Count interventions
            cursor.execute("SELECT COUNT(*) as count FROM interventions")
            count_result = cursor.fetchone()
            result['interventions_count'] = count_result['count']
            print(f"📊 [DEBUG] Total interventions: {result['interventions_count']}")
            
            # Test 3: Get sample interventions
            cursor.execute("SELECT * FROM interventions LIMIT 5")
            result['sample_data'] = cursor.fetchall()
            print(f"📊 [DEBUG] Sample interventions: {result['sample_data']}")
        
        # Test 4: Check related tables
        for table in ['clients', 'loans', 'users']:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            exists = cursor.fetchone()
            result['tables'][table] = exists is not None
            print(f"📊 [DEBUG] {table} table exists: {result['tables'][table]}")
        
    except Exception as e:
        print(f"❌ [DEBUG] Database error: {e}")
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        
    finally:
        cursor.close()
        conn.close()

    return f"""
    <html>
    <head>
        <title>Interventions Debug</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
            .info {{ color: blue; }}
        </style>
    </head>
    <body>
        <h1>Interventions Debug Info</h1>
        
        <h2>Database Status</h2>
        <p><strong>Interventions Table Exists:</strong> 
           <span class="{'success' if result['table_exists'] else 'error'}">
               {'✅ YES' if result['table_exists'] else '❌ NO'}
           </span>
        </p>
        
        <p><strong>Total Interventions:</strong> {result['interventions_count']}</p>
        
        <h2>Related Tables</h2>
        <ul>
            {"".join(f'<li>{table}: {"✅ EXISTS" if exists else "❌ MISSING"}</li>' 
                    for table, exists in result['tables'].items())}
        </ul>
        
        <h2>Sample Data</h2>
        <pre>{result['sample_data']}</pre>
        
        {f'<h2 class="error">Error:</h2><pre>{result["error"]}</pre>' if 'error' in result else ''}
        
        <div style="margin-top: 20px;">
            <a href="/interventions/">← Back to Interventions</a> | 
            <a href="/interventions/create-sample">Create Sample Interventions</a> |
            <a href="/interventions/test-template">Test Template</a>
        </div>
    </body>
    </html>
    """

@interventions_bp.route('/create-sample')
@login_required
def create_sample_interventions():
    """Create sample interventions for testing"""
    print("🎯 [DEBUG] Creating sample interventions")
    
    # Check if user has permission
    if current_user.role.name not in ['admin']:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # First check if interventions table exists
        cursor.execute("SHOW TABLES LIKE 'interventions'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ [DEBUG] Interventions table doesn't exist - creating it")
            # Create interventions table
            cursor.execute("""
                CREATE TABLE interventions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    client_id INT,
                    loan_id INT,
                    type VARCHAR(100),
                    description TEXT,
                    priority ENUM('low', 'medium', 'high'),
                    status ENUM('pending', 'in_progress', 'completed', 'cancelled'),
                    assigned_to INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id),
                    FOREIGN KEY (loan_id) REFERENCES loans(id),
                    FOREIGN KEY (assigned_to) REFERENCES users(id)
                )
            """)
            print("✅ [DEBUG] Created interventions table")

        # Create sample interventions
        sample_interventions = [
            (1, 1, 'payment_reminder', 'Payment overdue by 15 days - follow up required', 'high', 'pending', current_user.id),
            (2, 2, 'document_followup', 'Missing loan application documents', 'medium', 'in_progress', current_user.id),
            (1, 1, 'client_meeting', 'Schedule risk assessment meeting with client', 'high', 'pending', current_user.id)
        ]
        
        cursor.executemany("""
            INSERT INTO interventions (client_id, loan_id, type, description, priority, status, assigned_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, sample_interventions)
        
        conn.commit()
        print(f"✅ [DEBUG] Created {cursor.rowcount} sample interventions")
        
        return jsonify({
            'success': True, 
            'message': f'Created {cursor.rowcount} sample interventions',
            'created_table': not table_exists
        })

    except Exception as e:
        conn.rollback()
        print(f"❌ [DEBUG] Error creating interventions: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()

@interventions_bp.route('/test-template')
@login_required
def test_interventions_template():
    """Test if interventions template works"""
    print("🎯 [DEBUG] Interventions test template route called")
    
    # Test data
    test_interventions = [
        {
            'id': 1,
            'client_name': 'Test Client 1',
            'loan_id': 101,
            'type': 'payment_reminder',
            'description': 'Payment overdue by 15 days',
            'priority': 'high',
            'status': 'pending',
            'assigned_officer': 'Officer Smith',
            'created_at': '2025-11-06 09:00:00'
        },
        {
            'id': 2,
            'client_name': 'Test Client 2', 
            'loan_id': 102,
            'type': 'document_followup',
            'description': 'Missing loan documents',
            'priority': 'medium',
            'status': 'in_progress',
            'assigned_officer': 'Officer Johnson',
            'created_at': '2025-11-06 10:00:00'
        }
    ]
    
    print(f"🎨 [DEBUG] Sending {len(test_interventions)} test interventions to template")
    
    return render_template(
        'interventions.html',
        interventions=test_interventions,
        username=current_user.username
    )