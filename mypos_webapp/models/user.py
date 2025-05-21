from models import db, UserMixin, generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'consumer' or 'merchant'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    consumer_quotations = db.relationship('Quotation', backref='consumer', lazy=True, foreign_keys='Quotation.consumer_id')
    merchant_quotations = db.relationship('Quotation', backref='merchant', lazy=True, foreign_keys='Quotation.merchant_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"