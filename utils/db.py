import mysql.connector
from flask import current_app

def get_db_connection():
    """
    Establish and return a connection to crimap_db database
    """
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',           # XAMPP default username
            password='',           # XAMPP default password (empty)
            database='crimap_db',  # Your database name
            port=3306,             # XAMPP default MySQL port
            autocommit=True
        )
        print("✅ Database connection to crimap_db successful")
        return conn
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        return None