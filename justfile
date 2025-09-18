# justfile
# Definir que os comandos devem rodar no shell do PowerShell
set shell := ["powershell.exe", "-NoLogo", "-Command"]

# Start venv environment:
startvenv:
    .venv\Scripts\activate

# Cria ambiente virtual
venv:
    uv venv

# Instala dependências do requirements.txt
install: venv
    uv pip install -r requirements.txt

# Faz sync (garante que os pacotes extras/novos do pyproject.toml sejam instalados)
sync: venv
    uv sync

# Ativa o ambiente (no Windows)
activate:
    .venv\Scripts\activate.ps1

# Adiciona um pacote (uso: just add package=nome_do_pacote)
add package: venv
    uv pip install {{package}}
    uv sync
    uv pip freeze > requirements.txt

# Pipeline completo (do zero até sync)
setup: venv install sync