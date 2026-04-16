import os
import subprocess
from flask import current_app


def _render_order_text(order):
    lines = []
    lines.append(f'Pedido: #{order.id}')
    lines.append(f'Cliente: {order.customer or "-"}')
    lines.append(f'Endereço: {order.address or "-"}')
    lines.append(f'Cidade: {order.city or "-"}    Tel: {order.phone or "-"}')
    lines.append(f'CNPJ: {order.cnpj or "-"}')
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


def print_order(order):
    """Renderiza o pedido para texto e envia para a impressora ou salva em arquivo.

    Retorna o nome do arquivo gerado (relativo a PRINTER_OUTPUT_DIR).
    """
    method = current_app.config.get('PRINTER_METHOD', 'file')
    outdir = current_app.config.get('PRINTER_OUTPUT_DIR', 'prints')
    os.makedirs(outdir, exist_ok=True)

    content = _render_order_text(order)
    filename = f'order_{order.id}.txt'
    filepath = os.path.join(outdir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    if method == 'lpr':
        # send to default system printer via lpr (requires CUPS or lpr installed)
        subprocess.run(['lpr', filepath], check=True)

    return filename
