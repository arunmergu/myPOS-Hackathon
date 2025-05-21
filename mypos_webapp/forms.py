from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('consumer', 'Consumer'), ('merchant', 'Merchant')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class QuotationForm(FlaskForm):
    title = StringField('Quotation Title', validators=[DataRequired(), Length(max=100)])
    product_type = StringField('Product/Service Type', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[DataRequired()])
    #budget = FloatField('Budget (€)', validators=[DataRequired()])
    #merchant_id = SelectField('Select Merchant', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Generate Quotation')

class PaymentForm(FlaskForm):
    amount = FloatField('Amount (€)', validators=[DataRequired()])
    payment_terms = TextAreaField('Payment Terms')
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')