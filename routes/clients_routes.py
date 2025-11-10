from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth_utils import login_required
from database import get_db_connection

clients_bp = Blueprint('clients_bp', __name__)

# View all clients
@clients_bp.route('/clients', methods=['GET'])
@login_required
def view_clients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients ORDER BY id DESC")
    clients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_clients.html', clients=clients)

# Add new client
@clients_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        income = request.form['income']
        credit_score = request.form['credit_score']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (name, phone, email, income, credit_score)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, phone, email, income, credit_score))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Client added successfully.', 'success')
        return redirect(url_for('clients_bp.view_clients'))

    return render_template('add_client.html')

# Edit existing client
@clients_bp.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        income = request.form['income']
        credit_score = request.form['credit_score']

        cursor.execute("""
            UPDATE clients
            SET name = %s, phone = %s, email = %s, income = %s, credit_score = %s
            WHERE id = %s
        """, (name, phone, email, income, credit_score, client_id))
        conn.commit()
        flash('Client updated successfully.', 'success')
        return redirect(url_for('clients_bp.view_clients'))

    cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
    client = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_client.html', client=client)
