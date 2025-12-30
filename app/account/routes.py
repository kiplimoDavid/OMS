from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import Order, Payment, db
from datetime import datetime

bp = Blueprint('account', __name__, url_prefix='/account')

# ====================
# Dashboard
# ====================
@bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_customer():
        flash("Access restricted to customers", "toast-warning")
        return redirect(url_for('main.dashboard'))

    # Fetch recent orders summary
    orders = (Order.query
              .filter_by(customer_id=current_user.customer.id)
              .order_by(Order.order_date.desc())
              .limit(5)
              .all())

    upcoming = [o for o in orders if o.status.name in ['PENDING', 'PROCESSING', 'SHIPPED']]
    recent = orders

    return render_template('account/dashboard.html',
                           upcoming=upcoming,
                           recent=recent)

# ====================
# Clear Balance
# ====================
@bp.route('/<int:order_id>/clear-balance', methods=['POST'], endpoint='clear_balance')
@login_required
def clear_balance(order_id):
    order = Order.query.get_or_404(order_id)

    if not current_user.is_customer() or order.customer.user_id != current_user.id:
        abort(403)

    # Mark as fully paid
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_date=datetime.utcnow(),
        method="MANUAL",
        transaction_id=f"MANUAL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    db.session.add(payment)

    order.payment_status = 'PAID'
    order.status = 'PROCESSING'  # Or SHIPPED/DELIVERED based on your flow
    db.session.commit()

    flash("Balance cleared successfully.", "toast-success")
    return redirect(url_for('orders.view_order', order_id=order.id))

# ====================
# Make Payment
# ====================
@bp.route('/order/<int:order_id>/make-payment', methods=['POST'])
@login_required
def make_payment(order_id):
    order = Order.query.get_or_404(order_id)

    if current_user.role.name != 'CUSTOMER' or order.customer.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('orders.view_order', order_id=order_id))

    payment_method = request.form.get('payment_method')

    if not payment_method:
        flash("Please select a payment method.", "warning")
        return redirect(url_for('orders.view_order', order_id=order_id))

    # Simulate payment
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_date=datetime.utcnow(),
        method=payment_method,
        transaction_id=f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
    db.session.add(payment)

    # Update order
    order.payment_status = 'PAID'
    order.status = 'PROCESSING'
    order.payment_method = payment_method
    order.transaction_id = payment.transaction_id
    db.session.commit()

    flash("Payment received successfully.", "success")
    return redirect(url_for('orders.view_order', order_id=order_id))
