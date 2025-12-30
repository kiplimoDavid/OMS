
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import Product
from flask_login import login_required

product_bp = Blueprint('product', __name__, url_prefix='/product')

@product_bp.route('/<int:product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product/detail.html', product=product)
