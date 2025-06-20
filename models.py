from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# association table for store ↔ admins
store_admins = db.Table(
    'store_admins',
    db.Column('store_id', db.Integer, db.ForeignKey('store.id'), primary_key=True),
    db.Column('user_id',  db.Integer, db.ForeignKey('user.id'),  primary_key=True),
)

class User(db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    stores        = db.relationship('Store', secondary=store_admins, back_populates='admins')
    sessions      = db.relationship('ChatSession', back_populates='user', lazy=True)
    orders        = db.relationship('Order', back_populates='user', lazy=True)

class Store(db.Model):
    __tablename__ = 'store'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(150), unique=True, nullable=False)
    admins   = db.relationship('User', secondary=store_admins, back_populates='stores')
    products = db.relationship('Product', back_populates='store', lazy=True)
    orders   = db.relationship('Order', back_populates='store', lazy=True)

class Product(db.Model):
    __tablename__ = 'product'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(150), nullable=False)
    price           = db.Column(db.Float, nullable=False)
    max_discount    = db.Column(db.Float, nullable=False)
    description     = db.Column(db.Text,    nullable=True)
    justification   = db.Column(db.Text,    nullable=True)
    other_discounts = db.Column(db.Text,    nullable=True)
    store_id        = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store           = db.relationship('Store', back_populates='products')
    sessions        = db.relationship('ChatSession', back_populates='product', lazy=True)

class ChatSession(db.Model):
    __tablename__   = 'chat_session'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'),   nullable=False)
    product_id      = db.Column(db.Integer, db.ForeignKey('product.id'),nullable=False)
    active          = db.Column(db.Boolean, default=True)
    handed_to_human = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    user            = db.relationship('User',    back_populates='sessions', lazy=True)
    product         = db.relationship('Product', back_populates='sessions', lazy=True)
    messages        = db.relationship('Message', back_populates='session', lazy=True)
    current_price = db.Column(db.Float, nullable=False)


class Message(db.Model):
    __tablename__ = 'message'
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role       = db.Column(db.String(10), nullable=False)   # 'user','assistant','admin','system'
    content    = db.Column(db.Text,        nullable=False)
    timestamp  = db.Column(db.DateTime,    server_default=db.func.current_timestamp(), nullable=False)
    session    = db.relationship('ChatSession', back_populates='messages', lazy=True)

class Order(db.Model):
    __tablename__   = 'order'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    store_id        = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    total_amount    = db.Column(db.Float, nullable=False)
    timestamp       = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    user            = db.relationship('User',  back_populates='orders', lazy=True)
    store           = db.relationship('Store', back_populates='orders', lazy=True)
