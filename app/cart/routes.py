from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from flask_login import login_required, current_user
from app import db
from app.models import (
    Order,
    OrderItem,
    Product,
    OrderStatus,
    PaymentStatus,
    CartItem,
    ShippingAddress,
    PaymentMethod  # Added import
)

# Add at the top of cart/routes.py
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, validators

class CheckoutForm(FlaskForm):
    shipping_address = SelectField('Shipping Address', coerce=int, validators=[validators.InputRequired()])
    payment_method = SelectField('Payment Method', coerce=int, validators=[validators.InputRequired()])
    billing_address = TextAreaField('Billing Address')

from app.extensions import csrf

bp = Blueprint('cart', __name__)

# ─── VIEW CART ────────────────────────────────────────────────────────────────
@bp.route('/', methods=['GET'])
def view_cart():
    if current_user.is_authenticated and not current_user.is_customer():
        flash("Only customers can view the cart.", "danger")
        return redirect(url_for('main.dashboard'))

    cart_items = []
    total = 0.0

    if current_user.is_authenticated:
        db_cart = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_cart:
            subtotal = item.product.price * item.quantity
            total += subtotal
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })
    else:
        cart_data = session.get('cart', [])
        for item in cart_data:
            product = Product.query.get(item['product_id'])
            if product:
                qty = item.get('quantity', 1)
                subtotal = product.price * qty
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': qty,
                    'subtotal': subtotal
                })

    return render_template('cart/view_cart.html', cart_items=cart_items, total=total)


# ─── ADD TO CART ─────────────────────────────────────────────────────────────
@bp.route('/add/<int:product_id>', methods=['POST'])
@csrf.exempt
def add_to_cart(product_id):
    if current_user.is_authenticated and not current_user.is_customer():
        flash("Only customers can add to cart.", "danger")
        return redirect(url_for('main.dashboard'))

    try:
        quantity = max(1, int(request.form.get('quantity', 1)))
    except ValueError:
        flash("Invalid quantity provided.", "danger")
        return redirect(url_for('products.view_product', product_id=product_id))

    product = Product.query.get_or_404(product_id)

    if current_user.is_authenticated:
        existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing:
            existing.quantity += quantity
        else:
            db.session.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity))
        db.session.commit()
    else:
        cart_data = session.get('cart', [])
        for entry in cart_data:
            if entry['product_id'] == product_id:
                entry['quantity'] += quantity
                break
        else:
            cart_data.append({'product_id': product_id, 'quantity': quantity})
        session['cart'] = cart_data

    flash("Product added to cart.", "success")
    return redirect(url_for('products.view_product', product_id=product_id))


# ─── REMOVE FROM CART ────────────────────────────────────────────────────────
@bp.route('/remove/<int:product_id>')
def remove_from_cart(product_id):
    if current_user.is_authenticated and not current_user.is_customer():
        flash("Only customers can modify the cart.", "danger")
        return redirect(url_for('main.dashboard'))

    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).delete()
        db.session.commit()
    else:
        cart_data = session.get('cart', [])
        cart_data = [entry for entry in cart_data if entry['product_id'] != product_id]
        session['cart'] = cart_data

    flash("Item removed from cart.", "info")
    return redirect(url_for('cart.view_cart'))


# ─── CLEAR CART ──────────────────────────────────────────────────────────────
@bp.route('/clear')
def clear_cart():
    if current_user.is_authenticated and not current_user.is_customer():
        flash("Only customers can clear the cart.", "danger")
        return redirect(url_for('main.dashboard'))

    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session['cart'] = []

    flash("Cart cleared.", "info")
    return redirect(url_for('cart.view_cart'))

import json

# ─── CHECKOUT ────────────────────────────────────────────────────────────────
@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Ensure the current user is a customer
    if not current_user.is_customer():
        flash("Only customers can checkout.", "danger")
        return redirect(url_for('main.dashboard'))

    # Ensure the customer profile exists
    if not current_user.customer:
        flash("Customer profile not found. Please contact support.", "danger")
        return redirect(url_for('main.dashboard'))

    # Fetch the customer's cart items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Ensure the cart is not empty
    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('cart.view_cart'))
    
    # Fetch customer's shipping and billing addresses
    shipping_addresses = current_user.customer.shipping_addresses
    billing_addresses = current_user.customer.billing_addresses

    # Validate that the customer has at least one shipping address and billing address
    if not shipping_addresses:
        flash("Please add a shipping address before checkout.", "danger")
        return redirect(url_for('customers.add_billing_address'))
    
    if not billing_addresses:
        flash("Please add a billing address before checkout.", "danger")
        return redirect(url_for('customers.add_billing_address'))

    # Fetch payment methods
    payment_methods = current_user.customer.payment_methods.all()

    #  Parse `details` JSON if stored as a string
    for pm in payment_methods:
        if isinstance(pm.details, str):
            try:
                pm.details = json.loads(pm.details)
            except json.JSONDecodeError:
                pm.details = {}

    # Validate that the customer has at least one payment method
    if not payment_methods:
        flash("Please add a payment method before checkout.", "danger")
        return redirect(url_for('customers.add_payment_method'))

    # Initialize the checkout form
    form = CheckoutForm()

    # Populate the choices for the shipping and billing addresses in the form
    form.shipping_address.choices = [(a.id, f"{a.recipient_name}, {a.street}, {a.city}, {a.country}") for a in shipping_addresses]
    form.billing_address.choices = [(a.id, f"{a.recipient_name}, {a.street}, {a.city}, {a.country}") for a in billing_addresses]
    form.payment_method.choices = [(m.id, f"{m.card_type} ****{m.details.get('card_number', '')[-4:] if isinstance(m.details, dict) else ''}") for m in payment_methods]

    # If the form is submitted and valid, process the checkout
    if form.validate_on_submit():
        print("Shipping address selected ID:", form.shipping_address.data)
        print("Billing address selected ID:", form.billing_address.data)
        print("Payment method selected ID:", form.payment_method.data)

        # Retrieve the selected shipping address, billing address, and payment method
        shipping_address = ShippingAddress.query.get(form.shipping_address.data)
        billing_address = ShippingAddress.query.get(form.billing_address.data)
        payment_method = PaymentMethod.query.get(form.payment_method.data)
        billing_address_data = form.billing_address.data or None

        # Validate that the shipping address, billing address, and payment method exist
        if not shipping_address or not billing_address or not payment_method:
            flash("Invalid shipping address, billing address, or payment method.", "danger")
            return redirect(url_for('cart.checkout'))

        # Calculate the total price of the cart items
        total = float(calculate_cart_total(cart_items)) if cart_items else 0.0

        # Create the order
        order = Order(
            customer_id=current_user.id,
            shipping_address_id=shipping_address.id,
            billing_address=billing_address_data,
            payment_method_id=payment_method.id,
            total_amount=total,
            status=OrderStatus.PENDING
        )
        db.session.add(order)

        # Add the order items (cart items) to the order
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                quantity=item.quantity,
                unit_price=item.product.price,
                total_price=item.quantity * item.product.price
            )
            db.session.add(order_item)

        # Commit the transaction
        db.session.commit()

        # Clear the cart items after the order is placed
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        flash("Order placed successfully!", "success")
        return redirect(url_for('cart.order_confirmation', order_id=order.id))

    # Recalculate the total in case the form is not submitted yet
    total = float(calculate_cart_total(cart_items)) if cart_items else 0.0

    return render_template(
        'cart/checkout.html', 
        form=form, 
        cart_items=cart_items, 
        total=total,
        shipping_addresses=shipping_addresses, 
        billing_addresses=billing_addresses,
        payment_methods=payment_methods
    )


# ─── HELPER FUNCTION ───────────────────────────────────────────────────────────
def calculate_cart_total(cart_items):
    """Calculate the total price of the cart items."""
    # Ensure total price is a float
    return sum(float(item.product.price) * item.quantity for item in cart_items)
