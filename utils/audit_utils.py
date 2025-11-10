from datetime import datetime
from utils.db import get_db_connection

def log_action(user_id, username, action, module):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO audit_logs (user_id, username, action, module, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    timestamp = datetime.now()
    cursor.execute(query, (user_id, username, action, module, timestamp))
    conn.commit()
    cursor.close()
    conn.close()
