from flask import render_template, request
from flask_login import login_required
from app.models import Order
from app.reports import bp
from datetime import datetime, timedelta

@bp.route('/sales')
@login_required
def sales_report():
    # Default to last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()
    
    orders = Order.query.filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date
    ).order_by(Order.order_date.desc()).all()
    
    total_sales = sum(o.total_amount for o in orders)
    avg_order_value = total_sales / len(orders) if orders else 0
    
    return render_template(
        'reports/sales.html',
        orders=orders,
        total_sales=total_sales,
        avg_order_value=avg_order_value,
        start_date=start_date.date(),
        end_date=end_date.date()
    )

@bp.route('/sales/full', methods=['GET'])
@login_required
def full_sales_report():
    # Accept optional date filters via querystring
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    
    try:
        start = datetime.fromisoformat(start_str) if start_str else datetime.utcnow() - timedelta(days=365)
    except ValueError:
        start = datetime.utcnow() - timedelta(days=365)
    try:
        end = datetime.fromisoformat(end_str) if end_str else datetime.utcnow()
    except ValueError:
        end = datetime.utcnow()
    
    orders = Order.query.filter(
        Order.order_date >= start,
        Order.order_date <= end
    ).order_by(Order.order_date.desc()).all()
    
    total_amount = sum(o.total_amount for o in orders)
    total_count = len(orders)
    
    return render_template(
        'reports/full_report.html',
        orders=orders,
        total_amount=total_amount,
        total_count=total_count,
        start=start.date(),
        end=end.date()
    )
