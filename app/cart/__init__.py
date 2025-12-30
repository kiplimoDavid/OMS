from flask import Blueprint

bp = Blueprint('cart', __name__, url_prefix='/view_cart')

from app.cart import routes

from .routes import bp
