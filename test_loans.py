# test_loans.py
import sys
sys.path.append('.')
from app import app, db
from models import Loan

print('🧪 TESTING LOANS ACCESS...')

with app.app_context():
    try:
        loans = Loan.query.all()
        print(f'✅ Found {len(loans)} loans')
        
        for loan in loans:
            print(f'📋 Loan {loan.id}: {loan.client_name} - KSh {loan.amount:,} - {loan.status} - Risk: {loan.risk_score}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
