from flask import Blueprint

# Create the main blueprint
bp = Blueprint('main', __name__)

# Import routes at the bottom to avoid circular imports
from app.main import routes