from flask import Blueprint, session, redirect, url_for, flash, request, render_template
from models import Product

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    pid = request.form.get('product_id')
    price = request.form.get('price')
    if not pid or not price:
        flash("Add to cart failed.", "danger")
        return redirect(request.referrer or url_for('product.list_products'))
    cart = session.get('cart', [])
    cart.append({'product_id':int(pid), 'price':float(price)})
    session['cart'] = cart
    flash("Added to cart.", "success")
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    idx = request.form.get('index')
    cart = session.get('cart', [])
    try:
        i = int(idx)
        if 0 <= i < len(cart):
            cart.pop(i)
            session['cart']=cart
            flash("Removed from cart.", "info")
    except:
        flash("Remove failed.", "danger")
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    items=[]; total=0.0
    for e in cart:
        p=Product.query.get(e['product_id'])
        if p:
            items.append({'product':p,'price':e['price']})
            total+=e['price']
    return render_template('cart.html', items=items, total=total)
