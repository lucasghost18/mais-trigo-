from . import db
from datetime import datetime


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(120))
    address = db.Column(db.String(200))
    city = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    cnpj = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float, default=0.0)
