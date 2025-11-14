# models/__init__.py
from .user import User
from .client import Client
from .loan import Loan
from .intervention import Intervention
from .repayment import Repayment
from .role import Role
from .permission import Permission
from .role_permission import RolePermission
from .crb_report import CRBReport  # ADD THIS LINE

# Export only models, NOT db
__all__ = [
    'User', 
    'Client', 
    'Loan', 
    'Intervention',
    'Repayment', 
    'Role', 
    'Permission', 
    'RolePermission',
    'CRBReport'  # ADD THIS LINE
]