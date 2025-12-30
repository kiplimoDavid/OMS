from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, abort
)
from flask_login import login_required, current_user
from app import db
from app.models import Customer, Order, OrderStatus
from app.decorators import roles_required
from app.forms import CustomerForm
from sqlalchemy import desc

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


# ================================
# Dashboard for individual customer
# ================================
@customers_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.name != 'CUSTOMER':
        abort(403)

    status = request.args.get('status')
    orders_query = Order.query.filter_by(user_id=current_user.id)

    if status:
        try:
            status_enum = OrderStatus[status.upper()]
            orders_query = orders_query.filter_by(status=status_enum)
        except KeyError:
            flash('Invalid order status filter.', 'warning')

    orders = orders_query.order_by(desc(Order.created_at)).all()
    return render_template('customer/dashboard.html', orders=orders, selected_status=status)


# ================================
# Admin/Staff view: list customers
# ================================
@customers_bp.route('/')
@login_required
@roles_required('ADMIN', 'STAFF')
def list_customers():
    customers = Customer.query.order_by(Customer.name.asc()).all()
    return render_template('customers/list.html', customers=customers)


# ================================
# View single customer details
# ================================
@customers_bp.route('/view/<int:customer_id>')
@login_required
@roles_required('ADMIN', 'STAFF')
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('customers/view.html', customer=customer)


# ================================
# Add new customer
# ================================
@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('ADMIN', 'STAFF')
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully.', 'success')
        return redirect(url_for('customers.list_customers'))

    return render_template('customers/form.html', form=form, title="Add Customer")


# ================================
# Edit existing customer
# ================================
@customers_bp.route('/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@roles_required('ADMIN', 'STAFF')
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        db.session.commit()
        flash('Customer updated successfully.', 'success')
        return redirect(url_for('customers.list_customers'))

    return render_template('customers/form.html', form=form, title="Edit Customer")


# ================================
# Delete single customer
# ================================
@customers_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
@roles_required('ADMIN', 'STAFF')
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('customers.list_customers'))


# ================================
# Bulk delete customers
# ================================
@customers_bp.route('/bulk-delete', methods=['POST'])
@login_required
@roles_required('ADMIN', 'STAFF')
def bulk_delete():
    customer_ids = request.form.get('customer_ids', '')
    ids = [int(id.strip()) for id in customer_ids.split(',') if id.strip().isdigit()]
    
    deleted = 0
    for customer_id in ids:
        customer = Customer.query.get(customer_id)
        if customer:
            db.session.delete(customer)
            deleted += 1
    db.session.commit()

    flash(f'{deleted} customer(s) deleted successfully.', 'success')
    return redirect(url_for('customers.list_customers'))

from app.models import PaymentMethod
from app.forms.payment_method_form import PaymentMethodForm
from flask_login import current_user




