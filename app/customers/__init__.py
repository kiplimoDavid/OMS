from flask import Blueprint

# Create the blueprint instance
bp = Blueprint('customers', __name__)

# Import routes at the bottom to avoid circular imports
from app.customers import routes