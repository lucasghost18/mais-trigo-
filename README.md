
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
- Para impressoras térmicas ou ESC/POS é preciso integrar uma biblioteca específica e formatar o output.

Suporte
- Posso: atualizar README (feito), criar o branch, commitar e tentar abrir o PR (se quiser, prossigo).

Packaging & Installation
------------------------

This project can be installed to run as a background service on Linux (systemd + Gunicorn) and packaged as a single executable for Windows using PyInstaller. Two helper scripts are included in `scripts/`.

Linux (recommended for servers/desktops with systemd)
- Create a virtualenv, install dependencies, and register a systemd service:

```bash
sudo ./scripts/install_linux.sh /path/to/project username
```

- The script will:
	- create `./.venv` (if missing) and install `requirements.txt` + `gunicorn`
	- write `/etc/systemd/system/mais-trigo.service` (runs `gunicorn -b 127.0.0.1:8000 wsgi:app`)
	- enable and start the service

- After install, view logs with:

```bash
sudo journalctl -u mais-trigo.service -f
```

Windows (single executable)
- Use the PowerShell build helper to create a one-file executable using PyInstaller:console.log('products length', products.length);
console.log('first product', products[0]);
document.querySelectorAll('input.product-input').forEach((el,i)=>console.log(i, el.name, el.value));
document.querySelectorAll('select.product-select').forEach((el,i)=>console.log(i, 'options', el.options.length));

Open PowerShell as Administrator and run:

```powershell
.\scripts\build_windows.ps1 -AppDir 'C:\path\to\project'
```

- This will create a `.venv`, install dependencies and `pyinstaller`, then produce a single-file binary under `dist\`.
- To run as a Windows service you can use NSSM (https://nssm.cc/) or create a service with `sc.exe` that points to the produced executable.

Notes & Recommendations
- The repository includes `wsgi.py` (WSGI entrypoint) and `run.py` (development runner). Gunicorn uses `wsgi:app`.
- For production-facing deployments consider placing an Nginx reverse proxy in front of Gunicorn and enabling TLS.
-- For fleet installs, adapt the scripts to your configuration management tooling (Ansible, Salt, etc.).

Troubleshooting (Linux / Konsole)
--------------------------------

If you see an error like `sudo: ./scripts/install_linux.sh: comando não encontrado`, it usually means you ran the relative path from a different directory (the `./scripts/...` file doesn't exist in the current working directory) or the script wasn't called with a shell. Try the commands below from Konsole:

1) Change to the project folder and run the installer (recommended):

```bash
cd /home/lucas/Documentos/code
chmod +x scripts/install_linux.sh   # optional, makes the script executable
sudo ./scripts/install_linux.sh /home/lucas/Documentos/code lucas
```

2) Or run the script with `bash` (no execute bit needed):

```bash
cd /home/lucas/Documentos/code
sudo bash scripts/install_linux.sh /home/lucas/Documentos/code lucas
```

3) Run it by absolute path (if you are in another folder):

```bash
sudo /home/lucas/Documentos/code/scripts/install_linux.sh /home/lucas/Documentos/code lucas
```

4) Quick checks if it still fails:

```bash
# does the file exist?
ls -l /home/lucas/Documentos/code/scripts/install_linux.sh
# show the first line (shebang) to ensure it's a shell script
head -n 1 /home/lucas/Documentos/code/scripts/install_linux.sh
```

If you use the `fish` shell and prefer not to change shells, run the installer through `bash` as shown above. If you want, tell me the exact command you ran and the full output and I will help debug further.


