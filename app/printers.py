import os
import subprocess
from datetime import datetime
from flask import current_app


def _render_order_text(order):
    lines = []
    lines.append(f'Pedido: #{order.id}')
    lines.append(f'Cliente: {order.customer or "-"}')
    vendor_name = (order.vendor_obj.name if getattr(order, 'vendor_obj', None) else order.vendor)
    lines.append(f'Vendedor: {vendor_name or "-"}')
    lines.append(f'Endereço: {order.address or "-"}')
    lines.append(f'Cidade: {order.city or "-"}    Tel: {order.phone or "-"}')
    lines.append(f'CNPJ: {order.cnpj or "-"}')
    lines.append(f'Observação: {order.notes or "-"}')
    lines.append(f'Data: {order.created_at.strftime("%Y-%m-%d %H:%M")}')
    lines.append('-' * 60)
    lines.append(f'{"QUANT":>5}  {"DESCRIÇÃO":<30} {"PREÇO UNID":>12} {"TOTAL":>10}')
    lines.append('-' * 60)
    total = 0.0
    total_weight = 0.0
    def _fmt_weight_raw(v):
        try:
            f = float(v or 0.0)
        except:
            return ''
        s = f"{f:.3f}".rstrip('0').rstrip('.')
        return s

    for it in order.items:
        q = it.quantity or 0
        up = float(it.unit_price or 0.0)
        # determine unit weight: prefer stored unit_weight, fallback to product weight
        try:
            uw = float(getattr(it, 'unit_weight', None) if getattr(it, 'unit_weight', None) is not None else 0.0)
        except:
            uw = 0.0
        if not uw and getattr(it, 'product_obj', None):
            try:
                uw = float(getattr(it.product_obj, 'weight', 0.0) or 0.0)
            except:
                uw = 0.0
        line_weight = q * uw
        line_total = q * up
        total += line_total
        total_weight += line_weight
        prod_name = it.product or (it.product_obj.name if getattr(it, 'product_obj', None) else '')
        lines.append(f'{q:>5}  {prod_name:<30} {up:>12.2f} {line_total:>10.2f}')
    total_weight_str = _fmt_weight_raw(total_weight)
    lines.append(f'TOTAL PESO: {total_weight_str} kg')
    lines.append(f'TOTAL: {total:.2f}')
    lines.append('FIM')
    return '\n'.join(lines)


def print_order_pdf(order, outdir):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        raise RuntimeError('reportlab is required to generate PDF. Install with: pip install reportlab')

    filename = f'order_{order.id}.pdf'
    filepath = os.path.join(outdir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f'PEDIDO Nº {order.id}', styles['Title']))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f'<b>Cliente:</b> {order.customer or "-"}', styles['Normal']))
    vendor_name = (order.vendor_obj.name if getattr(order, 'vendor_obj', None) else order.vendor)
    story.append(Paragraph(f'<b>Vendedor:</b> {vendor_name or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Endereço:</b> {order.address or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Cidade / Tel:</b> {order.city or "-"} / {order.phone or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>CNPJ:</b> {order.cnpj or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Observação:</b> {order.notes or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Data:</b> {order.created_at.strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 12))

    data = [['QUANT', 'DESCRIÇÃO', 'PREÇO UNID', 'TOTAL']]
    total = 0.0
    total_weight = 0.0
    for it in order.items:
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
        line_weight = q * uw
        line_total = q * up
        total += line_total
        total_weight += line_weight
        prod_name = it.product or (it.product_obj.name if getattr(it, 'product_obj', None) else '')
        data.append([str(q), prod_name, f'{up:.2f}', f'{line_total:.2f}'])

    # append total row for price
    data.append(['', '', 'TOTAL', f'{total:.2f}'])

    colWidths = [50, 340, 80, 80]
    t = Table(data, colWidths=colWidths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9bd7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('SPAN', (0, len(data) - 1), (1, len(data) - 1)),
        ('ALIGN', (2, len(data) - 1), (3, len(data) - 1), 'RIGHT'),
    ])
    t.setStyle(style)
    story.append(t)
    # show total weight under the table (formatted)
    story.append(Spacer(1, 6))
    total_weight_str = (f"{(float(total_weight) if total_weight else 0.0):.3f}").rstrip('0').rstrip('.')
    story.append(Paragraph(f'<b>Peso total:</b> {total_weight_str} kg', styles['Normal']))

    doc.build(story)
    return filename


def print_delivery_pdf(orders, outdir):
    """Gera um PDF simples de comprovante de entrega com quantidade, peso e produto."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        raise RuntimeError('reportlab is required to generate PDF. Install with: pip install reportlab')

    # Ensure orders is a list
    if not isinstance(orders, list):
        orders = [orders]

    if len(orders) == 1:
        filename = f'delivery_{orders[0].id}.pdf'
    else:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'delivery_batch_{ts}.pdf'

    filepath = os.path.join(outdir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph('COMPROVANTE DE ENTREGA', styles['Title']))
    story.append(Spacer(1, 12))

    # Build items list: only quantity, product, weight
    # Group same products together and sum quantities/weights
    from collections import defaultdict
    grouped = defaultdict(lambda: {'quantity': 0, 'weight': 0.0})

    for order in orders:
        for it in order.items:
            q = it.quantity or 0
            try:
                uw = float(getattr(it, 'unit_weight', None) if getattr(it, 'unit_weight', None) is not None else 0.0)
            except:
                uw = 0.0
            if not uw and getattr(it, 'product_obj', None):
                try:
                    uw = float(getattr(it.product_obj, 'weight', 0.0) or 0.0)
                except:
                    uw = 0.0
            line_weight = q * uw
            prod_name = it.product or (it.product_obj.name if getattr(it, 'product_obj', None) else '')
            grouped[prod_name]['quantity'] += q
            grouped[prod_name]['weight'] += line_weight

    items_data = [['QUANTIDADE', 'PRODUTO', 'PESO TOTAL']]
    total_peso = 0.0

    for prod_name, data in grouped.items():
        total_peso += data['weight']
        items_data.append([
            str(data['quantity']),
            prod_name,
            f"{data['weight']:.2f} kg"
        ])

    # Total row
    items_data.append(['', 'TOTAL GERAL', f'{total_peso:.2f} kg'])

    colWidths = [80, 380, 100]
    items_table = Table(items_data, colWidths=colWidths)
    last_row = len(items_data) - 1
    items_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9bd7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('SPAN', (0, last_row), (1, last_row)),
        ('ALIGN', (0, last_row), (-1, last_row), 'RIGHT'),
        ('FONTNAME', (0, last_row), (-1, last_row), 'Helvetica-Bold'),
    ])
    items_table.setStyle(items_style)
    story.append(items_table)

    doc.build(story)
    return filename


def print_order(order, method=None):
    """Renderiza o pedido e salva como texto ou PDF, ou envia para impressora via lpr.

    Retorna o nome do arquivo gerado (relativo a PRINTER_OUTPUT_DIR).
    """
    method = method or current_app.config.get('PRINTER_METHOD', 'file')
    outdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    if not os.path.isabs(outdir):
        outdir = os.path.join(current_app.root_path, outdir)
    os.makedirs(outdir, exist_ok=True)

    if method == 'pdf':
        filename = print_order_pdf(order, outdir)
        # optionally send to printer? we just generate PDF
        return filename

    # default: text file
    content = _render_order_text(order)
    filename = f'order_{order.id}.txt'
    filepath = os.path.join(outdir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    if method == 'lpr':
        # send to default system printer via lpr (requires CUPS or lpr installed)
        subprocess.run(['lpr', filepath], check=True)

    return filename
