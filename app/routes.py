from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from . import db
from .models import Order, OrderItem
from .printers import print_order

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('index.html', orders=orders)


@bp.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        customer = request.form.get('customer', 'Cliente')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        phone = request.form.get('phone', '')
        cnpj = request.form.get('cnpj', '')
        try:
            item_count = int(request.form.get('item-count', 0))
        except ValueError:
            item_count = 0
        items = []
        for i in range(item_count):
            prod = request.form.get(f'product-{i}')
            qty = request.form.get(f'quantity-{i}')
            up = request.form.get(f'unit_price-{i}')
            if prod and qty:
                try:
                    q = int(qty)
                except:
                    q = 0
                try:
                    price = float(up) if up else 0.0
                except:
                    price = 0.0
                items.append({'product': prod, 'quantity': q, 'unit_price': price})

        order = Order(customer=customer, address=address, city=city, phone=phone, cnpj=cnpj)
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(order_id=order.id, product=it['product'], quantity=it['quantity'], unit_price=it.get('unit_price', 0.0)))
        db.session.commit()
        flash('Pedido criado com sucesso', 'success')
        return redirect(url_for('main.index'))
    return render_template('new_order.html')


@bp.route('/orders/<int:order_id>/print', methods=['POST'])
def order_print(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        filename = print_order(order)
        flash(f'Enviado para impressora: {filename}', 'success')
    except Exception as e:
        flash(f'Erro na impressão: {e}', 'danger')
    return redirect(url_for('main.index'))


@bp.route('/prints/<path:filename>')
def prints(filename):
    pdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    return send_from_directory(pdir, filename)
