# app/customers/routes.py

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Customer, Order, ShippingAddress
from app.customers import bp
from app.forms.customer_form import CustomerForm

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class BillingAddressForm(FlaskForm):
    recipient_name = StringField('Recipient Name', validators=[DataRequired(), Length(max=100)])
    street = StringField('Street Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State/Province', validators=[Length(max=50)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=100)], default='Kenya')
    phone = StringField('Phone Number', validators=[Length(max=20)])
    is_default_billing = BooleanField('Set as default billing address')
    submit = SubmitField('Add Billing Address')
    is_default = BooleanField('Set as default billing address')
    zip_code = StringField('Zip Code', validators=[Length(max=20)])




@bp.route('/')
@login_required
def list_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)

@bp.route('/<int:customer_id>')
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc()).all()
    totals = [order.total_amount for order in orders if order.total_amount]
    total_order_value = sum(totals)
    avg_order_value = total_order_value / len(totals) if totals else 0.0

    return render_template(
        'customers/view.html',
        customer=customer,
        orders=orders,
        total_order_value=total_order_value,
        avg_order_value=avg_order_value
    )

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            company=form.company.data,
            tax_id=form.tax_id.data,
            notes=form.notes.data
        )
        db.session.add(customer)
        db.session.flush()  # Get customer.id before committing

        if form.default_shipping_address.data:
            shipping = ShippingAddress(
                customer_id=customer.id,
                address=form.default_shipping_address.data,
                is_default_shipping=True
            )
            db.session.add(shipping)

        if form.default_billing_address.data:
            billing = ShippingAddress(
                customer_id=customer.id,
                address=form.default_billing_address.data,
                is_default_billing=True
            )
            db.session.add(billing)

        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers.list_customers'))

    return render_template('customers/add.html', form=form)

@bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.company = form.company.data
        customer.tax_id = form.tax_id.data
        customer.notes = form.notes.data

        # Optionally update addresses here (not implemented)

        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers.view_customer', customer_id=customer.id))

    return render_template('customers/edit.html', form=form, customer=customer)

@bp.route('/<int:customer_id>/delete', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('customers.list_customers'))

@bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    ids = request.form.getlist('selected_ids[]')
    if ids:
        customers = Customer.query.filter(Customer.id.in_(ids)).all()
        for customer in customers:
            db.session.delete(customer)
        db.session.commit()
        flash(f"{len(customers)} customers deleted.", "success")
    else:
        flash("No customers selected.", "warning")
    return redirect(url_for('customers.list_customers'))

# ================================
# Add Payment Method
# ================================
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import PaymentMethod
from app.forms.payment_method_form import PaymentMethodForm

from sqlalchemy import cast, String



@bp.route('/add-payment-method', methods=['GET', 'POST'])
@login_required
def add_payment_method():
    # Ensure only the customer can add payment methods for themselves
    if current_user.role.name != 'CUSTOMER':
        abort(403)

    form = PaymentMethodForm()

    if form.validate_on_submit():
        # Find the customer record for the current user
        customer = Customer.query.filter_by(user_id=current_user.id).first()
        if not customer:
            flash("No customer profile found for this account.", "danger")
            return redirect(url_for('customers.view_customer', customer_id=current_user.id))

        # Check if the payment method already exists for this customer
        existing_payment = PaymentMethod.query.filter_by(
            user_id=current_user.id
        ).filter(
            cast(PaymentMethod.details['card_number'], String) == form.card_number.data
        ).first()

        if existing_payment:
            flash('This payment method is already added.', 'warning')
            return redirect(url_for('customers.view_customer', customer_id=current_user.id))

        #  Option 3 logic — set card_type depending on method_type
        if form.method_type.data == "MPESA":
            card_type_value = "MOBILE"
        elif form.method_type.data == "PAYPAL":
            card_type_value = "ONLINE"
        elif form.method_type.data == "BANK":
            card_type_value = "BANK"
        else:
            card_type_value = form.card_type.data or "UNKNOWN"

        # Create a new payment method
        new_payment_method = PaymentMethod(
            customer_id=customer.id,
            user_id=current_user.id,
            card_type=card_type_value,
            method_type=form.method_type.data,
            details={
                "card_number": form.card_number.data or "",
                "expiration_date": form.expiration_date.data or "",
                "cardholder_name": form.cardholder_name.data or ""
            },
            is_default=form.is_default.data
        )

        # Commit to database
        try:
            db.session.add(new_payment_method)
            db.session.commit()
            flash('Payment method added successfully!', 'success')
            return redirect(url_for('main.index', customer_id=current_user.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding your payment method: {str(e)}", 'danger')

    return render_template('customers/add_payment_method.html', form=form, title="Add Payment Method")





@bp.route('/billing-address/add', methods=['GET', 'POST'])
@login_required
def add_billing_address():
    if current_user.role.name != 'CUSTOMER':
        abort(403)
    if not current_user.customer:
        flash("Customer profile not found.", "danger")
        return redirect(url_for('main.dashboard'))

    form = BillingAddressForm()

    if form.validate_on_submit():
        # Unset previous default billing addresses if this is default
        if form.is_default_billing.data:
            ShippingAddress.query.filter_by(
                customer_id=current_user.customer.id,
                address_type='BILLING',
                is_default_billing=True
            ).update({'is_default_billing': False})

        billing_address = ShippingAddress(
            customer_id=current_user.customer.id,
            recipient_name=form.recipient_name.data,
            street=form.street.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            phone=form.phone.data,
            address_type='BILLING',
            is_default_billing=form.is_default_billing.data,
            zip_code=form.zip_code.data or '00000',
        )
        db.session.add(billing_address)
        db.session.commit()
        flash("Billing address added successfully.", "success")
        
        # Redirect straight to Add Payment Method page
        return redirect(url_for('customers.add_payment_method'))

    return render_template('customers/add_billing_address.html', form=form)




