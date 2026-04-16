from . import db
from datetime import datetime


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(120))
    vendor = db.Column(db.String(120))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)
    vendor_obj = db.relationship('Vendor', backref='orders')
    notes = db.Column(db.Text)
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
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_obj = db.relationship('Product')
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float, default=0.0)


class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    manufacturer = db.Column(db.String(200))
    sku = db.Column(db.String(100))
    unit_price = db.Column(db.Float, default=0.0)
