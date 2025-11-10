from flask import Blueprint
from werkzeug.security import generate_password_hash
from database import get_db_connection

seed_bp = Blueprint('seed_bp', __name__)

@seed_bp.route('/seed-users')
def seed_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin"
        },
        {
            "username": "user",
            "email": "user@example.com",
            "password": "user123",
            "role": "user"
        }
    ]

    try:
        for u in users:
            cursor.execute("SELECT * FROM users WHERE username = %s", (u["username"],))
            if cursor.fetchone():
                continue

            hashed_pw = generate_password_hash(u["password"])
            cursor.execute("""
                INSERT INTO users (username, email, password, role)
                VALUES (%s, %s, %s, %s)
            """, (u["username"], u["email"], hashed_pw, u["role"]))

        conn.commit()
        return "✅ Admin and user accounts seeded successfully."

    except Exception as e:
        print("Seeding error:", e)
        return "❌ Failed to seed users."

    finally:
        cursor.close()
        conn.close()
