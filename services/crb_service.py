import logging
from datetime import datetime
from extensions import db
from models.crb_report import CRBReport

logger = logging.getLogger(__name__)

class CRBService:
    def __init__(self):
        self.api_key = "your_crb_api_key"
        
    def get_credit_report(self, national_id, phone_number, client_name):
        """Get credit report from CRB (simulated)"""
        try:
            # Simulate API call - replace with actual CRB API
            result = self._simulate_crb_response(national_id, phone_number)
        except Exception as e:
            logger.error(f"CRB API Error: {e}")
            result = None

        # Ensure we always return a dict; if simulation failed or returned None,
        # provide a safe fallback report so callers can safely call .get()
        if result is None:
            return {
                'success': False,
                'credit_score': 0,
                'active_loans': 0,
                'default_history': 0,
                'credit_utilization': 0.0,
                'payment_pattern': 'unknown',
                'blacklist_status': False,
                'days_arrears': 0,
                'credit_rating': 'Unknown',
                'crb_bureau': 'Simulated'
            }

        return result

    def _simulate_crb_response(self, national_id, phone_number):
        """Simulate realistic CRB response"""
        import random
        
        # Realistic simulation based on Kenyan context
        id_last_digit = int(national_id[-1]) if national_id else random.randint(0, 9)
        base_score = 300 + (id_last_digit * 55)
        credit_score = min(850, max(300, base_score + random.randint(-50, 50)))
        bureaus = ['Metropol', 'TransUnion', 'CRB Africa']
        bureau = random.choice(bureaus)

        # High/good credit profile
        if credit_score >= 700:
            return {
                'success': True,
                'credit_score': credit_score,
                'active_loans': random.randint(0, 2),
                'default_history': random.randint(0, 1),
                'credit_utilization': round(random.uniform(0.1, 0.4), 2),
                'payment_pattern': 'consistent',
                'blacklist_status': False,
                'days_arrears': 0,
                'credit_rating': 'Good',
                'recommendation': 'LOW_RISK',
                'crb_bureau': bureau
            }

        # Fair/average credit profile
        if 600 <= credit_score < 700:
            return {
                'success': True,
                'credit_score': credit_score,
                'active_loans': random.randint(1, 3),
                'default_history': random.randint(0, 2),
                'credit_utilization': round(random.uniform(0.3, 0.65), 2),
                'payment_pattern': random.choice(['irregular', 'mostly_on_time']),
                'blacklist_status': False,
                'days_arrears': random.choice([0, 0, 0, random.randint(5, 30)]),
                'credit_rating': 'Fair',
                'recommendation': 'MEDIUM_RISK',
                'crb_bureau': bureau
            }

        # Poor/very poor profile (possible blacklist)
        blacklist = True if (credit_score < 500 or id_last_digit in [0, 1]) else False
        return {
            'success': True,
            'credit_score': credit_score,
            'active_loans': random.randint(0, 4),
            'default_history': random.randint(1, 4),
            'credit_utilization': round(random.uniform(0.6, 0.95), 2),
            'payment_pattern': 'delayed',
            'blacklist_status': blacklist,
            'days_arrears': random.randint(15, 120),
            'credit_rating': 'Very Poor' if credit_score < 500 else 'Poor',
            'recommendation': 'REJECT' if blacklist else 'HIGH_RISK',
            'crb_bureau': bureau
        }