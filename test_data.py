# test_data.py
from models import db, Client, LoanApplication, User
from datetime import datetime, timedelta

def create_test_email_data():
    """Create sample data for testing email functionality"""
    try:
        print("📝 Creating test data for email testing...")
        
        # Create test clients with emails
        test_clients = [
            {
                'name': 'John Kamau', 
                'email': 'test1@example.com',
                'income': 50000,
                'credit_score': 650
            },
            {
                'name': 'Mary Wanjiku', 
                'email': 'test2@example.com', 
                'income': 75000,
                'credit_score': 720
            },
            {
                'name': 'Peter Ochieng',
                'email': 'test3@example.com',
                'income': 30000, 
                'credit_score': 580
            }
        ]
        
        # Create or update test clients
        for client_data in test_clients:
            client = Client.query.filter_by(email=client_data['email']).first()
            if not client:
                client = Client(**client_data)
                db.session.add(client)
                print(f"✅ Created test client: {client_data['name']}")
            else:
                # Update existing client
                for key, value in client_data.items():
                    setattr(client, key, value)
                print(f"✅ Updated test client: {client_data['name']}")
        
        db.session.commit()
        
        # Create test loan applications
        clients = Client.query.all()
        if clients:
            test_loans = [
                {
                    'client_id': clients[0].id,
                    'amount': 50000,
                    'term': 12,
                    'status': 'active',
                    'risk_score': 0.85,  # High risk
                    'next_due_date': datetime.now() + timedelta(days=3)  # Due soon
                },
                {
                    'client_id': clients[1].id, 
                    'amount': 100000,
                    'term': 24,
                    'status': 'active',
                    'risk_score': 0.45,  # Low risk
                    'next_due_date': datetime.now() + timedelta(days=10)
                },
                {
                    'client_id': clients[2].id,
                    'amount': 25000,
                    'term': 6, 
                    'status': 'pending',
                    'risk_score': 0.75,  # Medium-high risk
                    'next_due_date': None
                }
            ]
            
            for loan_data in test_loans:
                # Check if loan already exists for this client
                existing_loan = LoanApplication.query.filter_by(
                    client_id=loan_data['client_id']
                ).first()
                
                if not existing_loan:
                    loan = LoanApplication(**loan_data)
                    db.session.add(loan)
                    client_name = Client.query.get(loan_data['client_id']).name
                    print(f"✅ Created test loan for: {client_name}")
            
            db.session.commit()
        
        print("🎉 Test data created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.session.rollback()
        return False