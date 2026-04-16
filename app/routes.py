from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
import os
from . import db
from .models import Order, OrderItem, Vendor, Product
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
        # vendor may be provided as vendor_id (select) or free text
        vendor = request.form.get('vendor', '')
        vendor_id = request.form.get('vendor_id')
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
            prod_id = request.form.get(f'product_id-{i}')
            qty = request.form.get(f'quantity-{i}')
            up = request.form.get(f'unit_price-{i}')
            # fallback to free-text product name
            prod_text = request.form.get(f'product-{i}')
            if qty:
                try:
                    q = int(qty)
                except:
                    q = 0
                # resolve product by id if provided
                pid = None
                if prod_id:
                    try:
                        pid = int(prod_id)
                    except:
                        pid = None
                if pid:
                    p = Product.query.get(pid)
                    if p:
                        product_name = p.name
                        try:
                            price = float(up) if up else float(p.unit_price or 0.0)
                        except:
                            price = float(p.unit_price or 0.0)
                        items.append({'product': product_name, 'product_id': pid, 'quantity': q, 'unit_price': price})
                    else:
                        # unknown id, fallback to text
                        try:
                            price = float(up) if up else 0.0
                        except:
                            price = 0.0
                        items.append({'product': prod_text or '', 'product_id': None, 'quantity': q, 'unit_price': price})
                else:
                    try:
                        price = float(up) if up else 0.0
                    except:
                        price = 0.0
                    items.append({'product': prod_text or '', 'product_id': None, 'quantity': q, 'unit_price': price})

        order = Order(customer=customer, vendor=vendor, notes=notes, address=address, city=city, phone=phone, cnpj=cnpj)
        if vendor_id:
            try:
                order.vendor_id = int(vendor_id)
            except:
                pass
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(order_id=order.id, product=it['product'], product_id=it.get('product_id'), quantity=it['quantity'], unit_price=it.get('unit_price', 0.0)))
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
    # GET: provide vendors and products for selection
    vendors = Vendor.query.order_by(Vendor.name).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('new_order.html', vendors=vendors, products=products)


@bp.route('/vendors')
def vendors():
    vs = Vendor.query.order_by(Vendor.name).all()
    return render_template('vendors.html', vendors=vs)


@bp.route('/vendors/new', methods=['GET', 'POST'])
def new_vendor():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        v = Vendor(name=name, phone=phone, email=email)
        db.session.add(v)
        db.session.commit()
        flash('Vendedor criado com sucesso', 'success')
        return redirect(url_for('main.vendors'))
    return render_template('vendor_form.html')


@bp.route('/products')
def products():
    ps = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=ps)


@bp.route('/products/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku')
        try:
            price = float(request.form.get('unit_price') or 0.0)
        except:
            price = 0.0
        p = Product(name=name, sku=sku, unit_price=price)
        db.session.add(p)
        db.session.commit()
        flash('Produto criado com sucesso', 'success')
        return redirect(url_for('main.products'))
    return render_template('product_form.html')


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
