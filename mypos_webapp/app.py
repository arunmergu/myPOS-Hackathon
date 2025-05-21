from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from models import db, User, Quotation, Transaction
from services.openai_service import generate_quotation
from services.mypos_service import request_myposdeposit, get_merchant_transaction_list, analyze_transactions
from forms import LoginForm, RegistrationForm, QuotationForm, PaymentForm
import os
from datetime import datetime
from config import Config
import json
import uuid
from datetime import datetime, timedelta
import random



app = Flask(__name__)
app.config.from_object(Config)


# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor for template variables
@app.context_processor
def utility_processor():
    return {'now': datetime.utcnow()}

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'consumer':
            return redirect(url_for('consumer_dashboard'))
        else:
            return redirect(url_for('merchant_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'consumer':
            return redirect(url_for('consumer_dashboard'))
        else:
            return redirect(url_for('merchant_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if user.role == 'consumer':
                return redirect(next_page or url_for('consumer_dashboard'))
            else:
                return redirect(next_page or url_for('merchant_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    # Pre-select role if provided in URL
    role = request.args.get('role')
    if role in ['consumer', 'merchant'] and request.method == 'GET':
        form.role.data = role
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/consumer/create_quotation', methods=['GET', 'POST'])
@login_required
def create_quotation():
    if current_user.role != 'consumer':
        return redirect(url_for('index'))
    
    form = QuotationForm()
    
    if form.validate_on_submit():
        # Get all merchants
        merchants = User.query.filter_by(role='merchant').all()
        
        if not merchants:
            flash('No merchants available in the system.', 'warning')
            return redirect(url_for('consumer_dashboard'))
        
        # Generate quotation using OpenAI (without budget)
        ai_generated_content = generate_quotation(
            product_type=form.product_type.data,
            description=form.description.data
        )
        
        # Create a unique request_id to group related quotations
        request_id = str(uuid.uuid4())
        
        # Create a quotation for each UNIQUE merchant
        created_count = 0
        merchant_ids_added = set()  # Keep track of merchants we've added
        
        for merchant in merchants:
            # Skip if we've already added this merchant (prevents duplicates)
            if merchant.id in merchant_ids_added:
                continue
                
            quotation = Quotation(
                request_id=request_id,  # Group related quotations
                title=form.title.data,
                product_type=form.product_type.data,
                description=form.description.data,
                budget=0,  # Set a default value
                ai_generated_content=ai_generated_content,
                consumer_id=current_user.id,
                merchant_id=merchant.id,
                status='pending'
            )
            
            db.session.add(quotation)
            merchant_ids_added.add(merchant.id)  # Mark this merchant as added
            created_count += 1
        
        db.session.commit()
        flash(f'Quotation request created and sent to {created_count} merchants! You will be notified when a merchant responds.', 'success')
        return redirect(url_for('consumer_dashboard'))
    
    return render_template('consumer/create_quotation.html', form=form)


@app.route('/consumer/view_quotation/<int:quotation_id>')
@login_required
def view_quotation(quotation_id):
    if current_user.role != 'consumer':
        return redirect(url_for('index'))
    
    quotation = Quotation.query.get_or_404(quotation_id)
    if quotation.consumer_id != current_user.id:
        flash('You are not authorized to view this quotation', 'danger')
        return redirect(url_for('consumer_dashboard'))
    
    # Group related quotations
    related_quotations = []
    
    if quotation.request_id:
        # Find all quotations with the same request_id
        related_quotations = Quotation.query.filter_by(
            request_id=quotation.request_id,
            consumer_id=current_user.id
        ).all()
    else:
        # Fallback to finding by title if no request_id
        related_quotations = Quotation.query.filter_by(
            title=quotation.title,
            consumer_id=current_user.id
        ).all()
    
    # Count of merchants who received this request
    merchant_count = len(related_quotations)
    
    # Count of merchants who have responded (non-pending status)
    responded_count = sum(1 for q in related_quotations if q.status != 'pending')
    
    # Get a list of quotations that have been responded to
    active_quotations = [q for q in related_quotations if q.status != 'pending']
    
    return render_template(
        'consumer/view_quotation.html', 
        quotation=quotation,
        merchant_count=merchant_count,
        responded_count=responded_count,
        active_quotations=active_quotations
    )

def get_consolidated_quotations_for_consumer(consumer_id):
    """
    Gets all quotations for a consumer and consolidates them by request_id.
    For each group, returns the most advanced quotation (non-pending if available).
    """
    # Get all quotations for this consumer
    all_quotations = Quotation.query.filter_by(consumer_id=consumer_id).all()
    
    # Group quotations by request_id (or title as fallback)
    grouped_quotations = {}
    
    for quotation in all_quotations:
        # Use request_id if available, otherwise use title
        group_key = quotation.request_id if hasattr(quotation, 'request_id') and quotation.request_id else quotation.title
        
        if group_key not in grouped_quotations:
            grouped_quotations[group_key] = []
            
        grouped_quotations[group_key].append(quotation)
    
    # For each group, prioritize non-pending quotations
    consolidated_quotations = []
    
    for _, quotations in grouped_quotations.items():
        # Sort quotations by status priority
        status_priority = {
            'completed': 1,
            'deposit_paid': 2,
            'deposit_requested': 3,
            'revised': 4,
            'pending': 5
        }
        
        sorted_quotations = sorted(quotations, key=lambda q: status_priority.get(q.status, 999))
        
        # Take the highest priority quotation (lowest number)
        best_quotation = sorted_quotations[0] if sorted_quotations else None
        
        if best_quotation:
            consolidated_quotations.append(best_quotation)
    
    return consolidated_quotations

from datetime import datetime, timedelta

@app.route('/consumer/dashboard')
@login_required
def consumer_dashboard():
    if current_user.role != 'consumer':
        return redirect(url_for('index'))
    
    # Get all quotations for this consumer (consolidated view)
    consolidated_quotations = get_consolidated_quotations_for_consumer(current_user.id)
    
    # Calculate last month date for statistics
    last_month = datetime.utcnow() - timedelta(days=30)
    
    # Mock recent activities
    recent_activities = []
    
    # Add some mock activities based on actual quotations
    for i, quotation in enumerate(sorted(consolidated_quotations, key=lambda x: x.updated_at, reverse=True)[:5]):
        days_ago = i + 1
        activity_date = datetime.utcnow() - timedelta(days=days_ago)
        
        if quotation.status == 'pending':
            recent_activities.append({
                'type': 'quotation_created',
                'title': f'You created quotation "{quotation.title}"',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'revised':
            recent_activities.append({
                'type': 'quotation_responded',
                'title': f'{quotation.merchant.username} responded to your quotation',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'deposit_requested':
            recent_activities.append({
                'type': 'payment_requested',
                'title': f'{quotation.merchant.username} requested a deposit payment',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'deposit_paid':
            recent_activities.append({
                'type': 'payment_made',
                'title': f'You paid a deposit for "{quotation.title}"',
                'time': f'{days_ago} days ago'
            })
    
    # Sort quotations by created_at (newest first)
    consolidated_quotations.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template(
        'consumer/dashboard.html', 
        quotations=consolidated_quotations,
        last_month=last_month,
        recent_activities=recent_activities
    )

@app.route('/merchant/dashboard')
@login_required
def merchant_dashboard():
    if current_user.role != 'merchant':
        return redirect(url_for('index'))
    
    # Get all quotations for this merchant
    quotations = Quotation.query.filter_by(merchant_id=current_user.id).all()
    
    # Calculate last month date for statistics
    last_month = datetime.utcnow() - timedelta(days=30)
    
    # Mock recent activities
    recent_activities = []
    
    # Add some mock activities based on actual quotations
    for i, quotation in enumerate(sorted(quotations, key=lambda x: x.updated_at, reverse=True)[:5]):
        days_ago = i + 1
        
        if quotation.status == 'pending':
            recent_activities.append({
                'type': 'quotation_received',
                'title': f'Received quotation request from {quotation.consumer.username}',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'revised':
            recent_activities.append({
                'type': 'quotation_sent',
                'title': f'You sent a quotation to {quotation.consumer.username}',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'deposit_requested':
            recent_activities.append({
                'type': 'payment_requested',
                'title': f'You requested a deposit from {quotation.consumer.username}',
                'time': f'{days_ago} days ago'
            })
        elif quotation.status == 'deposit_paid':
            recent_activities.append({
                'type': 'payment_received',
                'title': f'Received deposit payment from {quotation.consumer.username}',
                'time': f'{days_ago} days ago'
            })
    
    # Sort quotations by created_at (newest first)
    quotations.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template(
        'merchant/dashboard.html', 
        quotations=quotations,
        last_month=last_month,
        recent_activities=recent_activities
    )


@app.route('/merchant/sales_dashboard')
@login_required
def sales_dashboard():
    if current_user.role != 'merchant':
        return redirect(url_for('index'))
    
    account_number,transaction_list=get_merchant_transaction_list()
    insights = analyze_transactions(transaction_list)

    total_transactions=insights["total_transactions"]
    total_revenue=insights["total_revenue_eur"]
    avergae_transactions=insights["average_transaction_eur"] 
    # Simple mock data to ensure the template has what it needs
    sales_data = {
        "total_revenue": total_revenue,
        "total_transactions":total_transactions,
        "avergae_transactions":avergae_transactions,
        "monthly_change": 0.8
    }
    
    return render_template(
        'merchant/sales_dashboard.html',
        sales_data=sales_data,
        current_month="May 2025"
    )

def generate_merchant_sales_data(merchant_id):
    """Generate simulated sales data for the merchant dashboard"""
    # This would normally come from your database
    # For demo purposes, we're generating random data
    
    # Last 6 months of sales data
    months = ["Dec '24", "Jan '25", "Feb '25", "Mar '25", "Apr '25", "May '25"]
    
    # Generate random monthly revenue
    base_revenue = 15000  # Starting point
    actual_revenue = []
    for i in range(6):
        # Add some variability to each month
        variation = random.uniform(0.9, 1.3)
        # Positive trend over time
        trend_factor = 1 + (i * 0.05)
        month_revenue = round(base_revenue * variation * trend_factor)
        actual_revenue.append(month_revenue)
    
    # Generate projected revenue (slightly different from actual)
    projected_revenue = [round(rev * random.uniform(0.9, 1.1)) for rev in actual_revenue]
    
    # Transaction counts
    transactions = [round(rev / random.uniform(30, 50)) for rev in actual_revenue]
    
    # Average transaction values
    avg_values = [round(actual_revenue[i] / transactions[i], 2) if transactions[i] > 0 else 0 for i in range(6)]
    
    # Month-over-month growth
    growth = []
    for i in range(1, 6):
        if actual_revenue[i-1] > 0:
            monthly_growth = ((actual_revenue[i] - actual_revenue[i-1]) / actual_revenue[i-1]) * 100
            growth.append(round(monthly_growth, 1))
        else:
            growth.append(0)
    growth.insert(0, 0)  # No growth for first month
    
    # Top performing products/services
    top_products = [
        {"name": "Website Design", "revenue": 8500, "growth": 12.3},
        {"name": "Logo Design", "revenue": 6200, "growth": 5.7},
        {"name": "SEO Services", "revenue": 4800, "growth": -2.1},
        {"name": "Content Writing", "revenue": 3900, "growth": 8.5},
        {"name": "Social Media", "revenue": 2600, "growth": 15.2}
    ]
    
    return {
        "months": months,
        "actual_revenue": actual_revenue,
        "projected_revenue": projected_revenue,
        "transactions": transactions,
        "avg_values": avg_values,
        "growth": growth,
        "top_products": top_products,
        "total_revenue": sum(actual_revenue),
        "avg_monthly_revenue": round(sum(actual_revenue) / len(actual_revenue)),
        "total_transactions": sum(transactions),
        "current_month_revenue": actual_revenue[-1],
        "previous_month_revenue": actual_revenue[-2],
        "monthly_change": round(((actual_revenue[-1] - actual_revenue[-2]) / actual_revenue[-2]) * 100, 1)
    }

@app.route('/api/sales/insight', methods=['POST'])
@login_required
def api_sales_insight():
    if current_user.role != 'merchant':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.json
    question = data.get('question', '')
    
    # Get the sales data (in a real app, this would come from your database)
    sales_data = generate_merchant_sales_data(merchant_id=current_user.id)
    
    # Generate insight using OpenAI
    answer = generate_sales_insight(question, sales_data)
    
    return jsonify({'answer': answer})

@app.route('/consumer/quotations')
@login_required
def consumer_quotations():
    if current_user.role != 'consumer':
        return redirect(url_for('index'))
    
    # Get all quotations for this consumer (consolidated view)
    consolidated_quotations = get_consolidated_quotations_for_consumer(current_user.id)
    
    # Sort quotations by created_at (newest first)
    consolidated_quotations.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('consumer/quotations.html', quotations=consolidated_quotations)

@app.route('/merchant/quotations')
@login_required
def merchant_quotations():
    if current_user.role != 'merchant':
        return redirect(url_for('index'))
    
    # Get all quotations for this merchant
    quotations = Quotation.query.filter_by(merchant_id=current_user.id).all()
    
    # Sort quotations by created_at (newest first)
    quotations.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('merchant/quotations.html', quotations=quotations)


@app.route('/merchant/review_quotation/<int:quotation_id>', methods=['GET', 'POST'])
@login_required
def review_quotation(quotation_id):
    if current_user.role != 'merchant':
        return redirect(url_for('index'))
    
    quotation = Quotation.query.get_or_404(quotation_id)
    if quotation.merchant_id != current_user.id:
        flash('You are not authorized to review this quotation', 'danger')
        return redirect(url_for('merchant_dashboard'))
    
    form = PaymentForm()
    if form.validate_on_submit():
        quotation.revised_amount = form.amount.data
        quotation.payment_terms = form.payment_terms.data
        quotation.merchant_notes = form.notes.data
        
        # Get the services data from the form
        services_data = request.form.get('services_data', '[]')
        try:
            services = json.loads(services_data)
            
            # Create a new updated quotation content with the edited services
            introduction_part = quotation.ai_generated_content.split('|')[0] if '|' in quotation.ai_generated_content else "Updated Quotation:\n\n"
            
            # Build the updated content with the table
            updated_content = introduction_part + "\n\n"
            updated_content += "| Service/Item | Description | Estimated Cost |\n"
            updated_content += "| ------------ | ----------- | -------------- |\n"
            
            # Add each service row
            for service in services:
                updated_content += f"| {service['name']} | {service['description']} | €{service['cost']:.2f} |\n"
            
            # Add total row
            total = sum(service['cost'] for service in services)
            updated_content += f"| **Total** | | **€{total:.2f}** |\n\n"
            
            # Add a closing note if one exists in the original content
            if "timeline" in quotation.ai_generated_content.lower():
                # Try to preserve any timeline info from the original
                timeline_part = quotation.ai_generated_content.split("timeline")[1].split("\n\n")[0] if "timeline" in quotation.ai_generated_content.lower() else ""
                updated_content += f"\n\nTimeline: {timeline_part}\n\n"
            
            # Update the quotation content
            quotation.ai_generated_content = updated_content
        except Exception as e:
            app.logger.error(f"Error processing services data: {str(e)}")
            # If there's an error, still update the quotation but don't modify the content
        
        quotation.status = 'revised'
        db.session.commit()
        flash('Quotation reviewed and updated successfully!', 'success')
        return redirect(url_for('merchant_dashboard'))
    
    # Pre-fill form with existing data if available
    if quotation.revised_amount:
        form.amount.data = quotation.revised_amount
    else:
        form.amount.data = quotation.budget or 0
    
    if quotation.payment_terms:
        form.payment_terms.data = quotation.payment_terms
    
    if quotation.merchant_notes:
        form.notes.data = quotation.merchant_notes
    
    return render_template('merchant/review_quotation.html', quotation=quotation, form=form)

@app.route('/merchant/request_deposit/<int:quotation_id>', methods=['GET', 'POST'])
@login_required
def request_deposit(quotation_id):
    if current_user.role != 'merchant':
        return redirect(url_for('index'))
    
    quotation = Quotation.query.get_or_404(quotation_id)
    if quotation.merchant_id != current_user.id:
        flash('You are not authorized to request deposit for this quotation', 'danger')
        return redirect(url_for('merchant_dashboard'))
    
    # Check if quotation is revised, otherwise redirect
    if quotation.status != 'revised':
        flash('You must review the quotation before requesting a deposit', 'warning')
        return redirect(url_for('review_quotation', quotation_id=quotation.id))
    
    form = PaymentForm()
    if form.validate_on_submit():
        # Request deposit via MyPOS API
        response = request_myposdeposit(
            quotation.id,
            quotation.title,
            amount=form.amount.data,
            currency='EUR',
            customer_email=quotation.consumer.email
        )
        
        if response.get('success'):
            transaction = Transaction(
                quotation_id=quotation.id,
                amount=form.amount.data,
                transaction_id=response.get('transaction_id'),
                payment_url=response.get('payment_url'),
                status='pending'
            )
            
            quotation.status = 'deposit_requested'
            
            db.session.add(transaction)
            db.session.commit()
            
            flash('Deposit request sent to customer!', 'success')
            return redirect(url_for('merchant_dashboard'))
        else:
            flash(f"Error requesting deposit: {response.get('error')}", 'danger')
    
    # Pre-fill the form with calculated deposit amount (30% by default)
    if not form.amount.data and quotation.revised_amount:
        form.amount.data = round(quotation.revised_amount * 0.3, 2)  # 30% deposit by default, rounded to 2 decimal places
    
    return render_template('merchant/request_deposit.html', quotation=quotation, form=form)



# API endpoints
@app.route('/api/generate_quotation', methods=['POST'])
@login_required
def api_generate_quotation():
    data = request.json
    ai_content = generate_quotation(
        product_type=data.get('product_type'),
        description=data.get('description'),
        budget=data.get('budget')
    )
    return jsonify({'content': ai_content})

@app.route('/api/webhook/mypos', methods=['POST'])
def mypos_webhook():
    data = request.json
    transaction_id = data.get('transaction_id')
    status = data.get('status')
    
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if transaction:
        transaction.status = status
        if status == 'completed':
            quotation = Quotation.query.get(transaction.quotation_id)
            quotation.status = 'deposit_paid'
        
        db.session.commit()
    
    return jsonify({'status': 'success'})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)