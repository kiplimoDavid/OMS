from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes  # ensure this import is after bp is defined
