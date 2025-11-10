from flask import Blueprint, render_template
import mysql.connector

audit_bp = Blueprint('audit_bp', __name__)

def get_audit_logs():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="your_db_user",
            password="your_db_password",
            database="your_db_name"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user, action, module, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return logs
    except Exception as e:
        print(f"Error fetching audit logs: {e}")
        return []

@audit_bp.route('/audit/logs')
def view_audit_logs():
    logs = get_audit_logs()
    return render_template("audit_logs.html", audit_logs=logs)
