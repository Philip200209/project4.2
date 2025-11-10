from extensions import db

class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer)  # REMOVE foreign key
    permission_id = db.Column(db.Integer)  # REMOVE foreign key
    
    # REMOVE these relationships
    # role = db.relationship('Role', backref=db.backref('role_permissions', lazy=True))
    # permission = db.relationship('Permission', backref=db.backref('permission_roles', lazy=True))
    
    def __repr__(self):
        return f'<RolePermission {self.role_id}-{self.permission_id}>'