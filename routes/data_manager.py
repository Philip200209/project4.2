from database import get_db_connection

def log_action(user_id, username, action, module):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (user_id, username, action, module)
        VALUES (%s, %s, %s, %s)
    """, (user_id, username, action, module))
    conn.commit()
    cursor.close()
    conn.close()
