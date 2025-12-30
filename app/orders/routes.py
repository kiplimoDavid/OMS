from flask import (
    render_template, request, redirect, url_for,
    flash, abort, jsonify, Response
)
from flask_login import login_required, current_user
from app import db
from app.orders import bp
from app.models import (
    Order, OrderItem, Product, Customer,
    Payment, OrderNote, OrderStatus, PaymentStatus
)
from app.orders.forms import OrderForm
import csv
from io import StringIO
from datetime import datetime

# ───────────────────────────────────────────────
# Admin: List Orders (with optional filtering)
# ───────────────────────────────────────────────
@bp.route('/', endpoint='list_orders')
@login_required
def list_orders():
    if not (current_user.is_admin() or current_user.is_staff()):
        abort(403)

    status = request.args.get('status')
    orders_query = Order.query

    if status:
        try:
            status_enum = OrderStatus[status.upper()]
            orders_query = orders_query.filter_by(status=status_enum)
        except KeyError:
            flash("Invalid status filter.", "toast-warning")

    orders = orders_query.order_by(Order.order_date.desc()).all()
    total_revenue = sum(o.total_amount for o in orders)
    order_count = len(orders)
    avg_order_value = total_revenue / order_count if order_count else 0

    return render_template(
        'orders/list.html',
        orders=orders,
        status_filter=status,
        total_revenue=total_revenue,
        order_statuses=[s.name for s in OrderStatus],
        payment_statuses=[s.name for s in PaymentStatus],
        order_count=order_count,
        avg_order_value=avg_order_value
    )


# ───────────────────────────────────────────────
# Admin: Bulk Delete Orders
# ───────────────────────────────────────────────
@bp.route('/bulk-delete', methods=['POST'], endpoint='bulk_delete')
@login_required
def bulk_delete():
    if not current_user.is_admin():
        abort(403)
    data = request.get_json() or {}
    ids = data.get('ids', [])
    deleted = 0
    for oid in ids:
        o = Order.query.get(oid)
        if o:
            db.session.delete(o)
            deleted += 1
    db.session.commit()
    return jsonify({"message": f"{deleted} orders deleted."}), 200


# ───────────────────────────────────────────────
# Customer: View Their Orders
# ───────────────────────────────────────────────
@bp.route('/my-orders', endpoint='my_orders')
@login_required
def my_orders():
    if not current_user.is_customer():
        abort(403)
    cust = current_user.customer

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)

    query = Order.query.filter_by(customer_id=cust.id)
    if status:
        try:
            query = query.filter(Order.status == OrderStatus[status.upper()])
        except KeyError:
            flash("Invalid status filter.", "toast-warning")
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)

    orders = query.order_by(Order.order_date.desc()).paginate(page=page, per_page=5)

    return render_template('orders/my_orders.html', orders=orders)


# ───────────────────────────────────────────────
# Export Orders as CSV (Customer)
# ───────────────────────────────────────────────
@bp.route('/my-orders/export', endpoint='export_csv')
@login_required
def export_csv():
    if not current_user.is_customer():
        abort(403)
    cust = current_user.customer

    status = request.args.get('status', type=str)
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)

    query = Order.query.filter_by(customer_id=cust.id)
    if status:
        try:
            query = query.filter(Order.status == OrderStatus[status.upper()])
        except KeyError:
            flash("Invalid status for export.", "toast-warning")
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)

    orders = query.order_by(Order.order_date.desc()).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Order #', 'Date', 'Status', 'Total', 'Payment'])
    for o in orders:
        cw.writerow([
            o.order_number,
            o.order_date.strftime('%Y-%m-%d'),
            o.status.value,
            f"{o.total_amount:.2f}",
            o.payment_status.value if getattr(o, 'payment_status', None) else ''
        ])

    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=my_orders.csv"}
    )


# ───────────────────────────────────────────────
# View Order Details (Admin/Customer)
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>', endpoint='view_order')
@login_required
def view_order(order_id):
    o = Order.query.get_or_404(order_id)
    if current_user.is_customer():
        if not o.customer or o.customer.user_id != current_user.id:
            abort(403)

    total_paid = sum(p.amount for p in o.payments)
    balance_due = o.total_amount - total_paid

    return render_template('orders/view.html', order=o, total_paid=total_paid, balance_due=balance_due)


# ───────────────────────────────────────────────
# Download Invoice
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/invoice', endpoint='invoice')
@login_required
def invoice(order_id):
    o = Order.query.get_or_404(order_id)
    if current_user.is_admin() or (current_user.is_customer() and o.customer and o.customer.user_id == current_user.id):
        return render_template('orders/invoice.html', order=o)
    abort(403)


# ───────────────────────────────────────────────
# Cancel Order (Customer or Staff/Admin)
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/cancel', methods=['POST'], endpoint='cancel_order')
@login_required
def cancel_order(order_id):
    o = Order.query.get_or_404(order_id)

    if current_user.is_customer():
        if not o.customer or o.customer.user_id != current_user.id:
            abort(403)

    if o.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
        flash("Cannot cancel this order.", "toast-warning")
        return redirect(url_for('orders.view_order', order_id=o.id))

    o.status = OrderStatus.CANCELLED
    db.session.commit()
    flash(f"Order #{o.order_number} cancelled.", "toast-success")
    return redirect(url_for('orders.view_order', order_id=o.id))


# ───────────────────────────────────────────────
# Track Shipment
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/track', endpoint='track_order')
@login_required
def track_order(order_id):
    o = Order.query.get_or_404(order_id)

    if current_user.is_customer():
        if not o.customer or o.customer.user_id != current_user.id:
            abort(403)

    if o.status != OrderStatus.SHIPPED:
        flash("Order not yet shipped.", "toast-info")
        return redirect(url_for('orders.view_order', order_id=o.id))

    return render_template('orders/track.html', order=o)


# ───────────────────────────────────────────────
# Payment Submission
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/add-payment', methods=['POST'], endpoint='add_payment')
@login_required
def add_payment(order_id):
    o = Order.query.get_or_404(order_id)

    if current_user.is_customer():
        if not o.customer or o.customer.user_id != current_user.id:
            abort(403)

    try:
        amt = float(request.form.get('amount', 0))
    except ValueError:
        flash("Invalid amount.", "toast-danger")
        return redirect(url_for('orders.view_order', order_id=order_id))

    balance = o.total_amount - sum(p.amount for p in o.payments)
    if amt <= 0:
        flash("Amount must be positive.", "toast-warning")
    elif amt > balance:
        flash(f"Payment exceeds balance (Ksh {balance:.2f}).", "toast-danger")
    else:
        db.session.add(Payment(order_id=o.id, amount=amt))
        db.session.commit()
        flash(f"Payment of Ksh {amt:.2f} recorded.", "toast-success")

    return redirect(url_for('orders.view_order', order_id=order_id))


# ───────────────────────────────────────────────
# Add Order Note
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/add-note', methods=['POST'], endpoint='add_note')
@login_required
def add_order_note(order_id):
    o = Order.query.get_or_404(order_id)
    if not current_user.is_customer() or (o.customer and o.customer.user_id != current_user.id):
        abort(403)

    text = request.form.get('note', '').strip()
    if not text:
        flash("Note cannot be empty.", "toast-danger")
        return redirect(url_for('orders.view_order', order_id=order_id))

    db.session.add(OrderNote(order_id=o.id, user_id=current_user.id, content=text))
    db.session.commit()
    flash("Note added.", "toast-success")
    return redirect(url_for('orders.view_order', order_id=order_id))


# ───────────────────────────────────────────────
# Leave Review (Customers only)
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/leave-review', methods=['POST'], endpoint='leave_review')
@login_required
def leave_review(order_id):
    o = Order.query.get_or_404(order_id)

    if not current_user.is_customer() or o.customer.user_id != current_user.id:
        abort(403)
    if o.status != OrderStatus.DELIVERED:
        flash("Cannot review until delivered.", "toast-warning")
        return redirect(url_for('orders.view_order', order_id=o.id))

    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    if not rating or not comment:
        flash("Rating and comment are required.", "toast-danger")
        return redirect(url_for('orders.view_order', order_id=o.id))

    from app.models import Review
    review = Review(order_id=o.id, user_id=current_user.id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash("Review submitted—thank you!", "toast-success")
    return redirect(url_for('orders.view_order', order_id=order_id))


# ───────────────────────────────────────────────
# Admin/Staff: Add Order
# ───────────────────────────────────────────────
@bp.route('/add', methods=['GET', 'POST'], endpoint='add_order')
@login_required
def add_order():
    if not (current_user.is_admin() or current_user.is_staff()):
        abort(403)
    form = OrderForm()
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by('name')]
    if form.validate_on_submit():
        o = Order(customer_id=form.customer_id.data, status=OrderStatus.PENDING, total_amount=0)
        db.session.add(o)
        db.session.flush()
        total = 0
        for item in form.items:
            prod = Product.query.get(item.product_id.data)
            if prod:
                qty = item.quantity.data
                oi = OrderItem(order_id=o.id, product_id=prod.id, quantity=qty, unit_price=prod.price)
                db.session.add(oi)
                total += prod.price * qty
                prod.stock_quantity -= qty
        o.total_amount = total
        db.session.commit()
        flash('Order created successfully!', 'toast-success')
        return redirect(url_for('orders.view_order', order_id=o.id))
    return render_template('orders/add.html', form=form)


# ───────────────────────────────────────────────
# Admin/Staff: Create Order for Specific Customer
# ───────────────────────────────────────────────
@bp.route('/create/<int:customer_id>', methods=['GET', 'POST'], endpoint='create_order')
@login_required
def create_order(customer_id):
    if not (current_user.is_admin() or current_user.is_staff()):
        abort(403)
    cust = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        o = Order(customer_id=cust.id, status=OrderStatus.PENDING)
        db.session.add(o)
        db.session.commit()
        flash('Order created successfully!', 'toast-success')
        return redirect(url_for('customers.view_customer', customer_id=cust.id))
    return render_template('orders/create.html', customer=cust)


# ───────────────────────────────────────────────
# Admin/Staff: Update Order Status (Guarded by full payment for Delivered)
# ───────────────────────────────────────────────
@bp.route('/<int:order_id>/update-status', methods=['POST'], endpoint='update_status')
@login_required
def update_order_status(order_id):
    if not (current_user.is_admin() or current_user.is_staff()):
        abort(403)
    o = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    try:
        status_enum = OrderStatus[status.upper()]
    except (KeyError, TypeError):
        flash("Invalid status.", 'toast-danger')
        return redirect(url_for('orders.view_order', order_id=o.id))

    if status_enum == OrderStatus.DELIVERED:
        total_paid = sum(p.amount for p in o.payments)
        if total_paid < o.total_amount:
            flash("Cannot mark as delivered until fully paid.", "toast-warning")
            return redirect(url_for('orders.view_order', order_id=o.id))

    o.status = status_enum
    db.session.commit()
    flash('Order status updated.', 'toast-success')
    return redirect(url_for('orders.view_order', order_id=o.id))


# ───────────────────────────────────────────────
# Placeholder: Edit Order (Not implemented)
# ───────────────────────────────────────────────
@bp.route('/edit/<int:order_id>', methods=['GET', 'POST'], endpoint='edit_order')
@login_required
def edit_order(order_id):
    abort(501)  # Not Implemented Yet


# ───────────────────────────────────────────────
# Customer: Reorder Items
# ───────────────────────────────────────────────
@bp.route('/orders/<int:order_id>/reorder', methods=['GET'])
@login_required
def reorder(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer.user_id != current_user.id:
        abort(403)
    for item in order.items:
        from app.cart import add_to_cart
        add_to_cart(item.product_id, item.quantity)
    flash('Items from this order were added to your cart.', 'toast-success')
    return redirect(url_for('cart.view_cart'))


#------/mark_delivered------
@bp.route('/mark-delivered/<int:order_id>', methods=['POST'])
@login_required
def mark_delivered(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    if order.status == 'CANCELLED':
        return jsonify({'success': False, 'message': 'Cannot mark cancelled order as delivered'}), 400

    if order.payment_status != 'PAID':
        return jsonify({'success': False, 'message': 'Order is not fully paid'}), 400

    order.status = 'DELIVERED'
    db.session.commit()

    return jsonify({'success': True, 'message': 'Order marked as delivered successfully'})
