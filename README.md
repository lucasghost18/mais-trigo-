
# Sistema de Pedidos - Distribuição de Panificação

Pequeno sistema web para criar pedidos internos e gerar impressões para carregar o caminhão.

Requisitos
- Python 3.8+
- `pip install -r requirements.txt`

Como rodar (desenvolvimento)

1. Instale dependências:

```bash
pip install -r requirements.txt
```

2. Execute a aplicação (desenvolvimento):

```bash
python run.py
```

3. Abra no navegador: `http://localhost:5000`

Visão geral
- A aplicação permite criar pedidos internos com múltiplos itens, preço unitário e total.
- Campos do pedido: `customer`, `address`, `city`, `phone`, `cnpj`.
- Impressão: por padrão grava `prints/order_<id>.txt`. Configure `PRINTER_METHOD` para `lpr` para enviar ao CUPS.

Configuração de impressão
- Para salvar arquivos de impressão em outra pasta:

```bash
export PRINTER_OUTPUT_DIR=/caminho/para/pasta
```

- Para enviar direto à impressora (CUPS):

```bash
export PRINTER_METHOD=lpr
```

Notas sobre banco de dados
- A aplicação usa SQLite por padrão (`orders.db`). Quando novos campos foram adicionados (endereço, cidade, telefone, cnpj, unit_price), a aplicação tenta aplicar um `ALTER TABLE` simples em SQLite para manter dados existentes.

Commit e PR (opcional)
- Crie um branch local, adicione e comite as alterações, e envie ao `origin`:

```bash
git checkout -b feature/update-readme
git add -A
git commit -m "docs: update README and usage instructions"
git push -u origin feature/update-readme
```

- Para abrir um Pull Request você pode usar a interface do GitHub ou o `gh` (GitHub CLI):

```bash
gh pr create --fill --base main --head feature/update-readme
```

Observações
- Por padrão a impressão gera arquivos texto (UTF-8) prontos para visualização/impressão.
- Para impressoras térmicas ou ESC/POS é preciso integrar uma biblioteca específica e formatar o output
