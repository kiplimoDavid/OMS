
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Product, Order, User, RoleEnum
from functools import wraps

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != RoleEnum.ADMIN:
            flash('Admin access only.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    products = Product.query.all()
    orders = Order.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', products=products, orders=orders, users=users)
