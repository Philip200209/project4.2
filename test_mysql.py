import MySQLdb

try:
    connection = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",  # change if you have a password
        db="crimap_db",
        port=3306
    )
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("MySQL connected! Tables:", tables)
    cursor.close()
    connection.close()
except Exception as e:
    print("MySQL connection failed:", e)
