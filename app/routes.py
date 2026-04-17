from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify
import os
import secrets
import re
from sqlalchemy import func
from . import db
from .models import Order, OrderItem, Vendor, Product
from .printers import print_order

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    # support optional search by order number via query param `q`
    q = request.args.get('q')
    if q:
        try:
            order_id = int(q)
            orders = Order.query.filter_by(id=order_id).order_by(Order.created_at.desc()).all()
        except ValueError:
            flash('Número de pedido inválido', 'warning')
            orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
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


@bp.route('/orders/search')
def orders_search():
    # return only the orders list HTML fragment for AJAX search
    q = request.args.get('q')
    if q:
        try:
            order_id = int(q)
            orders = Order.query.filter_by(id=order_id).order_by(Order.created_at.desc()).all()
        except ValueError:
            orders = []
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    outdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    if not os.path.isabs(outdir):
        outdir = os.path.join(current_app.root_path, outdir)
    exists_map = {}
    for o in orders:
        exists_map[o.id] = {
            'txt': os.path.exists(os.path.join(outdir, f'order_{o.id}.txt')),
            'pdf': os.path.exists(os.path.join(outdir, f'order_{o.id}.pdf')),
        }
    return render_template('_orders_list.html', orders=orders, exists_map=exists_map)


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
            uw = request.form.get(f'unit_weight-{i}')
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
                        try:
                            weight = float(uw) if uw else float(p.weight or 0.0)
                        except:
                            weight = float(p.weight or 0.0)
                        items.append({'product': product_name, 'product_id': pid, 'quantity': q, 'unit_price': price, 'unit_weight': weight})
                    else:
                        # unknown id, fallback to text
                        try:
                            price = float(up) if up else 0.0
                        except:
                            price = 0.0
                        try:
                            weight = float(uw) if uw else 0.0
                        except:
                            weight = 0.0
                        items.append({'product': prod_text or '', 'product_id': None, 'quantity': q, 'unit_price': price, 'unit_weight': weight})
                else:
                    try:
                        price = float(up) if up else 0.0
                    except:
                        price = 0.0
                    try:
                        weight = float(uw) if uw else 0.0
                    except:
                        weight = 0.0
                    items.append({'product': prod_text or '', 'product_id': None, 'quantity': q, 'unit_price': price, 'unit_weight': weight})

        order = Order(customer=customer, vendor=vendor, notes=notes, address=address, city=city, phone=phone, cnpj=cnpj)
        if vendor_id:
            try:
                order.vendor_id = int(vendor_id)
            except:
                pass
        db.session.add(order)
        db.session.flush()
        for it in items:
            db.session.add(OrderItem(order_id=order.id, product=it['product'], product_id=it.get('product_id'), quantity=it['quantity'], unit_price=it.get('unit_price', 0.0), unit_weight=it.get('unit_weight', 0.0)))
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
    # serialize products for JSON usage in template
    products_data = [
        {
            'id': p.id,
            'name': p.name,
            'unit_price': float(p.unit_price or 0.0),
            'weight': float(p.weight or 0.0),
            'sku': p.sku or '',
            'manufacturer': p.manufacturer or ''
        }
        for p in products
    ]
    return render_template('new_order.html', vendors=vendors, products=products_data)


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
        name = (request.form.get('name') or '').strip()
        manufacturer = (request.form.get('manufacturer') or '').strip()
        sku = (request.form.get('sku') or '').strip()
        try:
            weight = float(request.form.get('weight') or 0.0)
        except:
            weight = 0.0
        try:
            price = float(request.form.get('unit_price') or 0.0)
        except:
            price = 0.0

        # If sku not provided, generate one based on manufacturer
        if not sku:
            prefix = 'PRD'
            if manufacturer:
                prefix = ''.join(ch for ch in manufacturer if ch.isalnum()).upper()[:3] or 'PRD'
            attempts = 0
            while True:
                candidate = f"{prefix}-{secrets.token_hex(3).upper()}"
                if not Product.query.filter_by(sku=candidate).first():
                    sku = candidate
                    break
                attempts += 1
                if attempts > 5:
                    sku = f"{prefix}-{secrets.token_hex(4).upper()}"
                    break

        # server-side uniqueness check
        existing = Product.query.filter_by(sku=sku).first()
        if existing:
            flash('Código de referência (SKU) já existe. Escolha outro ou deixe em branco para gerar aleatório.', 'danger')
            form = {'name': name, 'manufacturer': manufacturer, 'sku': sku, 'unit_price': price}
            return render_template('product_form.html', form=form)

        p = Product(name=name, sku=sku, unit_price=price, manufacturer=manufacturer, weight=weight)
        try:
            db.session.add(p)
            db.session.commit()
            flash('Produto criado com sucesso', 'success')
            return redirect(url_for('main.products'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erro ao salvar produto: %s', e)
            flash('Erro ao salvar produto.', 'danger')
            form = {'name': name, 'manufacturer': manufacturer, 'sku': sku, 'unit_price': price, 'weight': weight}
            return render_template('product_form.html', form=form)
    return render_template('product_form.html')


@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        manufacturer = (request.form.get('manufacturer') or '').strip()
        sku = (request.form.get('sku') or '').strip()
        try:
            weight = float(request.form.get('weight') or 0.0)
        except:
            weight = 0.0
        try:
            price = float(request.form.get('unit_price') or 0.0)
        except:
            price = 0.0

        # If sku blank, generate one
        if not sku:
            prefix = 'PRD'
            if manufacturer:
                prefix = ''.join(ch for ch in manufacturer if ch.isalnum()).upper()[:3] or 'PRD'
            attempts = 0
            while True:
                candidate = f"{prefix}-{secrets.token_hex(3).upper()}"
                if not Product.query.filter_by(sku=candidate).first():
                    sku = candidate
                    break
                attempts += 1
                if attempts > 5:
                    sku = f"{prefix}-{secrets.token_hex(4).upper()}"
                    break

        # uniqueness check excluding self
        existing = Product.query.filter_by(sku=sku).first()
        if existing and existing.id != product.id:
            flash('Código de referência (SKU) já existe em outro produto.', 'danger')
            return render_template('product_form.html', product=product)

        product.name = name
        product.manufacturer = manufacturer
        product.sku = sku
        product.weight = weight
        product.unit_price = price
        try:
            db.session.commit()
            flash('Produto atualizado com sucesso', 'success')
            return redirect(url_for('main.products'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erro ao atualizar produto: %s', e)
            flash('Erro ao atualizar produto.', 'danger')
            return render_template('product_form.html', product=product)
    return render_template('product_form.html', product=product)


@bp.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # prevent deletion if used in order items
    used = OrderItem.query.filter_by(product_id=product_id).count()
    if used:
        flash('Não é possível excluir: produto está associado a pedidos.', 'danger')
        return redirect(url_for('main.products'))
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Produto removido com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover produto: {e}', 'danger')
    return redirect(url_for('main.products'))


@bp.route('/vendors/<int:vendor_id>/edit', methods=['GET', 'POST'])
def edit_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if request.method == 'POST':
        vendor.name = request.form.get('name')
        vendor.phone = request.form.get('phone')
        vendor.email = request.form.get('email')
        try:
            db.session.commit()
            flash('Vendedor atualizado com sucesso', 'success')
            return redirect(url_for('main.vendors'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erro ao atualizar vendedor: %s', e)
            flash('Erro ao atualizar vendedor.', 'danger')
            return render_template('vendor_form.html', vendor=vendor)
    return render_template('vendor_form.html', vendor=vendor)


@bp.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    used = Order.query.filter_by(vendor_id=vendor_id).count()
    if used:
        flash('Não é possível excluir: vendedor está associado a pedidos.', 'danger')
        return redirect(url_for('main.vendors'))
    try:
        db.session.delete(vendor)
        db.session.commit()
        flash('Vendedor removido com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover vendedor: {e}', 'danger')
    return redirect(url_for('main.vendors'))


@bp.route('/orders/<int:order_id>/print', methods=['POST'])
def order_print(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        method = request.form.get('print_method')
        filename = print_order(order, method=method)
        if method == 'pdf':
            flash(f'PDF gerado: {filename}', 'success')
            return redirect(url_for('main.prints', filename=filename))
        else:
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


@bp.route('/products/search')
def products_search():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    # search by SKU, name or manufacturer (case-insensitive)
    term = f"%{q}%"
    # also try matching SKU when user types without punctuation (e.g. ABC123 -> ABC-123)
    q_plain = re.sub(r'[^A-Za-z0-9]', '', q)
    term_plain = f"%{q_plain}%"
    try:
        # build SKU replace expression to strip common punctuation
        sku_replace = func.replace(func.replace(func.replace(func.replace(Product.sku, '-', ''), ' ', ''), '/', ''), '.', '')
        filters = (Product.sku.ilike(term)) | (Product.name.ilike(term)) | (Product.manufacturer.ilike(term))
        if q_plain:
            filters = filters | sku_replace.ilike(term_plain)
        matches = Product.query.filter(filters).order_by(Product.name).limit(50).all()
    except Exception:
        # fallback for DBs without ilike
        sku_replace = func.replace(func.replace(func.replace(func.replace(Product.sku, '-', ''), ' ', ''), '/', ''), '.', '')
        filters = (Product.sku.like(term)) | (Product.name.like(term)) | (Product.manufacturer.like(term))
        if q_plain:
            filters = filters | sku_replace.like(term_plain)
        matches = Product.query.filter(filters).order_by(Product.name).limit(50).all()

    results = []
    for p in matches:
        results.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku or '',
            'manufacturer': p.manufacturer or '',
            'unit_price': float(p.unit_price or 0.0)
        })
    return jsonify(results)
