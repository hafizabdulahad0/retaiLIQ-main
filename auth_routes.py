from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Store

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash("All fields required.", "warning")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        else:
            user = User(username=username,
                        password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            # log in as customer
            session['user_id'] = user.id
            session.pop('is_store_admin', None)
            flash("Logged in as customer.", "success")
            return redirect(url_for('store.list_stores'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')

@auth_bp.route('/store/register', methods=['GET','POST'])
def store_register():
    if Store.query.count() > 0:
        flash("Store signup closed.", "warning")
        return redirect(url_for('auth.store_login'))

    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password'].strip()
        s = request.form['store_name'].strip()
        if not u or not p or not s:
            flash("All fields required.", "warning")
        elif User.query.filter_by(username=u).first():
            flash("Username already taken.", "danger")
        elif Store.query.filter_by(name=s).first():
            flash("Store name already exists.", "danger")
        else:
            user = User(username=u, password_hash=generate_password_hash(p))
            store = Store(name=s)
            store.admins.append(user)
            db.session.add_all([user, store])
            db.session.commit()
            session['user_id']        = user.id
            session['is_store_admin'] = True
            session['store_id']       = store.id
            flash("Store & admin created. Welcome!", "success")
            return redirect(url_for('store.dashboard'))
    return render_template('store_register.html')

@auth_bp.route('/store/login', methods=['GET','POST'])
def store_login():
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password'].strip()
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password_hash, p) and user.stores:
            session['user_id']        = user.id
            session['is_store_admin'] = True
            session['store_id']       = user.stores[0].id
            flash("Logged in as store-admin.", "success")
            return redirect(url_for('store.dashboard'))
        flash("Invalid store credentials.", "danger")
    return render_template('store_login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('index'))
