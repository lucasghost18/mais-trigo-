import os
import subprocess
from flask import current_app


def _render_order_text(order):
    lines = []
    lines.append(f'Pedido: #{order.id}')
    lines.append(f'Cliente: {order.customer or "-"}')
    lines.append(f'Vendedor: {order.vendor or "-"}')
    lines.append(f'Endereço: {order.address or "-"}')
    lines.append(f'Cidade: {order.city or "-"}    Tel: {order.phone or "-"}')
    lines.append(f'CNPJ: {order.cnpj or "-"}')
    lines.append(f'Observação: {order.notes or "-"}')
    lines.append(f'Data: {order.created_at.strftime("%Y-%m-%d %H:%M")}')
    lines.append('-' * 60)
    lines.append(f'{"QUANT":>5}  {"DESCRIÇÃO":<30} {"UNIT.":>8} {"TOTAL":>8}')
    lines.append('-' * 60)
    total = 0.0
    for it in order.items:
        q = it.quantity or 0
        up = float(it.unit_price or 0.0)
        line_total = q * up
        total += line_total
        lines.append(f'{q:>5}  {it.product:<30} {up:>8.2f} {line_total:>8.2f}')
    lines.append('-' * 60)
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
    story.append(Paragraph(f'<b>Vendedor:</b> {order.vendor or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Endereço:</b> {order.address or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Cidade / Tel:</b> {order.city or "-"} / {order.phone or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>CNPJ:</b> {order.cnpj or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Observação:</b> {order.notes or "-"}', styles['Normal']))
    story.append(Paragraph(f'<b>Data:</b> {order.created_at.strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 12))

    data = [['QUANT', 'DESCRIÇÃO', 'UNIT.', 'TOTAL']]
    total = 0.0
    for it in order.items:
        q = it.quantity or 0
        up = float(it.unit_price or 0.0)
        line_total = q * up
        total += line_total
        data.append([str(q), it.product or '', f'{up:.2f}', f'{line_total:.2f}'])

    data.append(['', '', 'TOTAL', f'{total:.2f}'])

    colWidths = [50, 300, 60, 60]
    t = Table(data, colWidths=colWidths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9bd7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('SPAN', (0, len(data) - 1), (1, len(data) - 1)),
        ('ALIGN', (2, len(data) - 1), (3, len(data) - 1), 'RIGHT'),
    ])
    t.setStyle(style)
    story.append(t)

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
