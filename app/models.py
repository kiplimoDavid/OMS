from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import event, UniqueConstraint, func, CheckConstraint
from sqlalchemy.orm import validates
from app.extensions import db, login_manager
import enum
from sqlalchemy.types import TypeDecorator, Enum as SAEnum
from sqlalchemy import Index, ForeignKeyConstraint

# ==========================
# Custom Enum TypeDecorator
# ==========================
class CaseInsensitiveEnum(TypeDecorator):
    impl = db.String(50)
    cache_ok = True

    def __init__(self, enumclass, **kwargs):
        self.enumclass = enumclass
        kwargs['length'] = 50
        super().__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, self.enumclass):
            return value.name
        if isinstance(value, str):
            value = value.upper()
            try:
                return self.enumclass[value].name
            except KeyError:
                raise ValueError(f"Invalid {self.enumclass.__name__}: {value}")
        raise ValueError(f"Unexpected enum type: {type(value)}")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return self.enumclass[value]
        except KeyError:
            raise ValueError(f"Invalid value '{value}' for enum {self.enumclass.__name__}")

# ==========================
# Enums
# ==========================
class OrderStatus(enum.Enum):
    CART = 'CART'
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'
    REFUNDED = 'REFUNDED'
    RETURNED = 'RETURNED'
    ON_HOLD = 'ON_HOLD'
    PARTIALLY_SHIPPED = 'PARTIALLY_SHIPPED'

class PaymentStatus(enum.Enum):
    UNPAID = 'UNPAID'
    PAID = 'PAID'
    PARTIALLY_PAID = 'PARTIALLY_PAID'
    REFUNDED = 'REFUNDED'
    FAILED = 'FAILED'
    PENDING = 'PENDING'

class RoleEnum(enum.Enum):
    ADMIN = 'ADMIN'
    STAFF = 'STAFF'
    CUSTOMER = 'CUSTOMER'
    SUPPLIER = 'SUPPLIER'

class RefundStatus(enum.Enum):
    REQUESTED = 'REQUESTED'
    APPROVED = 'APPROVED'
    PROCESSED = 'PROCESSED'
    REJECTED = 'REJECTED'
    FAILED = 'FAILED'

class ShippingStatus(enum.Enum):
    PREPARING = 'PREPARING'
    IN_TRANSIT = 'IN_TRANSIT'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'
    RETURNED = 'RETURNED'
    DELAYED = 'DELAYED'

class NotificationType(enum.Enum):
    ORDER_UPDATE = 'ORDER_UPDATE'
    PAYMENT = 'PAYMENT'
    SHIPPING = 'SHIPPING'
    PROMOTION = 'PROMOTION'
    ACCOUNT = 'ACCOUNT'

# ==========================
# User & Related Models
# ==========================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_username', 'username'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(400))
    role = db.Column(CaseInsensitiveEnum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active_user = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)

    # Relationships
    customer = db.relationship('Customer', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', back_populates='user', cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', back_populates='user', cascade='all, delete-orphan')
    
    created_support_tickets = db.relationship(
        'SupportTicket', 
        back_populates='created_by_user',
        foreign_keys='SupportTicket.user_id'
    )
    closed_support_tickets = db.relationship(
        'SupportTicket', 
        back_populates='closed_by_user',
        foreign_keys='SupportTicket.closed_by'
    )
    assigned_support_tickets = db.relationship(
        'SupportTicket', 
        back_populates='assigned_to_user',
        foreign_keys='SupportTicket.assigned_to'
    )
    order_notes = db.relationship('OrderNote', back_populates='user')
    inventory_actions = db.relationship('InventoryLog', back_populates='user')
    audit_logs = db.relationship('AuditLog', back_populates='user')
    support_messages = db.relationship('SupportMessage', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == RoleEnum.ADMIN

    def is_staff(self):
        return self.role == RoleEnum.STAFF

    def is_customer(self):
        return self.role == RoleEnum.CUSTOMER

    def is_supplier(self):
        return self.role == RoleEnum.SUPPLIER

    def full_name(self):
        if self.customer:
            return self.customer.name
        return self.username


class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # Ensure unique
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(100))
    address = db.Column(db.Text)
    website = db.Column(db.String(200))
    rating = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    purchase_orders = db.relationship('PurchaseOrder', back_populates='vendor')
    
    # Relationships
    products = db.relationship('Product', back_populates='vendor')
    
    def __repr__(self):
        return f'<Vendor {self.name}>'

class Customer(db.Model):
    __tablename__ = 'customers'
    __table_args__ = (
        Index('ix_customers_email', 'email'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(100))
    company = db.Column(db.String(100))
    tax_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    loyalty_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='customer')
    order_status_histories = db.relationship('OrderStatusHistory', back_populates='customer')
    addresses = db.relationship(
        'ShippingAddress',
        back_populates='customer',
        cascade='all, delete-orphan',
        overlaps="shipping_addresses,billing_addresses"
    )
    shipping_addresses = db.relationship(
        'ShippingAddress',
        primaryjoin="and_(ShippingAddress.customer_id==Customer.id, ShippingAddress.address_type=='SHIPPING')",
        overlaps="addresses,billing_addresses"
    )
    billing_addresses = db.relationship(
        'ShippingAddress',
        primaryjoin="and_(ShippingAddress.customer_id==Customer.id, ShippingAddress.address_type=='BILLING')",
        overlaps="addresses,shipping_addresses"
    )
    orders = db.relationship('Order', back_populates='customer', cascade='all, delete-orphan')
    wishlist = db.relationship('WishlistItem', back_populates='customer', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='customer')
    payment_methods = db.relationship('PaymentMethod', back_populates='customer', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Customer {self.name}>"


class ShippingAddress(db.Model):
    __tablename__ = 'shipping_addresses'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), default='Kenya')
    phone = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    address_type = db.Column(db.String(100))  # 'SHIPPING' or 'BILLING'
    postal_code = db.Column(db.String(100))   # <- Check if this exists or not
    is_default = db.Column(db.Boolean, default=False)
    is_default_shipping = db.Column(db.Boolean, default=False)
    is_default_billing = db.Column(db.Boolean, default=False)  # ADD THIS




    # Relationships
    customer = db.relationship(
        'Customer',
        back_populates='addresses',
        overlaps="shipping_addresses,billing_addresses"
    )
    shipping_orders = db.relationship(
        'Order',
        back_populates='shipping_address',
        foreign_keys='Order.shipping_address_id'
    )
    billing_orders = db.relationship(
        'Order',
        back_populates='billing_address',
        foreign_keys='Order.billing_address_id'
    )

    def __repr__(self):
        return f'<ShippingAddress {self.id}: {self.street}, {self.city}>'

# ==========================
# Product Models
# ==========================
class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)  # Added slug
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))  # Added image
    is_active_user = db.Column(db.Boolean, default=True)  # Added active status
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', back_populates='category')
    children = db.relationship('ProductCategory', 
                              backref=db.backref('parent', remote_side=[id]),
                              order_by='ProductCategory.name')  # Added ordering
    
    def __init__(self, *args, **kwargs):
        if not kwargs.get('slug') and kwargs.get('name'):
            kwargs['slug'] = self.generate_slug(kwargs['name'])
        super().__init__(*args, **kwargs)
    
    def generate_slug(self, name):
        """Generate URL-friendly slug"""
        slug = name.lower().replace(' ', '-')
        # Ensure uniqueness
        counter = 1
        base_slug = slug
        while ProductCategory.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug
    
    @property
    def all_children(self):
        """Get all descendants in a flat list"""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.all_children)
        return children
    
    @property
    def path(self):
        """Get full category path (breadcrumbs)"""
        path = []
        current = self
        while current:
            path.append(current)
            current = current.parent
        return path[::-1]  # Return from root to current
    
    def __repr__(self):
        return f'<Category {self.name} (ID: {self.id})>'

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        Index('ix_products_name', 'name'),
        Index('ix_products_sku', 'sku'),
        Index('ix_products_category', 'category_id'),
        Index('ix_products_vendor', 'vendor_id'),
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('sale_price >= 0 OR sale_price IS NULL', name='check_sale_price_positive'),
        CheckConstraint('stock_quantity >= 0', name='check_stock_quantity'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    sku = db.Column(db.String(100), unique=True)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float)
    cost_price = db.Column(db.Float)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    min_order_quantity = db.Column(db.Integer, default=1)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'))
    description = db.Column(db.Text)
    short_description = db.Column(db.Text)
    specifications = db.Column(db.JSON)  # JSON for key-value specifications
    weight = db.Column(db.Float)  # in kg
    dimensions = db.Column(db.String(100))  # Format: "LxWxH" in cm
    is_featured = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    is_digital = db.Column(db.Boolean, default=False)
    download_url = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vendor = db.relationship('Vendor', back_populates='products')
    category = db.relationship('ProductCategory', back_populates='products')
    order_items = db.relationship('OrderItem', back_populates='product', cascade='all, delete-orphan')
    reviews = db.relationship('ProductReview', back_populates='product', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', back_populates='product', cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', back_populates='product', cascade='all, delete-orphan')
    inventory_logs = db.relationship('InventoryLog', back_populates='product', cascade='all, delete-orphan')
    
    related_products = db.relationship(
        'Product',
        secondary='product_relations',
        primaryjoin='Product.id == ProductRelation.product_id',
        secondaryjoin='Product.id == ProductRelation.related_product_id',
        backref='related_to'
    )
    
    discounts = db.relationship('Discount', secondary='product_discounts', back_populates='products')

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        total = sum(review.rating for review in self.reviews)
        return round(total / len(self.reviews), 1)

    @property
    def current_price(self):
        # Safely handle price comparisons
        if self.sale_price is not None and self.sale_price < self.price:
            return self.sale_price
        return self.price

    @validates('price', 'sale_price', 'cost_price')
    def validate_prices(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value

    @validates('stock_quantity')
    def validate_stock_quantity(self, key, value):
        if value < 0:
            raise ValueError("Stock quantity cannot be negative")
        return value

class ProductRelation(db.Model):
    __tablename__ = 'product_relations'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    related_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('product_id', 'related_product_id', name='uq_product_relation'),
    )

class ProductReview(db.Model):
    __tablename__ = 'product_reviews'
    __table_args__ = (
        Index('ix_reviews_product', 'product_id'),
        Index('ix_reviews_user', 'user_id'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    review = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

    @validates('rating')
    def validate_rating(self, key, rating):
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating

# ==========================
# Order Models
# ==========================
class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        Index('ix_orders_customer', 'customer_id'),
        Index('ix_orders_status', 'status'),
        Index('ix_orders_payment_status', 'payment_status'),
        UniqueConstraint('order_number', name='uq_order_order_number'),
        CheckConstraint('subtotal >= 0', name='check_subtotal_positive'),
        CheckConstraint('shipping_cost >= 0', name='check_shipping_cost_positive'),
        CheckConstraint('tax_amount >= 0', name='check_tax_amount_positive'),
        CheckConstraint('discount_amount >= 0', name='check_discount_amount_positive'),
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('shipping_addresses.id'))
    billing_address_id = db.Column(db.Integer, db.ForeignKey('shipping_addresses.id'))
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(CaseInsensitiveEnum(OrderStatus), default=OrderStatus.CART, nullable=False)
    payment_status = db.Column(CaseInsensitiveEnum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    shipping_cost = db.Column(db.Float, default=0.0, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    payment_method = db.Column(db.String(100))
    transaction_id = db.Column(db.String(120))
    estimated_delivery = db.Column(db.DateTime)
    actual_delivery = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'))
    order_number = db.Column(db.String(50), unique=True)
    shipping_method = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    shipping_status = db.Column(CaseInsensitiveEnum(ShippingStatus))

    # Relationships
    customer = db.relationship('Customer', back_populates='orders')
    shipping_address = db.relationship('ShippingAddress', foreign_keys=[shipping_address_id], back_populates='shipping_orders')
    billing_address = db.relationship('ShippingAddress', foreign_keys=[billing_address_id], back_populates='billing_orders')
    coupon = db.relationship('Coupon')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='order', cascade='all, delete-orphan')
    refunds = db.relationship('Refund', back_populates='order', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='order', cascade='all, delete-orphan')
    shipment = db.relationship('Shipment', back_populates='order', uselist=False, cascade='all, delete-orphan')
    notes_history = db.relationship('OrderNote', back_populates='order', cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', back_populates='order', cascade='all, delete-orphan')
    support_tickets = db.relationship('SupportTicket', back_populates='order', cascade='all, delete-orphan')

    @property
    def balance_due(self):
        total_paid = sum(payment.amount for payment in self.payments)
        return max(self.total_amount - total_paid, 0)

    def calculate_totals(self):
        self.subtotal = sum(item.total_price for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount


@event.listens_for(Order, 'after_insert')
def generate_order_number(mapper, connection, target):
    if not target.order_number:
        order_number = f"ORD{target.id:06d}"
        connection.execute(
            Order.__table__.update()
            .where(Order.id == target.id)
            .values(order_number=order_number)
        )
        

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        Index('ix_order_items_order', 'order_id'),
        Index('ix_order_items_product', 'product_id'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_positive'),
        CheckConstraint('discount >= 0', name='check_discount_positive'),
        CheckConstraint('total_price >= 0', name='check_total_price_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float)  # Cost at time of purchase
    variant = db.Column(db.String(100))  # For product variants

    # Relationships
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')
    refund_items = db.relationship('RefundItem', back_populates='order_item', cascade='all, delete-orphan')

@event.listens_for(OrderItem, 'before_insert')
@event.listens_for(OrderItem, 'before_update')
def calculate_total_price(mapper, connection, target):
    target.total_price = (target.unit_price - target.discount) * target.quantity

       

class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    __table_args__ = (
        Index('ix_status_history_order', 'order_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))  # New FK
    status = db.Column(CaseInsensitiveEnum(OrderStatus), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='status_history')
    user = db.relationship('User')
    customer = db.relationship('Customer', back_populates='order_status_histories')




class Payment(db.Model):
    __tablename__ = 'payments'
    __table_args__ = (
        Index('ix_payments_order', 'order_id'),
        Index('ix_payments_customer', 'customer_id'),
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50), nullable=False)  # M-PESA, Credit Card, etc.
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(CaseInsensitiveEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_gateway = db.Column(db.String(100))
    gateway_response = db.Column(db.JSON)  # Store gateway response data
    currency = db.Column(db.String(100), default='KES')
    notes = db.Column(db.Text)

    # Relationships
    order = db.relationship('Order', back_populates='payments')
    customer = db.relationship('Customer', back_populates='payments')
    refunds = db.relationship('Refund', back_populates='payment', cascade='all, delete-orphan')

class Refund(db.Model):
    __tablename__ = 'refunds'
    __table_args__ = (
        Index('ix_refunds_order', 'order_id'),
        Index('ix_refunds_payment', 'payment_id'),
        CheckConstraint('amount > 0', name='check_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(CaseInsensitiveEnum(RefundStatus), default=RefundStatus.REQUESTED)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    refund_method = db.Column(db.String(100))  # Original payment, bank transfer, store credit
    bank_account = db.Column(db.JSON)  # Bank details for transfer
    transaction_id = db.Column(db.String(100))

    # Relationships
    order = db.relationship('Order', back_populates='refunds')
    payment = db.relationship('Payment', back_populates='refunds')
    items = db.relationship('RefundItem', back_populates='refund', cascade='all, delete-orphan')
    processed_by_user = db.relationship('User')

class RefundItem(db.Model):
    __tablename__ = 'refund_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('amount >= 0', name='check_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refunds.id'), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    # Relationships
    refund = db.relationship('Refund', back_populates='items')
    order_item = db.relationship('OrderItem', back_populates='refund_items')

class OrderNote(db.Model):
    __tablename__ = 'order_notes'
    __table_args__ = (
        Index('ix_order_notes_order', 'order_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    note = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=True)  # Internal note vs customer visible
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', back_populates='notes_history')
    user = db.relationship('User', back_populates='order_notes')

class Coupon(db.Model):
    __tablename__ = 'coupons'
    __table_args__ = (
        Index('ix_coupons_code', 'code'),
        CheckConstraint('discount_value > 0', name='check_discount_value_positive'),
        CheckConstraint('usage_limit >= 0', name='check_usage_limit_positive'),
        CheckConstraint('times_used >= 0', name='check_times_used_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(100), nullable=False)  # percentage, fixed
    discount_value = db.Column(db.Float, nullable=False)
    valid_from = db.Column(db.DateTime)
    valid_to = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer, default=100)
    times_used = db.Column(db.Integer, default=0)
    min_order_value = db.Column(db.Float, default=0.0)
    max_discount = db.Column(db.Float)
    is_active_user = db.Column(db.Boolean, default=True)
    is_single_use = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Discount(db.Model):
    __tablename__ = 'discounts'
    __table_args__ = (
        CheckConstraint('discount_value > 0', name='check_discount_value_positive'),
        CheckConstraint('usage_limit >= 0', name='check_usage_limit_positive'),
        CheckConstraint('times_used >= 0', name='check_times_used_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(100), nullable=False)  # percentage, fixed
    discount_value = db.Column(db.Float, nullable=False)
    valid_from = db.Column(db.DateTime)
    valid_to = db.Column(db.DateTime)
    is_active_user = db.Column(db.Boolean, default=True)
    apply_to = db.Column(db.String(100), default='all')  # all, categories, products
    min_order_value = db.Column(db.Float)
    max_discount = db.Column(db.Float)
    usage_limit = db.Column(db.Integer)
    times_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', secondary='product_discounts', back_populates='discounts')

class ProductDiscount(db.Model):
    __tablename__ = 'product_discounts'
    discount_id = db.Column(db.Integer, db.ForeignKey('discounts.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(['discount_id'], ['discounts.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    )

class Invoice(db.Model):
    __tablename__ = 'invoices'
    __table_args__ = (
        Index('ix_invoices_order', 'order_id'),
        UniqueConstraint('invoice_number', name='uq_invoice_invoice_number'),
        CheckConstraint('amount >= 0', name='check_amount_positive'),
        CheckConstraint('tax_amount >= 0', name='check_tax_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    amount = db.Column(db.Float)
    tax_amount = db.Column(db.Float)
    pdf_url = db.Column(db.String(255))
    status = db.Column(db.String(100), default='UNPAID')  # UNPAID, PAID, PARTIALLY_PAID
    notes = db.Column(db.Text)

    # Relationships
    order = db.relationship('Order', back_populates='invoices')

@event.listens_for(Invoice, 'after_insert')
def generate_invoice_number(mapper, connection, target):
    if not target.invoice_number:
        invoice_number = f"INV{target.id:06d}"
        connection.execute(
            Invoice.__table__.update()
            .where(Invoice.id == target.id)
            .values(invoice_number=invoice_number)
        )

# ==========================
# Cart Model
# ==========================
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', 'variant', name='uq_cart_item'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    variant = db.Column(db.String(100))  # For product variants

    # Relationships
    user = db.relationship('User', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'variant', 
                            name='uq_cart_item_user_product_variant'),
    )

    # Subtotal calculation: This is the total price for the cart item
    @property
    def subtotal(self):
        # Make sure the product exists and has a price
        return round(self.product.price * self.quantity, 2) if self.product else 0.0


# ==========================
# Inventory Management
# ==========================
class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    __table_args__ = (
        Index('ix_inventory_product', 'product_id'),
        Index('ix_inventory_reference', 'reference_type', 'reference_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)  # Positive for addition, negative for deduction
    description = db.Column(db.Text)
    reference_id = db.Column(db.Integer)  # Order ID, Purchase Order ID, etc.
    reference_type = db.Column(db.String(100))  # 'order', 'purchase', 'adjustment'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='inventory_logs')
    user = db.relationship('User', back_populates='inventory_actions')

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    __table_args__ = (
        Index('ix_purchase_orders_vendor', 'vendor_id'),
        UniqueConstraint('po_number', name='uq_po_po_number'),
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery = db.Column(db.DateTime)
    received_date = db.Column(db.DateTime)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(100), default='PENDING')  # PENDING, ORDERED, RECEIVED, CANCELLED
    notes = db.Column(db.Text)
    po_number = db.Column(db.String(100), unique=True)

    # Relationships
    vendor = db.relationship('Vendor', back_populates='purchase_orders')
    items = db.relationship('PurchaseOrderItem', back_populates='purchase_order', cascade='all, delete-orphan')
    def __repr__(self):
        return f'<PurchaseOrder {self.id} - {self.vendor.name}>'

@event.listens_for(PurchaseOrder, 'after_insert')
def generate_po_number(mapper, connection, target):
    if not target.po_number:
        po_number = f"PO{target.id:06d}"
        connection.execute(
            PurchaseOrder.__table__.update()
            .where(PurchaseOrder.id == target.id)
            .values(po_number=po_number)
        )

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('unit_cost >= 0', name='check_unit_cost_positive'),
        CheckConstraint('received_quantity >= 0', name='check_received_quantity_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    received_quantity = db.Column(db.Integer, default=0)

    # Relationships
    purchase_order = db.relationship('PurchaseOrder', back_populates='items')
    product = db.relationship('Product')
    
    def __repr__(self):
        return f'<POItem {self.product.name} x {self.quantity}>'

# ==========================
# Shipping & Fulfillment
# ==========================
class Shipment(db.Model):
    __tablename__ = 'shipments'
    __table_args__ = (
        Index('ix_shipments_order', 'order_id'),
        UniqueConstraint('tracking_number', name='uq_shipment_tracking'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True, nullable=False)
    shipping_method = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100), unique=True)
    carrier = db.Column(db.String(100))
    status = db.Column(CaseInsensitiveEnum(ShippingStatus), default=ShippingStatus.PREPARING)
    shipped_at = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)
    actual_delivery = db.Column(db.DateTime)
    shipping_cost = db.Column(db.Float)
    notes = db.Column(db.Text)

    # Relationships
    order = db.relationship('Order', back_populates='shipment')
    tracking_events = db.relationship('TrackingEvent', back_populates='shipment', cascade='all, delete-orphan')

class TrackingEvent(db.Model):
    __tablename__ = 'tracking_events'
    __table_args__ = (
        Index('ix_tracking_shipment', 'shipment_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    event_time = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(200))
    status = db.Column(db.String(100))
    description = db.Column(db.Text)
    event_code = db.Column(db.String(100))  # Standardized event code

    # Relationships
    shipment = db.relationship('Shipment', back_populates='tracking_events')

# ==========================
# Payment Methods
# ==========================
from sqlalchemy import Index
from datetime import datetime
import json

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    __table_args__ = (
        Index('ix_payment_methods_customer', 'customer_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    card_type = db.Column(db.String(100), nullable=False)
    method_type = db.Column(db.String(100), nullable=False)  # M-PESA, Credit Card, etc.
    details = db.Column(db.JSON, nullable=False)  # Store method-specific details
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


    # Relationships
    customer = db.relationship('Customer', back_populates='payment_methods')

    @property
    def last4(self):
        """Extract the last 4 digits of the card number from the details."""
        # Check if details is a dictionary (should be JSON parsed)
        if isinstance(self.details, str):
            try:
                # If it's a string, try to parse it as JSON
                details = json.loads(self.details)
            except json.JSONDecodeError:
                # If it fails, return an empty string
                return ''
        else:
            # Use the details as a dictionary if it's already a parsed JSON object
            details = self.details
        
        # Safely extract the last 4 digits of the card number
        card_number = details.get('card_number', '')
        return card_number[-4:] if card_number else ''  # Safely extract last 4 digits

    # Ensuring that there can only be one default payment method
    @staticmethod
    def set_default(customer_id, payment_method_id):
        """Set the provided payment method as the default for the customer."""
        # Unset any default payment method for this customer
        PaymentMethod.query.filter_by(customer_id=customer_id, is_default=True).update({"is_default": False})
        
        # Set the selected payment method as default
        payment_method = PaymentMethod.query.get(payment_method_id)
        if payment_method:
            payment_method.is_default = True
            db.session.commit()
        else:
            raise ValueError("Payment method not found")



# ==========================
# Customer Support
# ==========================
class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    __table_args__ = (
        Index('ix_tickets_user', 'user_id'),
        Index('ix_tickets_order', 'order_id'),
        Index('ix_tickets_status', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(100), default='OPEN')  # OPEN, IN_PROGRESS, CLOSED
    priority = db.Column(db.String(100), default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    created_by_user = db.relationship('User', foreign_keys=[user_id], back_populates='created_support_tickets')
    closed_by_user = db.relationship('User', foreign_keys=[closed_by], back_populates='closed_support_tickets')
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to], back_populates='assigned_support_tickets')
    messages = db.relationship('SupportMessage', back_populates='ticket', cascade='all, delete-orphan')
    order = db.relationship('Order', back_populates='support_tickets')

class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    __table_args__ = (
        Index('ix_messages_ticket', 'ticket_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Internal note vs customer visible
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attachments = db.Column(db.JSON)  # List of attachment URLs

    # Relationships
    ticket = db.relationship('SupportTicket', back_populates='messages')
    user = db.relationship('User', back_populates='support_messages')

# ==========================
# Miscellaneous Models
# ==========================
class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    __table_args__ = (
        UniqueConstraint('customer_id', 'product_id', name='uq_wishlist'),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='wishlist')
    product = db.relationship('Product', back_populates='wishlist_items')

class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = (
        Index('ix_notifications_user', 'user_id'),
        Index('ix_notifications_type', 'type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(CaseInsensitiveEnum(NotificationType), default=NotificationType.ORDER_UPDATE)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(255))
    related_id = db.Column(db.Integer)  # ID of related order, product, etc.

    # Relationships
    user = db.relationship('User', back_populates='notifications')

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)  # Publicly accessible via API
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    __table_args__ = (
        Index('ix_audit_logs_user', 'user_id'),
        Index('ix_audit_logs_model', 'model'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    changes = db.Column(db.JSON)  # JSON of {field: [old_value, new_value]}
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='audit_logs')

    # ==========================
    # M-pesa Payment Model
    # ==========================

class MpesaTransaction(db.Model):
    __tablename__ = "mpesa_transactions"

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    merchant_request_id = db.Column(db.String(100))
    checkout_request_id = db.Column(db.String(100))

    result_code = db.Column(db.String(100))
    result_desc = db.Column(db.String(255))

    mpesa_receipt_number = db.Column(db.String(50))
    transaction_date = db.Column(db.String(100))

    status = db.Column(db.String(100), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================
# Login Manager Hook
# ==========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
