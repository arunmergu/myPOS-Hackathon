from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Import models to make them available through the models package
from models.user import User
from models.quotation import Quotation
from models.transaction import Transaction