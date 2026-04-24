from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify, session
import os
import secrets
import re
from functools import wraps
from datetime import datetime
from sqlalchemy import func
from . import db
from .models import Order, OrderItem, Vendor, Product, User
from .printers import print_order, print_delivery_pdf

bp = Blueprint('main', __name__)

VALID_USERNAME = 'mais vendas'
VALID_PASSWORD = '3341'


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('main.login'))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        if not is_admin():
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return view(**kwargs)
    return wrapped_view


def is_admin():
    return session.get('role') == 'admin'


def get_current_vendor_id():
    return session.get('vendor_id')


def _build_orders_query():
    """Return base order query filtered by current user role."""
    q = request.args.get('q')
    query = Order.query
    if q:
        q = q.strip()
        try:
            order_id = int(q)
            query = query.filter_by(id=order_id)
        except ValueError:
            # For admin, also search by customer or vendor name
            if is_admin():
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Order.customer.ilike(f'%{q}%'),
                        Order.vendor.ilike(f'%{q}%')
                    )
                )
    if not is_admin():
        vid = get_current_vendor_id()
        if vid:
            query = query.filter_by(vendor_id=vid)
    return query.order_by(Order.created_at.desc())


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        # Try database user first
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['logged_in'] = True
            session['username'] = user.username
            session['role'] = user.role
            session['vendor_id'] = user.vendor_id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        # Fallback to hardcoded admin for backward compatibility
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin'
            session['vendor_id'] = None
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.login'))


@bp.route('/')
@login_required
def index():
    orders = _build_orders_query().all()
    if request.args.get('q'):
        try:
            int(request.args.get('q'))
        except ValueError:
            flash('Número de pedido inválido', 'warning')
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
@login_required
def orders_search():
    # return only the orders list HTML fragment for AJAX search
    orders = _build_orders_query().all()
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
@login_required
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
        # if logged in as vendor, force assign own vendor_id
        if not is_admin():
            vid = get_current_vendor_id()
            if vid:
                order.vendor_id = vid
                v = Vendor.query.get(vid)
                if v:
                    order.vendor = v.name
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
    return render_template('new_order.html', vendors=vendors, products=products_data, is_admin=is_admin(), current_vendor_id=get_current_vendor_id())


@bp.route('/vendors')
@login_required
def vendors():
    vs = Vendor.query.order_by(Vendor.name).all()
    return render_template('vendors.html', vendors=vs, is_admin=is_admin())


@bp.route('/vendors/new', methods=['GET', 'POST'])
@admin_required
def new_vendor():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        auto_password = request.form.get('auto_password')
        if not username:
            flash('Nome de usuário é obrigatório.', 'danger')
            return render_template('vendor_form.html', form=request.form)
        if auto_password:
            password = secrets.token_urlsafe(8)
        if not password:
            flash('Senha é obrigatória (ou marque a opção de gerar automaticamente).', 'danger')
            return render_template('vendor_form.html', form=request.form)
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe. Escolha outro.', 'danger')
            return render_template('vendor_form.html', form=request.form)
        v = Vendor(name=name, phone=phone, email=email)
        db.session.add(v)
        db.session.flush()  # get v.id before commit
        u = User(username=username, password=password, role='vendor', vendor_id=v.id)
        db.session.add(u)
        db.session.commit()
        flash(f'Vendedor criado com sucesso. Usuário de acesso: {username} / Senha: {password}', 'success')
        return redirect(url_for('main.vendors'))
    return render_template('vendor_form.html')


@bp.route('/products')
@login_required
def products():
    ps = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=ps, is_admin=is_admin())

@bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def edit_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    if request.method == 'POST':
        vendor.name = request.form.get('name')
        vendor.phone = request.form.get('phone')
        vendor.email = request.form.get('email')
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            u = User.query.filter_by(vendor_id=vendor.id).first()
            if u:
                u.password = new_password
        try:
            db.session.commit()
            flash('Vendedor atualizado com sucesso', 'success')
            return redirect(url_for('main.vendors'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception('Erro ao atualizar vendedor: %s', e)
            flash('Erro ao atualizar vendedor.', 'danger')
            return render_template('vendor_form.html', vendor=vendor)
    user = User.query.filter_by(vendor_id=vendor.id).first()
    return render_template('vendor_form.html', vendor=vendor, user=user)


@bp.route('/vendors/<int:vendor_id>/delete', methods=['POST'])
@admin_required
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    used = Order.query.filter_by(vendor_id=vendor_id).count()
    if used:
        flash('Não é possível excluir: vendedor está associado a pedidos.', 'danger')
        return redirect(url_for('main.vendors'))
    try:
        # remove associated user first
        u = User.query.filter_by(vendor_id=vendor.id).first()
        if u:
            db.session.delete(u)
        db.session.delete(vendor)
        db.session.commit()
        flash('Vendedor removido com sucesso', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover vendedor: {e}', 'danger')
    return redirect(url_for('main.vendors'))


@bp.route('/orders/<int:order_id>/print', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def prints(filename):
    pdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    if not os.path.isabs(pdir):
        pdir = os.path.join(current_app.root_path, pdir)
    return send_from_directory(pdir, filename)


@bp.route('/carga')
@admin_required
def carga():
    """Tela de controle de cargas (admin). Exibe pedidos filtrados com totais por vendedor."""
    vendor_id = request.args.get('vendor_id', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Order.query
    if vendor_id:
        try:
            query = query.filter_by(vendor_id=int(vendor_id))
        except ValueError:
            pass
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d')
            # ajusta para o final do dia
            dt_to = datetime.combine(dt_to.date(), datetime.time(23, 59, 59))
            query = query.filter(Order.created_at <= dt_to)
        except ValueError:
            pass

    orders = query.order_by(Order.created_at.desc()).all()

    # totais gerais
    total_valor = 0.0
    total_peso = 0.0
    # totais por vendedor
    vendor_summary = {}
    for o in orders:
        vname = o.vendor_obj.name if o.vendor_obj else (o.vendor or 'Desconhecido')
        if vname not in vendor_summary:
            vendor_summary[vname] = {'valor': 0.0, 'peso': 0.0, 'qtd': 0}
        o_valor = 0.0
        o_peso = 0.0
        for it in o.items:
            q = it.quantity or 0
            up = float(it.unit_price or 0.0)
            try:
                uw = float(getattr(it, 'unit_weight', None) if getattr(it, 'unit_weight', None) is not None else 0.0)
            except:
                uw = 0.0
            if not uw and getattr(it, 'product_obj', None):
                try:
                    uw = float(getattr(it.product_obj, 'weight', 0.0) or 0.0)
                except:
                    uw = 0.0
            o_valor += q * up
            o_peso += q * uw
        total_valor += o_valor
        total_peso += o_peso
        vendor_summary[vname]['valor'] += o_valor
        vendor_summary[vname]['peso'] += o_peso
        vendor_summary[vname]['qtd'] += 1

    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template('carga.html',
                           orders=orders,
                           vendors=vendors,
                           vendor_id=vendor_id,
                           date_from=date_from,
                           date_to=date_to,
                           total_valor=total_valor,
                           total_peso=total_peso,
                           vendor_summary=vendor_summary)


@bp.route('/delivery/pdf', methods=['POST'])
@admin_required
def delivery_pdf():
    """Gera PDF de comprovante de entrega para um pedido."""
    order_id = request.form.get('order_id')
    if not order_id:
        flash('Pedido não informado.', 'danger')
        return redirect(url_for('main.carga'))
    order = Order.query.get_or_404(int(order_id))
    outdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    if not os.path.isabs(outdir):
        outdir = os.path.join(current_app.root_path, outdir)
    os.makedirs(outdir, exist_ok=True)
    try:
        filename = print_delivery_pdf(order, outdir)
        flash(f'Comprovante de entrega gerado: {filename}', 'success')
        return redirect(url_for('main.prints', filename=filename))
    except Exception as e:
        current_app.logger.exception('Erro ao gerar comprovante: %s', e)
        flash(f'Erro ao gerar comprovante: {e}', 'danger')
        return redirect(url_for('main.carga'))


@bp.route('/products/search')
@login_required
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
