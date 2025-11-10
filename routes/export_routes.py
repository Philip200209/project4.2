from flask import Blueprint, send_file
from flask_login import login_required
import io

export_bp = Blueprint('export_bp', __name__, url_prefix='/export')

@export_bp.route('/summary/<int:loan_id>')
@login_required
def export_summary(loan_id):
    # Placeholder logic — replace with real export logic
    dummy_csv = "Loan ID,Amount,Status\n{},10000,Approved".format(loan_id)
    return send_file(
        io.BytesIO(dummy_csv.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'loan_{loan_id}_summary.csv'
    )
