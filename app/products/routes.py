from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Product
from app.products import bp
from app.products.forms import ProductForm
from app.admin.routes import admin_required
@bp.route('/')
def list_products():
    products = Product.query.order_by(Product.name).all()
    return render_template('products/list.html', products=products)

@bp.route('/<int:product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('products/view.html', product=product)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock_quantity=form.stock_quantity.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/add.html', form=form)

@bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products.view_product', product_id=product.id))
    return render_template('products/edit.html', form=form, product=product)