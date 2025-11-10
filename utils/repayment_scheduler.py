import mysql.connector
from datetime import datetime, timedelta

def generate_repayment_schedule(loan_id, client_id, principal, term_months, start_date):
    """
    Auto-generates equal monthly repayments for a loan and inserts them into the repayments table.
    """
    # Calculate monthly installment (simple division — no interest for now)
    monthly_amount = round(principal / term_months, 2)

    # Connect to MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='your_db_user',
        password='your_db_password',
        database='crimap_db'
    )
    cursor = conn.cursor()

    for i in range(term_months):
        due_date = start_date + timedelta(days=30 * i)
        cursor.execute("""
            INSERT INTO repayments (loan_id, client_id, due_date, amount, status)
            VALUES (%s, %s, %s, %s, 'pending')
        """, (loan_id, client_id, due_date.strftime('%Y-%m-%d'), monthly_amount))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Repayment schedule created for loan {loan_id} ({term_months} months)")

# Example usage
if __name__ == "__main__":
    generate_repayment_schedule(
        loan_id=3,
        client_id=101,
        principal=10000,
        term_months=5,
        start_date=datetime.strptime("2025-11-01", "%Y-%m-%d")
    )
