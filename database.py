import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",      # your MySQL root password
        database="crimap_db"
    )
