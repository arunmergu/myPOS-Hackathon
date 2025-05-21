from models import db, datetime

class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(50), nullable=True)  # Group related quotations
    title = db.Column(db.String(100), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float, nullable=True)
    ai_generated_content = db.Column(db.Text, nullable=True)
    revised_amount = db.Column(db.Float, nullable=True)
    payment_terms = db.Column(db.Text, nullable=True)
    merchant_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, revised, deposit_requested, deposit_paid, completed
    consumer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='quotation', lazy=True)
    
    def __repr__(self):
        return f"Quotation('{self.title}', '{self.status}', '€{self.budget}')"