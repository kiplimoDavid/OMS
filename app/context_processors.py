from app.extensions import db
from flask import session
from flask_login import current_user
from app.models import OrderItem, Order, OrderStatus, Customer
from sqlalchemy.orm import joinedload

def inject_cart_item_count():
    if current_user.is_authenticated and current_user.role.name == "CUSTOMER":
        # Join Order with Customer to filter by current user's ID
        cart = (
            Order.query
            .join(Customer)
            .options(joinedload(Order.items))  # Efficiently load order items
            .filter(Customer.user_id == current_user.id, Order.status == OrderStatus.CART)
            .first()
        )
        if cart:
            item_count = sum(item.quantity for item in cart.items)
            return {'cart_item_count': item_count}
    return {'cart_item_count': 0}

