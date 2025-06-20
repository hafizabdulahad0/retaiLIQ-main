from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
from models import db, Store, Product

product_bp = Blueprint('product', __name__)

@product_bp.route('/store/<int:store_id>/products')
def list_products(store_id):
    store = Store.query.get_or_404(store_id)
    products = Product.query.filter_by(store_id=store_id).all()
    return render_template('products.html', products=products, store=store)

@product_bp.route('/store/<int:store_id>/products/new', methods=['GET','POST'])
def add_product(store_id):
    store = Store.query.get_or_404(store_id)
    if not session.get('is_store_admin') or session.get('store_id')!=store_id:
        abort(403)
    if request.method=='POST':
        name         = request.form['name'].strip()
        price        = float(request.form['price'])
        max_disc     = float(request.form['max_discount'])
        description  = request.form.get('description','').strip()
        justification= request.form.get('justification','').strip()
        other_disc   = request.form.get('other_discounts','').strip()

        prod = Product(
            name=name,
            price=price,
            max_discount=max_disc,
            description=description,
            justification=justification,
            other_discounts=other_disc,
            store_id=store_id
        )
        db.session.add(prod)
        db.session.commit()
        flash(f"Product '{name}' added.", "success")
        return redirect(url_for('store.dashboard'))

    return render_template('new_product.html', store=store)

@product_bp.route('/store/<int:store_id>/products/<int:product_id>/edit', methods=['GET','POST'])
def edit_product(store_id, product_id):
    store = Store.query.get_or_404(store_id)
    if not session.get('is_store_admin') or session.get('store_id')!=store_id:
        abort(403)
    prod = Product.query.get_or_404(product_id)
    if request.method=='POST':
        prod.name            = request.form['name'].strip()
        prod.price           = float(request.form['price'])
        prod.max_discount    = float(request.form['max_discount'])
        prod.description     = request.form.get('description','').strip()
        prod.justification   = request.form.get('justification','').strip()
        prod.other_discounts = request.form.get('other_discounts','').strip()
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for('store.dashboard'))
    return render_template('edit_product.html', store=store, product=prod)

@product_bp.route('/store/<int:store_id>/products/<int:product_id>/delete', methods=['POST'])
def delete_product(store_id, product_id):
    store = Store.query.get_or_404(store_id)
    if not session.get('is_store_admin') or session.get('store_id')!=store_id:
        abort(403)
    prod = Product.query.get_or_404(product_id)
    db.session.delete(prod)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for('store.dashboard'))
