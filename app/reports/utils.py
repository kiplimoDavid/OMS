from datetime import datetime, timedelta
from app.models import Order, OrderItem, Product

def get_sales_data(start_date=None, end_date=None):
    """Generate sales data for the given date range"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = Order.query.filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    )
    
    return {
        'total_orders': query.count(),
        'total_sales': sum(order.total_amount for order in query.all()),
        'orders': query.order_by(Order.order_date).all()
    }

def get_top_products(limit=5):
    """Get top selling products"""
    return db.session.query(
        Product.name,
        db.func.sum(OrderItem.quantity).label('total_quantity'),
        db.func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_revenue')
    ).join(OrderItem).group_by(Product.id).order_by(db.desc('total_revenue')).limit(limit).all()