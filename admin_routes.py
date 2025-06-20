from flask import Blueprint, render_template, session, abort, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from models import db, User, Product, ChatSession, Message

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('is_admin'):
        abort(403)
    total_products = Product.query.count()
    ongoing_chats  = ChatSession.query.filter_by(active=True).count()

    # Stats per product
    product_stats = []
    for p in Product.query.all():
        total = ChatSession.query.filter_by(product_id=p.id).count()
        active = ChatSession.query.filter_by(product_id=p.id, active=True).count()
        product_stats.append((p, total, active))

    # Active chat sessions
    active_sessions = ChatSession.query.filter_by(active=True).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           ongoing_chats=ongoing_chats,
                           product_stats=product_stats,
                           active_sessions=active_sessions)

@admin_bp.route('/chat/terminate/<int:session_id>')
def terminate_chat(session_id):
    if not session.get('is_admin'):
        abort(403)
    cs = ChatSession.query.get_or_404(session_id)
    cs.active = False
    cs.handed_to_human = True
    # Log system message
    sys_msg = Message(
        session_id=session_id,
        role='system',
        content="**Chat terminated by admin — human will take over.**"
    )
    db.session.add(sys_msg)
    db.session.commit()
    flash("Chat terminated; human support will take over.", "info")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/add', methods=['GET', 'POST'])
def add_admin():
    if not session.get('is_admin'):
        abort(403)
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash("All fields are required.", "warning")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        else:
            new_admin = User(
                username=username,
                password_hash=generate_password_hash(password),
                is_admin=True
            )
            db.session.add(new_admin)
            db.session.commit()
            flash("New admin account created.", "success")
            return redirect(url_for('admin.dashboard'))
    return render_template('add_admin.html')
