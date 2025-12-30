from flask import render_template, request, jsonify, url_for, session
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, cast, String

from app.main import bp
from app.models import Order, Product, Customer

# ─────────────────────────────────────────────────────────────────────────────
# 🏠 HOME ROUTE: Public landing page (no login required)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

# ─────────────────────────────────────────────────────────────────────────────
# 🧭 INDEX / DASHBOARD ROUTE: Requires login; shows stats
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/index')
@login_required
def index():
    # Admin/Staff: See full system-wide stats
    if current_user.is_admin() or current_user.is_staff():
        total_orders = Order.query.count()
        total_products = Product.query.count()
        total_customers = Customer.query.count()

        recent_orders = (
            Order.query
            .order_by(Order.order_date.desc())
            .limit(10)
            .all()
        )
    else:
        # Customers: See only their own recent orders
        total_orders = None
        total_products = Product.query.count()
        total_customers = None

        recent_orders = (
            Order.query
            .filter_by(customer_id=current_user.id)
            .order_by(Order.order_date.desc())
            .limit(5)
            .all()
        )

    return render_template(
        'index.html',
        total_orders=total_orders,
        total_products=total_products,
        total_customers=total_customers,
        recent_orders=recent_orders
    )

# ─────────────────────────────────────────────────────────────────────────────
# 🔒 AUTH DEBUGGING ROUTE: View session/debug info (dev use only)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/test-auth')
def test_auth():
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user_id': current_user.get_id() if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'session': dict(session)
    })

# ─────────────────────────────────────────────────────────────────────────────
# 🧮 DASHBOARD VIEW (unused route)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('main/dashboard.html')

# ─────────────────────────────────────────────────────────────────────────────
# 🔍 FULL SEARCH RESULTS PAGE (products and orders)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    products = []
    orders = []

    if query:
        # Product matches (available to all)
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            )
        ).all()

        # Order matches (depends on user role)
        if current_user.is_authenticated:
            if current_user.is_admin() or current_user.is_staff():
                orders = Order.query.join(Customer).filter(
                    or_(
                        cast(Order.id, String).ilike(f'%{query}%'),
                        Customer.name.ilike(f'%{query}%')
                    )
                ).all()
            elif current_user.is_customer():
                orders = Order.query.filter(
                    Order.customer_id == current_user.id,
                    cast(Order.id, String).ilike(f'%{query}%')
                ).all()

    return render_template(
        'search_results.html',
        query=query,
        products=products,
        orders=orders
    )

# ─────────────────────────────────────────────────────────────────────────────
# ⚡ AJAX SEARCH SUGGESTIONS (no login required)
# ─────────────────────────────────────────────────────────────────────────────
@bp.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip().lower()
    suggestions = []

    if query:
        # Product matches (always public)
        product_matches = Product.query.filter(
            Product.name.ilike(f"%{query}%")
        ).limit(5).all()

        for product in product_matches:
            suggestions.append({
                'type': 'Product',
                'name': product.name,
                'url': url_for('products.view_product', product_id=product.id)
            })

        # Order matches (only if user is authenticated)
        if current_user.is_authenticated:
            if current_user.is_admin() or current_user.is_staff():
                order_matches = Order.query.join(Customer).filter(
                    or_(
                        cast(Order.id, String).ilike(f"%{query}%"),
                        Customer.name.ilike(f"%{query}%")
                    )
                ).limit(5).all()
            elif current_user.is_customer():
                order_matches = Order.query.filter(
                    Order.customer_id == current_user.id,
                    cast(Order.id, String).ilike(f"%{query}%")
                ).limit(5).all()
            else:
                order_matches = []
        else:
            order_matches = []  # Not logged in: no order suggestions

        for order in order_matches:
            suggestions.append({
                'type': 'Order',
                'name': f"Order #{order.id} - {order.customer.name}",
                'url': url_for('orders.view_order', order_id=order.id)
            })

    return jsonify(suggestions)

