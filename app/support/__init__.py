from flask import Blueprint

bp = Blueprint('support', __name__)

from app.support import routes  # ensure this import is after bp is defined
