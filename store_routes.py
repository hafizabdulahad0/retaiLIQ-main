from flask import (
    Blueprint, render_template, redirect, url_for,
    session, abort, flash, request
)
from werkzeug.security import generate_password_hash
from models import db, User, Store, Product, ChatSession, Message, Order

store_bp = Blueprint('store', __name__)

def require_store_admin():
    if not session.get('is_store_admin'):
        abort(403)
    return Store.query.get_or_404(session['store_id'])


@store_bp.route('/stores')
def list_stores():
    stores = Store.query.all()
    return render_template('store_list.html', stores=stores)


@store_bp.route('/store/dashboard')
def dashboard():
    store = require_store_admin()

    # Product count + Recent orders
    prod_count    = len(store.products)
    recent_orders = (
        Order.query
             .filter_by(store_id=store.id)
             .order_by(Order.timestamp.desc())
             .limit(10)
             .all()
    )

    # Session categories
    ai_sessions = (
        ChatSession.query.join(Product)
                   .filter(
                       Product.store_id==store.id,
                       ChatSession.active==True,
                       ChatSession.handed_to_human==False
                   )
                   .all()
    )
    human_sessions = (
        ChatSession.query.join(Product)
                   .filter(
                       Product.store_id==store.id,
                       ChatSession.active==True,
                       ChatSession.handed_to_human==True
                   )
                   .all()
    )
    ended_sessions = (
        ChatSession.query.join(Product)
                   .filter(
                       Product.store_id==store.id,
                       ChatSession.active==False
                   )
                   .order_by(ChatSession.created_at.desc())
                   .all()
    )

    return render_template(
        'store_dashboard.html',
        store=store,
        prod_count=prod_count,
        recent_orders=recent_orders,
        ai_sessions=ai_sessions,
        human_sessions=human_sessions,
        ended_sessions=ended_sessions
    )


@store_bp.route('/store/chat/terminate/<int:session_id>')
def terminate_session(session_id):
    store = require_store_admin()
    cs = ChatSession.query.get_or_404(session_id)
    if cs.product.store_id != store.id:
        abort(403)

    cs.active = False
    cs.handed_to_human = True
    db.session.add(Message(
        session_id=cs.id,
        role='system',
        content="**Chat terminated by store admin.**"
    ))
    db.session.commit()
    flash("Chat terminated; human will take over.", "info")
    return redirect(url_for('store.dashboard'))


@store_bp.route('/store/chat/view/<int:session_id>')
def watch_chat(session_id):
    store = require_store_admin()
    cs = ChatSession.query.get_or_404(session_id)
    if cs.product.store_id != store.id:
        abort(403)

    messages = (
        Message.query
               .filter_by(session_id=cs.id)
               .order_by(Message.timestamp)
               .all()
    )

    return render_template(
        'store_watch_chat.html',
        chat_session=cs,
        messages=messages
    )


@store_bp.route('/store/chat/override/<int:session_id>', methods=['POST'])
def override_price(session_id):
    """
    Admin override: set cs.current_price exactly as entered (no clamp),
    mark handed_to_human so AI stops, and notify customer via price update only.
    """
    store = require_store_admin()
    cs = ChatSession.query.get_or_404(session_id)
    if cs.product.store_id != store.id:
        abort(403)

    # Parse override (no floor clamp)
    try:
        raw = request.form['override_price'].strip()
        new_price = round(float(raw), 2)
    except (KeyError, ValueError):
        flash("Please enter a valid price.", "danger")
        return redirect(url_for('store.watch_chat', session_id=session_id))

    # Apply override
    cs.current_price   = new_price
    cs.handed_to_human = True
    db.session.commit()

    flash(f"Price overridden to ${new_price:.2f}. Customer will see the updated price.", "success")
    return redirect(url_for('store.watch_chat', session_id=session_id))


@store_bp.route('/store/chat/view/<int:session_id>/send', methods=['POST'])
def send_admin_message(session_id):
    """
    Admin free-form message: inject it as if the assistant sent it,
    so the customer sees it in the same chat flow.
    """
    store = require_store_admin()
    cs = ChatSession.query.get_or_404(session_id)
    if cs.product.store_id != store.id:
        abort(403)

    text = request.form.get('message', '').strip()
    if text:
        cs.handed_to_human = True
        # Save as assistant so it renders like a bot message
        db.session.add(Message(session_id=cs.id, role='assistant', content=text))
        db.session.commit()
        flash("Your message has been sent to the customer.", "success")

    return redirect(url_for('store.watch_chat', session_id=session_id))


@store_bp.route('/store/admins/add', methods=['GET','POST'])
def add_admin():
    store = require_store_admin()
    if request.method == 'POST':
        uname = request.form['username'].strip()
        pwd   = request.form['password'].strip()
        if not uname or not pwd:
            flash("All fields are required.", "warning")
        elif User.query.filter_by(username=uname).first():
            flash("Username already exists.", "danger")
        else:
            user = User(username=uname, password_hash=generate_password_hash(pwd))
            store.admins.append(user)
            db.session.add(user)
            db.session.commit()
            flash("New store-admin added.", "success")
            return redirect(url_for('store.dashboard'))
    return render_template('add_store_admin.html', store=store)
