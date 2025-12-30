import random
from faker import Faker
from datetime import datetime, timedelta
import json
import uuid

from app import db
from app.models import (
    User, Customer, Product, ProductCategory, Order,
    OrderItem, OrderStatus, PaymentStatus, RoleEnum,
    CartItem, ShippingAddress, Vendor, Payment, Refund,
    Shipment, TrackingEvent, SupportTicket, SupportMessage,
    Notification, WishlistItem, PurchaseOrder, PurchaseOrderItem,
    InventoryLog, Discount, Coupon, ProductDiscount,
    OrderStatusHistory, RefundItem, ProductReview,
    OrderNote, PaymentMethod, NotificationType
)

fake = Faker()

# =====================
# SEEDING CONFIGURATION
# =====================
NUM_CUSTOMERS = 150
NUM_PRODUCTS = 300
NUM_ORDERS = 700
NUM_ADMINS = 10
NUM_STAFF = 20
NUM_VENDORS = 50
NUM_PURCHASE_ORDERS = 120
NUM_SUPPORT_TICKETS = 180
NUM_WISHLIST_ITEMS = 400
NUM_REVIEWS = 500

CATEGORIES = [
    ('Electronics', None),
    ('Laptops', 'Electronics'),
    ('Smartphones', 'Electronics'),
    ('Tablets', 'Electronics'),
    ('Headphones', 'Electronics'),
    ('Fashion', None),
    ('Men Clothing', 'Fashion'),
    ('Women Clothing', 'Fashion'),
    ('Watches', 'Fashion'),
    ('Footwear', 'Fashion'),
    ('Home & Kitchen', None),
    ('Furniture', 'Home & Kitchen'),
    ('Cookware', 'Home & Kitchen'),
    ('Storage', 'Home & Kitchen'),
    ('Home Decor', 'Home & Kitchen'),
    ('Books', None),
    ('Fiction', 'Books'),
    ('Non-Fiction', 'Books'),
    ('Children’s Books', 'Books'),
    ('Comics', 'Books'),
    ('Toys', None),
    ('Board Games', 'Toys'),
    ('Outdoor Toys', 'Toys'),
    ('Educational Toys', 'Toys'),
    ('Sports', None),
    ('Fitness Equipment', 'Sports'),
    ('Cycling', 'Sports'),
    ('Running', 'Sports'),
    ('Beauty', None),
    ('Skincare', 'Beauty'),
    ('Makeup', 'Beauty'),
    ('Haircare', 'Beauty'),
    ('Fragrances', 'Beauty'),
    ('Office Supplies', None),
    ('Stationery', 'Office Supplies'),
    ('Printers', 'Office Supplies'),
    ('Computer Accessories', 'Office Supplies'),
    ('Groceries', None),
    ('Snacks', 'Groceries'),
    ('Beverages', 'Groceries'),
    ('Organic Foods', 'Groceries'),
    ('Canned Goods', 'Groceries'),
    ('Automotive', None),
    ('Car Accessories', 'Automotive'),
    ('Tools', 'Automotive'),
    ('Motorbike Gear', 'Automotive'),
    ('Pet Supplies', None),
    ('Dog Food', 'Pet Supplies'),
    ('Cat Toys', 'Pet Supplies'),
    ('Aquarium', 'Pet Supplies')
]

# ==========================
# CATEGORY SEEDER
# ==========================
def create_categories():
    print("📦 Creating product categories...")
    categories = {}
    category_objs = []
    
    # Create all categories first
    for name, parent_name in CATEGORIES:
        category = ProductCategory(
            name=name,
            slug=name.lower().replace(' ', '-').replace('&', 'and'),
            description=fake.sentence()
        )
        db.session.add(category)
        categories[name] = category
        category_objs.append(category)
    
    db.session.commit()
    
    # Set parent-child relationships
    for name, parent_name in CATEGORIES:
        if parent_name:
            child = categories[name]
            parent = categories[parent_name]
            child.parent_id = parent.id
    
    db.session.commit()
    return category_objs

# ==========================
# VENDOR SEEDER
# ==========================
def create_vendors():
    vendors = []
    vendor_names = set()  # Track used names to avoid duplicates
    
    for _ in range(15):
        while True:
            name = fake.company()
            # Ensure the name is unique
            if name not in vendor_names:
                vendor_names.add(name)
                break
        
        vendor = Vendor(
            name=name,  # Use the unique name
            contact_name=fake.name(),
            contact_email=fake.email(),
            contact_phone=fake.phone_number(),
            address=fake.address(),
            website=fake.url(),
            rating=round(random.uniform(1.0, 5.0), 1),
            created_at=fake.date_time_this_decade(),
            updated_at=fake.date_time_this_decade()
        )
        vendors.append(vendor)
    
    db.session.add_all(vendors)
    db.session.commit()
    return vendors
# ==========================
# PRODUCT SEEDER
# ==========================
def create_products(categories, vendors):
    import uuid  # Import UUID module
    products = []
    print("🛒 Creating products...")
    
    # Define a list of product image URLs
    product_images = [
        "https://picsum.photos/300/300?image=1",
        "https://picsum.photos/300/300?image=2",
        "https://picsum.photos/300/300?image=3",
        "https://picsum.photos/300/300?image=4",
        "https://picsum.photos/300/300?image=5",
        "https://picsum.photos/300/300?image=6",
        "https://picsum.photos/300/300?image=7",
        "https://picsum.photos/300/300?image=8",
        "https://picsum.photos/300/300?image=9",
        "https://picsum.photos/300/300?image=10"
    ]
    
    # Pre-generate unique slugs to ensure uniqueness
    unique_slugs = set()
    slugs = []
    
    for i in range(50):
        while True:
            # Generate a base slug using product index and random word
            base_slug = f"product-{i+1}-{fake.word()}"
            # Sanitize and truncate slug to 120 characters
            slug_candidate = base_slug.lower().replace(' ', '-')[:120]
            
            # Ensure slug is unique
            if slug_candidate not in unique_slugs:
                unique_slugs.add(slug_candidate)
                slugs.append(slug_candidate)
                break
    
    # Create products with pre-generated slugs
    for i in range(50):
        product_name = fake.sentence(nb_words=3).replace('.', '')
        category = random.choice(categories)
        vendor = random.choice(vendors)
        
        product = Product(
            name=product_name,
            slug=slugs[i],
            sku=f"SKU-{str(uuid.uuid4())[:8].upper()}",  # Unique SKU with UUID
            price=round(random.uniform(10, 500), 2),
            sale_price=round(random.uniform(5, 450), 2) if random.random() > 0.7 else None,
            cost_price=round(random.uniform(5, 200), 2),
            stock_quantity=random.randint(0, 1000),
            reorder_level=random.randint(5, 20),
            min_order_quantity=random.randint(1, 10),
            vendor_id=vendor.id,
            description=fake.paragraph(nb_sentences=5),
            short_description=fake.sentence(),
            specifications={"color": fake.color_name(), "material": fake.word()},
            weight=round(random.uniform(0.1, 10.0), 2),
            dimensions=f"{random.randint(5,50)}x{random.randint(5,50)}x{random.randint(5,50)}",
            is_featured=random.random() > 0.8,
            is_digital=random.random() > 0.9,
            download_url=fake.url() if random.random() > 0.9 else None,
            image_url=random.choice(product_images),  # Now defined
            category_id=category.id,
            created_at=fake.date_time_this_decade(),
        )
        products.append(product)
        db.session.add(product)
    
    db.session.commit()
    return products

# ==========================
# USER + CUSTOMER SEEDER
# ==========================
def create_users_and_customers():
    print("👤 Creating admin, staff, and customer accounts...")
    customers = []

    print("\n🔐 Sample Login Credentials:\n")

    # Create Admin Users
    for i in range(NUM_ADMINS):
        username = f'admin{i+1}'
        email = f'{username}@example.com'
        password = f'{username}.p'

        admin = User(
            username=username,
            email=email,
            role=RoleEnum.ADMIN,
            is_active_user=True,
            is_verified=True
        )
        admin.set_password(password)
        db.session.add(admin)

        if i == 0:
            print(f"🛡️ Admin Login → Username: {username}, Password: {password}")

    # Create Staff Users
    for i in range(NUM_STAFF):
        username = f'staff{i+1}'
        email = f'{username}@example.com'
        password = f'{username}.p'

        staff = User(
            username=username,
            email=email,
            role=RoleEnum.STAFF,
            is_active_user=True,
            is_verified=True
        )
        staff.set_password(password)
        db.session.add(staff)

        if i == 0:
            print(f"👷 Staff Login → Username: {username}, Password: {password}")

    # Create Customer Users and Linked Profiles
    for i in range(NUM_CUSTOMERS):
        username = f'customer{i+1}'
        email = f'{username}@example.com'
        password = f'{username}.p'

        user = User(
            username=username,
            email=email,
            role=RoleEnum.CUSTOMER,
            is_active_user=True,
            is_verified=random.random() > 0.2  # 80% verified
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        customer = Customer(
            user_id=user.id,
            name=fake.name(),
            email=email,
            phone=fake.phone_number(),
            company=fake.company() if random.random() > 0.7 else None,
            tax_id=fake.bothify(text='??######'),
            notes=fake.sentence(),
            loyalty_points=random.randint(0, 500)
        )
        db.session.add(customer)
        db.session.flush()

        # Create Shipping and Billing addresses for each customer
        num_addresses = random.randint(1, 3)  # Random number of addresses for the customer
        for _ in range(num_addresses):
            address_type = random.choice(['SHIPPING', 'BILLING'])
            address = ShippingAddress(
                customer_id=customer.id,
                address_type=address_type,
                recipient_name=fake.name(),
                street=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                zip_code=fake.zipcode(),           # REQUIRED field, must be set
                country=fake.country(),
                phone=fake.phone_number(),
                is_default=random.random() > 0.8,
                postal_code=None,          
            )
            if address_type == 'SHIPPING':
                address.is_default_shipping = random.random() > 0.8
            elif address_type == 'BILLING':
                address.is_default_billing = random.random() > 0.8

            db.session.add(address)

        # Create payment methods for customers (70% chance to have payment methods)
        if random.random() > 0.3:  # 70% have payment methods
            for _ in range(random.randint(1, 2)):
                method_type = random.choice(['M-PESA', 'Credit Card', 'PayPal'])
                
                # Handle different payment method types
                if method_type == 'Credit Card':
                    card_type = random.choice(['Visa', 'MasterCard', 'Amex', 'Discover'])
                    details = {
                        'card_number': fake.credit_card_number(),
                        'expiry': fake.credit_card_expire(),
                        'cvv': fake.credit_card_security_code()
                    }
                elif method_type == 'M-PESA':
                    card_type = 'N/A'
                    details = {'phone': fake.phone_number()}
                else:  # PayPal
                    card_type = 'N/A'
                    details = {'email': fake.email()}
                
                payment_method = PaymentMethod(
                    customer_id=customer.id,
                    user_id=user.id,  # ✅ Link payment method to the user
                    card_type=card_type,
                    method_type=method_type,
                    details=json.dumps(details),
                    is_default=random.random() > 0.7,
                    created_at=datetime.utcnow()
                )
                db.session.add(payment_method)

        customers.append(customer)

        if i == 0:
            print(f"🛍️ Customer Login → Username: {username}, Password: {password}")

    db.session.commit()
    return customers


# ==========================
# ORDER SEEDER
# ==========================
def create_orders(customers, products):
    from app.models import ShippingStatus, OrderStatus, PaymentStatus, RefundStatus
    from datetime import timedelta
    import random
    from faker import Faker
    import uuid
    
    fake = Faker()
    print("📦 Creating orders and order items...")
    orders = []
    NUM_ORDERS = 20
    shipping_statuses = list(ShippingStatus) + [None]

    for i in range(NUM_ORDERS):
        if i > 0 and i % 500 == 0:
            print(f"  → {i} orders created...")

        customer = random.choice(customers)
        order_date = fake.date_time_between(start_date='-1y', end_date='now')
        
        # Get customer addresses
        customer_addresses = ShippingAddress.query.filter_by(customer_id=customer.id).all()
        shipping_address = random.choice(customer_addresses) if customer_addresses else None
        billing_address = random.choice(customer_addresses) if customer_addresses else None
        
        order = Order(
            customer_id=customer.id,
            order_date=order_date,
            status=random.choice(list(OrderStatus)),
            payment_status=random.choice(list(PaymentStatus)),
            shipping_address_id=shipping_address.id if shipping_address else None,
            billing_address_id=billing_address.id if billing_address else None,
            subtotal=0.0,
            shipping_cost=round(random.uniform(5.0, 50.0), 2),
            tax_amount=round(random.uniform(2.0, 30.0), 2),
            discount_amount=0.0,
            total_amount=0.0,
            payment_method=random.choice(['M-PESA', 'Credit Card', 'PayPal', 'Bank Transfer']),
            transaction_id=fake.unique.uuid4(),
            estimated_delivery=order_date + timedelta(days=random.randint(2, 14)),
            actual_delivery=order_date + timedelta(days=random.randint(5, 20)) if random.random() > 0.3 else None,
            shipping_method=random.choice(['Standard', 'Express', 'Overnight']),
            tracking_number=fake.unique.bothify(text='TRK-####-####-####') if random.random() > 0.4 else None,
            shipping_status=random.choice(shipping_statuses)
        )
        db.session.add(order)
        db.session.flush()
        orders.append(order)

        # Create order status history
        status_history = []
        for status in [OrderStatus.PENDING, order.status]:
            if status != OrderStatus.PENDING or random.random() > 0.5:
                history_entry = OrderStatusHistory(
                    order_id=order.id,
                    status=status,
                    changed_at=fake.date_time_between(start_date=order_date, end_date='now'),
                    notes=f"Status changed to {status.value}"
                )
                db.session.add(history_entry)
                status_history.append(history_entry)

        # Create order items
        total = 0.0
        for _ in range(random.randint(1, 5)):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            
            # Check stock availability
            if product.stock_quantity < quantity:
                continue
                
            unit_price = product.current_price
            discount = round(random.uniform(0, 0.25) * unit_price, 2)
            subtotal = (unit_price - discount) * quantity
            total += subtotal

            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                total_price=subtotal,
                variant=random.choice(['Black', 'White', 'Blue', 'Red']) if random.random() > 0.7 else None
            )
            db.session.add(item)
            
            # Update product stock
            product.stock_quantity -= quantity
            
            # Create inventory log
            log = InventoryLog(
                product_id=product.id,
                change=-quantity,
                description=f"Order ID: {order.id}",
                reference_id=order.id,
                reference_type='order'
            )
            db.session.add(log)

        # Apply discounts
        discount_amount = round(total * random.uniform(0, 0.15), 2) if random.random() > 0.7 else 0.0
        order.sfubtotal = round(total, 2)
        order.discount_amount = discount_amount
        order.total_amount = round(total + order.shipping_cost + order.tax_amount - discount_amount, 2)

        # Create payments for paid orders
        payment = None
        if order.payment_status != PaymentStatus.UNPAID:
            payment_amount = order.total_amount
            if order.payment_status == PaymentStatus.PARTIALLY_PAID:
                payment_amount = round(order.total_amount * random.uniform(0.3, 0.9), 2)
            
            payment = Payment(
                order_id=order.id,
                customer_id=customer.id,
                amount=payment_amount,
                payment_date=fake.date_time_between(start_date=order_date, end_date='now'),
                method=order.payment_method,
                transaction_id=fake.unique.uuid4(),
                status=PaymentStatus.PAID,
                payment_gateway=random.choice(['M-PESA', 'Stripe', 'PayPal']),
                gateway_response={'status': 'success', 'code': '200'},
                currency='KES'
            )
            db.session.add(payment)
            # Flush to ensure payment gets an ID
            db.session.flush()

        # Create shipment for shipped orders
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            shipment = Shipment(
                order_id=order.id,
                shipping_method=order.shipping_method,
                tracking_number=order.tracking_number,
                carrier=random.choice(['DHL', 'FedEx', 'UPS', 'Aramex']),
                status=ShippingStatus.IN_TRANSIT,
                shipped_at=fake.date_time_between(start_date=order_date, end_date='now'),
                estimated_delivery=order.estimated_delivery,
                actual_delivery=order.actual_delivery,
                shipping_cost=order.shipping_cost
            )
            db.session.add(shipment)
            db.session.flush()
            
            # Create tracking events
            events = [
                ('PREPARING', 'Package prepared for shipment'),
                ('IN_TRANSIT', 'Package in transit'),
                ('OUT_FOR_DELIVERY', 'Package out for delivery')
            ]
            
            # Add DELIVERED event only if order is delivered
            if order.status == OrderStatus.DELIVERED:
                events.append(('DELIVERED', 'Package delivered'))
            
            event_date = shipment.shipped_at
            for status, description in events:
                event_date += timedelta(days=random.randint(1, 3))
                event = TrackingEvent(
                    shipment_id=shipment.id,
                    event_time=event_date,
                    location=fake.city(),
                    status=status,
                    description=description,
                    event_code=f"EVT-{status[:3].upper()}"
                )
                db.session.add(event)

        # Create refunds for refunded orders
        if order.status == OrderStatus.REFUNDED:
            # If no payment exists, create one
            if not payment:
                payment = Payment(
                    order_id=order.id,
                    customer_id=customer.id,
                    amount=order.total_amount,
                    payment_date=fake.date_time_between(start_date=order_date, end_date='now'),
                    method=order.payment_method,
                    transaction_id=fake.unique.uuid4(),
                    status=PaymentStatus.PAID,
                    payment_gateway=random.choice(['M-PESA', 'Stripe', 'PayPal']),
                    gateway_response={'status': 'success', 'code': '200'},
                    currency='KES'
                )
                db.session.add(payment)
                # Flush to ensure payment gets an ID
                db.session.flush()
            
            # Now payment should have an ID
            if payment and payment.id:
                refund = Refund(
                    order_id=order.id,
                    payment_id=payment.id,
                    amount=round(order.total_amount * random.uniform(0.5, 1.0), 2),
                    reason=random.choice(['Customer request', 'Defective product', 'Late delivery']),
                    status=RefundStatus.PROCESSED,
                    processed_at=fake.date_time_between(start_date=order_date, end_date='now'),
                    refund_method=random.choice(['Original Payment Method', 'Bank Transfer', 'Store Credit']),
                    bank_account={
                        'bank': fake.company(),
                        'account_name': fake.name(),
                        'account_number': fake.iban()
                    },
                    transaction_id=fake.unique.uuid4()
                )
                db.session.add(refund)
                db.session.flush()
                
                # Create refund items
                for item in order.items:
                    if random.random() > 0.5:  # Refund some items
                        refund_item = RefundItem(
                            refund_id=refund.id,
                            order_item_id=item.id,
                            quantity=min(item.quantity, random.randint(1, item.quantity)),
                            amount=round(item.total_price * random.uniform(0.5, 1.0), 2)
                        )
                        db.session.add(refund_item)
            else:
                print(f"⚠️ Could not create refund for order {order.id}: No payment available")

        # Pre-fetch user IDs for order notes
        user_ids = [u.id for u in User.query.all()]
        # Create order notes
        for _ in range(random.randint(0, 3)):
            note = OrderNote(
                order_id=order.id,
                user_id=random.choice(user_ids),
                note=fake.sentence(),
                is_internal=random.random() > 0.3
            )
            db.session.add(note)

    db.session.commit()
    print(f"✔️ {len(orders)} orders created successfully.")
    return orders

#=========== PAYMENT METHODS=======
def create_payment_methods(customers):
    payment_methods = []
    card_types = ['Visa', 'MasterCard', 'American Express', 'Discover']
    
    for customer in customers:
        # Create 1-3 payment methods per customer
        for _ in range(random.randint(1, 3)):
            pm = PaymentMethod(
                customer_id=customer.id,
                card_type=random.choice(card_types),  # Always set card_type
                cardholder_name=fake.name(),
                last4=str(fake.random_number(digits=4, fix_len=True)),
                expiration_date=fake.future_date(end_date='+5y'),
                is_primary=False
            )
            payment_methods.append(pm)
    
    # Set the first method as primary
    if payment_methods:
        payment_methods[0].is_primary = True
    
    db.session.add_all(payment_methods)
    db.session.commit()
    return payment_methods


# ==========================
# DISCOUNT SEEDER
# ==========================
def create_discounts(products):
    print("🎁 Creating discounts...")
    discounts = []
    
    for i in range(50):
        discount = Discount(
            name=f"Discount {i+1}",
            description=fake.sentence(),
            discount_type=random.choice(['percentage', 'fixed']),
            discount_value=random.randint(5, 50),
            valid_from=fake.date_time_between(start_date='-30d', end_date='-15d'),
            valid_to=fake.date_time_between(start_date='+15d', end_date='+30d'),
            is_active_user=random.random() > 0.2,
            apply_to=random.choice(['all', 'categories', 'products']),
            min_order_value=round(random.uniform(50, 200), 2),
            max_discount=round(random.uniform(10, 100), 2),
            usage_limit=random.randint(50, 500)
        )
        db.session.add(discount)
        discounts.append(discount)
    
    db.session.commit()
    
    # Create product-discount relationships
    for discount in discounts:
        if discount.apply_to == 'products':
            for product in random.sample(products, random.randint(5, 20)):
                product_discount = ProductDiscount(
                    discount_id=discount.id,
                    product_id=product.id
                )
                db.session.add(product_discount)
    
    db.session.commit()
    return discounts

# ==========================
# COUPON SEEDER
# ==========================
def create_coupons():
    print("🎫 Creating coupons...")
    coupons = []
    
    for i in range(30):
        coupon = Coupon(
            code=f"SAVE{i+1}{fake.unique.lexify(text='??').upper()}",
            discount_type=random.choice(['percentage', 'fixed']),
            discount_value=random.randint(5, 30),
            valid_from=fake.date_time_between(start_date='-30d', end_date='-15d'),
            valid_to=fake.date_time_between(start_date='+15d', end_date='+30d'),
            usage_limit=random.randint(50, 500),
            min_order_value=round(random.uniform(50, 200), 2),
            max_discount=round(random.uniform(10, 50), 2),
            is_active_user=random.random() > 0.2,
            is_single_use=random.random() > 0.7
        )
        db.session.add(coupon)
        coupons.append(coupon)
    
    db.session.commit()
    return coupons

# ==========================
# CART ITEM SEEDER
# ==========================
def create_cart_items(customers, products):
    cart_items = []
    now = datetime.utcnow()
    seen_combinations = set()
    
    for customer in customers:
        num_items = random.randint(1, 5)
        selected_products = random.sample(products, num_items)
        
        for product in selected_products:
            # Remove variant selection since we don't have variants in Product model
            variant = None
            
            # Create a unique key for this combination
            combination_key = (customer.user_id, product.id, variant)
            
            # Skip if combination already exists
            if combination_key in seen_combinations:
                continue
                
            seen_combinations.add(combination_key)
            
            cart_item = CartItem(
                user_id=customer.user_id,
                product_id=product.id,
                quantity=random.randint(1, 3),
                added_at=now,
                updated_at=now,
                variant=variant  # Set to None
            )
            cart_items.append(cart_item)
    
    db.session.add_all(cart_items)
    db.session.commit()
    return cart_items

# ==========================
# WISHLIST ITEM SEEDER
# ==========================
def create_wishlist_items(customers, products):
    print("❤️ Creating wishlist items...")
    wishlist_items = []
    
    # Track which products each customer has already wishlisted
    customer_wishlists = {customer.id: set() for customer in customers}
    
    # Create wishlist items ensuring unique customer-product pairs
    for customer in customers:
        num_items = random.randint(1, 10)
        added_count = 0
        attempts = 0
        max_attempts = len(products) * 2  # Prevent infinite loops
        
        while added_count < num_items and attempts < max_attempts:
            product = random.choice(products)
            attempts += 1
            
            # Skip if customer already has this product in their wishlist
            if product.id in customer_wishlists[customer.id]:
                continue
                
            # Add to wishlist
            wishlist_item = WishlistItem(
                customer_id=customer.id,
                product_id=product.id,
                added_at=fake.date_time_this_year()
            )
            wishlist_items.append(wishlist_item)
            db.session.add(wishlist_item)
            customer_wishlists[customer.id].add(product.id)
            added_count += 1

    db.session.commit()
    print(f"✔️ Created {len(wishlist_items)} wishlist items.")
    return wishlist_items

# ==========================
# PRODUCT REVIEW SEEDER
# ==========================
def create_product_reviews(customers, products):
    print("⭐ Creating product reviews...")
    reviews = []
    
    for _ in range(NUM_REVIEWS):
        customer = random.choice(customers)
        product = random.choice(products)
        
        review = ProductReview(
            product_id=product.id,
            user_id=customer.user_id,
            rating=random.randint(1, 5),
            title=fake.sentence(),
            review=fake.text(max_nb_chars=200),
            is_approved=random.random() > 0.2
        )
        db.session.add(review)
        reviews.append(review)
    
    db.session.commit()
    print(f"✔️ Created {len(reviews)} product reviews.")
    return reviews

# ==========================
# PURCHASE ORDER SEEDER
# ==========================
def create_purchase_orders(vendors, products):
    print("📝 Creating purchase orders...")
    purchase_orders = []
    
    for _ in range(NUM_PURCHASE_ORDERS):
        vendor = random.choice(vendors)
        order_date = fake.date_time_between(start_date='-6m', end_date='now')
        
        po = PurchaseOrder(
            vendor_id=vendor.id,
            order_date=order_date,
            expected_delivery=order_date + timedelta(days=random.randint(7, 30)),
            status=random.choice(['PENDING', 'ORDERED', 'RECEIVED', 'CANCELLED']),
            total_amount=0.0
        )
        db.session.add(po)
        db.session.flush()
        purchase_orders.append(po)
        
        # Create PO items
        total = 0.0
        for _ in range(random.randint(1, 8)):
            product = random.choice(products)
            quantity = random.randint(10, 100)
            unit_cost = round(product.cost_price * random.uniform(0.8, 1.2), 2)
            total += quantity * unit_cost
            
            item = PurchaseOrderItem(
                po_id=po.id,
                product_id=product.id,
                quantity=quantity,
                unit_cost=unit_cost,
                received_quantity=quantity if po.status == 'RECEIVED' else 0
            )
            db.session.add(item)
            
            # Create inventory logs for received items
            if po.status == 'RECEIVED':
                inventory_log = InventoryLog(
                    product_id=product.id,
                    change=quantity,
                    description=f"Purchase Order #{po.po_number}",
                    reference_id=po.id,
                    reference_type='purchase',
                    user_id=random.choice([u.id for u in User.query.filter_by(role=RoleEnum.STAFF).all()])
                )
                db.session.add(inventory_log)
                
                # Update product stock
                product.stock_quantity += quantity
        
        po.total_amount = round(total, 2)
    
    db.session.commit()
    print(f"✔️ Created {len(purchase_orders)} purchase orders.")
    return purchase_orders

# ==========================
# SUPPORT TICKET SEEDER
# ==========================
def create_support_tickets(customers, orders):
    print("🆘 Creating support tickets...")
    tickets = []
    
    for _ in range(NUM_SUPPORT_TICKETS):
        customer = random.choice(customers)
        order = random.choice(orders) if orders and random.random() > 0.4 else None
        
        ticket = SupportTicket(
            user_id=customer.user_id,
            order_id=order.id if order else None,
            subject=fake.sentence(),
            description=fake.text(max_nb_chars=200),
            status=random.choice(['OPEN', 'IN_PROGRESS', 'CLOSED']),
            priority=random.choice(['LOW', 'MEDIUM', 'HIGH', 'URGENT']),
            created_at=fake.date_time_this_year()
        )
        db.session.add(ticket)
        db.session.flush()
        tickets.append(ticket)
        
        # Create support messages
        for _ in range(random.randint(1, 5)):
            user = random.choice([customer.user] + User.query.filter_by(role=RoleEnum.STAFF).all())
            message = SupportMessage(
                ticket_id=ticket.id,
                user_id=user.id,
                message=fake.text(max_nb_chars=100),
                is_internal=user.role != RoleEnum.CUSTOMER,
                created_at=fake.date_time_between(start_date=ticket.created_at, end_date='now')
            )
            db.session.add(message)
    
    db.session.commit()
    print(f"✔️ Created {len(tickets)} support tickets.")
    return tickets

# ==========================
# NOTIFICATION SEEDER
# ==========================
def create_notifications(customers, orders):
    print("🔔 Creating notifications...")
    notifications = []
    notification_types = list(NotificationType)
    
    for customer in customers:
        user = customer.user
        for _ in range(random.randint(3, 10)):
            order = random.choice(orders) if orders else None
            
            notification = Notification(
                user_id=user.id,
                type=random.choice(notification_types),
                message=fake.sentence(),
                is_read=random.random() > 0.5,
                link=fake.url(),
                related_id=order.id if order else None
            )
            db.session.add(notification)
            notifications.append(notification)
    
    db.session.commit()
    print(f"✔️ Created {len(notifications)} notifications.")
    return notifications

# ==============================
# MAIN SEED ENTRY POINT
# ==============================
def create_default_records(app):
    """
    Drops all existing tables and creates fresh default seed data.
    """
    with app.app_context():
        print("🧹 Dropping all tables...")
        db.drop_all()

        print("🧱 Creating all tables...")
        db.create_all()

        print("\n🌱 Starting seeding process...\n")
        
        categories = create_categories()
        vendors = create_vendors()
        products = create_products(categories, vendors)
        customers = create_users_and_customers()
        orders = create_orders(customers, products)
        discounts = create_discounts(products)
        coupons = create_coupons()
        cart_items = create_cart_items(customers, products)
        wishlist_items = create_wishlist_items(customers, products)
        reviews = create_product_reviews(customers, products)
        purchase_orders = create_purchase_orders(vendors, products)
        support_tickets = create_support_tickets(customers, orders)
        notifications = create_notifications(customers, orders)

        print("\n✅ Seeding Complete:")
        print(f" → Categories: {len(categories)}")
        print(f" → Vendors: {len(vendors)}")
        print(f" → Products: {len(products)}")
        print(f" → Customers: {len(customers)}")
        print(f" → Orders: {len(orders)}")
        print(f" → Discounts: {len(discounts)}")
        print(f" → Coupons: {len(coupons)}")
        print(f" → Cart Items: {len(cart_items)}")
        print(f" → Wishlist Items: {len(wishlist_items)}")
        print(f" → Product Reviews: {len(reviews)}")
        print(f" → Purchase Orders: {len(purchase_orders)}")
        print(f" → Support Tickets: {len(support_tickets)}")
        print(f" → Notifications: {len(notifications)}")
        print(f" → Admins: {NUM_ADMINS}, Staff: {NUM_STAFF}\n")

