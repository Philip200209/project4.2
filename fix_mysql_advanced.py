# fix_mysql_advanced.py
import sys
sys.path.append('.')
from app import app, db
from models import User, Loan, Client
from sqlalchemy import inspect, text

print('🔧 FIXING MYSQL DATABASE (ADVANCED)...')

with app.app_context():
    try:
        # First, let's see what tables actually exist
        inspector = inspect(db.engine)
        current_tables = inspector.get_table_names()
        print(f'📊 Current tables: {current_tables}')
        
        # Check loans table structure
        if 'loans' in current_tables:
            loans_columns = [col['name'] for col in inspector.get_columns('loans')]
            print(f'📋 Loans table columns: {loans_columns}')
            
            # Check if client_name column exists
            if 'client_name' not in loans_columns:
                print('⚠️ Loans table missing client_name column - need to recreate')
                
                # Disable foreign key checks
                db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
                print('🔓 Foreign key checks disabled')
                
                # Drop all tables
                db.drop_all()
                print('✅ Tables dropped')
                
                # Re-enable foreign key checks
                db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
                print('🔒 Foreign key checks enabled')
                
                # Create all tables with correct structure
                db.create_all()
                print('✅ Tables recreated with correct structure')
            else:
                print('✅ Loans table has correct structure')
        else:
            print('❌ Loans table does not exist - creating...')
            db.create_all()
            print('✅ Tables created')
        
        # Create sample data
        if User.query.count() == 0:
            users = [
                User(username='admin', email='admin@crimap.com', role='admin'),
                User(username='loan officer', email='officer@crimap.com', role='officer'),
                User(username='user', email='user@crimap.com', role='client'),
            ]
            users[0].set_password('admin123')
            users[1].set_password('admin123')
            users[2].set_password('user123')
            
            for user in users:
                db.session.add(user)
            db.session.commit()
            print('✅ Users created')
        
        if Loan.query.count() == 0:
            loans = [
                Loan(client_name='John Kamau', client_email='john@example.com', client_phone='+254712345678', 
                     amount=50000, term=12, purpose='Business expansion', status='pending', risk_score=65.5),
                Loan(client_name='Mary Wanjiku', client_email='mary@example.com', client_phone='+254723456789', 
                     amount=25000, term=6, purpose='Education fees', status='approved', risk_score=82.3),
                Loan(client_name='David Ochieng', client_email='david@example.com', client_phone='+254734567890', 
                     amount=100000, term=24, purpose='Home renovation', status='rejected', risk_score=28.7),
            ]
            
            for loan in loans:
                db.session.add(loan)
            db.session.commit()
            print('✅ Loans created')
        
        # Final verification
        user_count = User.query.count()
        loan_count = Loan.query.count()
        print(f'✅ FINAL CHECK: {user_count} users, {loan_count} loans')
        print('🎉 MySQL database fixed and ready!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        # Make sure to re-enable foreign key checks if there was an error
        try:
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
            print('🔒 Foreign key checks re-enabled')
        except:
            pass
