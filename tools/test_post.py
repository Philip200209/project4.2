import os, sys
# Ensure project root (python/) is on sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app

print('Starting test client POST to /loans/apply')
with app.test_client() as client:
    with app.app_context():
        data = {
            'amount': '50000',
            'term': '12',
            'purpose': 'Personal',
            'employment_status': 'Employed',
            'monthly_income': '50000',
            'credit_history': '0',
            'client_phone': '+254712345678',
            'national_id': '12345678',
            'client_name': 'Unit Test',
            'existing_debt': '0',
            'terms_accepted': 'on'
        }
        # Set a logged-in user in the session (flask-login stores id under '_user_id')
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True

        resp = client.post('/loans/apply', data=data, follow_redirects=True)
        print('Response status:', resp.status_code)
        print(resp.get_data(as_text=True)[:1000])
print('Done')
