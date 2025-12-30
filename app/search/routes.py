from flask import Blueprint, request, jsonify, url_for

bp = Blueprint('search', __name__)

@bp.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '').lower()

    # Replace this dummy logic with real model lookups
    results = []
    if "prod" in query:
        results.append({
            "label": "Product ABC",
            "url": url_for('products.view_product', product_id=1)
        })
    if "order" in query:
        results.append({
            "label": "Order #1234",
            "url": url_for('orders.view_order', order_id=1234)
        })

    return jsonify(results)
