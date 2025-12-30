@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip().lower()
    # Perform search logic here
    # Example:
    results = [{'label': 'Product A', 'url': url_for('products.view_product', id=1)},
               {'label': 'Order #1234', 'url': url_for('orders.view_order', id=1234)}]
    return jsonify(results)
