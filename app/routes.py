from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
import os
from . import db
from .models import Order, OrderItem
from .printers import print_order

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    outdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    # ensure absolute path
    if not os.path.isabs(outdir):
        outdir = os.path.join(current_app.root_path, outdir)
    exists_map = {}
    for o in orders:
        exists_map[o.id] = {
            'txt': os.path.exists(os.path.join(outdir, f'order_{o.id}.txt')),
            'pdf': os.path.exists(os.path.join(outdir, f'order_{o.id}.pdf')),
        }
    return render_template('index.html', orders=orders, exists_map=exists_map)


@bp.route('/orders/new', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        customer = request.form.get('customer', 'Cliente')
        vendor = request.form.get('vendor', '')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        phone = request.form.get('phone', '')
        cnpj = request.form.get('cnpj', '')
        notes = request.form.get('notes', '')
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

        order = Order(customer=customer, vendor=vendor, notes=notes, address=address, city=city, phone=phone, cnpj=cnpj)
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(order_id=order.id, product=it['product'], quantity=it['quantity'], unit_price=it.get('unit_price', 0.0)))
        db.session.commit()
        # gerar arquivo de impressão automaticamente conforme opção do formulário
        print_method = request.form.get('print_method')
        try:
            filename = print_order(order, method=print_method)
            flash(f'Pedido criado e arquivo gerado: {filename}', 'success')
        except Exception as e:
            current_app.logger.exception('Erro ao gerar impressão: %s', e)
            flash('Pedido criado com sucesso. Falha ao gerar arquivo de impressão.', 'warning')
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


@bp.route('/orders/<int:order_id>/delete', methods=['POST'])
def order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        db.session.delete(order)
        db.session.commit()
        flash('Pedido removido com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover pedido: {e}', 'danger')
    return redirect(url_for('main.index'))


@bp.route('/prints/<path:filename>')
def prints(filename):
    pdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    if not os.path.isabs(pdir):
        pdir = os.path.join(current_app.root_path, pdir)
    return send_from_directory(pdir, filename)
