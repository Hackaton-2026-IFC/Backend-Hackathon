# Backend Hackathon 2026

API REST do backend do **Hackathon 2026** do Instituto Federal Catarinense - Campus Araquari, voltado aos alunos do 3° ano do curso Técnico em Informática para Internet.

---

## Stack Tecnológica

- **Linguagem:** Python (v3.12+)
- **Gerenciador de Dependências:** [PDM](https://pdm-project.org/)
- **Framework Web:** Django (v5+)
- **API REST:** Django REST Framework (DRF)
- **Autenticação:** SimpleJWT (`rest-framework-simplejwt`)
- **Documentação da API:** `drf-spectacular` (Swagger / OpenAPI 3)
- **Armazenamento de Mídia:** Cloudinary
- **Banco de Dados (Dev):** SQLite3
- **Banco de Dados (Prod):** PostgreSQL
- **Servidor de Produção:** Gunicorn & WhiteNoise
- **Plataforma de Deploy:** Fabroku

---

## Arquitetura e Estrutura de Pastas

O projeto adota uma estrutura modularizada baseada em aplicações Django (`core`, `uploader`), com configurações centralizadas no pacote `app`.

```text
Backend-Hackathon/
├── .vscode/                   # Configurações do ambiente de desenvolvimento (VS Code)
├── app/                       # Módulo de configurações principais do Django
│   ├── __init__.py
│   ├── asgi.py                # Interface ASGI para serviços assíncronos
│   ├── pagination.py          # Classes customizadas de paginação da API
│   ├── settings.py            # Configurações gerais (Apps, DB, JWT, Cloudinary, CORS)
│   ├── urls.py                # Roteamento global de URLs da API
│   └── wsgi.py                # Interface WSGI para servidores Web (Gunicorn)
├── core/                      # Aplicação principal de domínio de negócio
│   ├── migrations/            # Histórico de migrações do banco de dados
│   ├── models/                # Modelos de dados (Usuários, Categorias, etc.)
│   ├── serializers/           # Serializadores do DRF para conversão de dados
│   ├── views/                 # ViewSets e endpoints da API
│   ├── __init__.py
│   ├── admin.py               # Painel administrativo do Django
│   └── apps.py                # Configuração do app Core
├── uploader/                  # Aplicação responsável pela gestão e envio de mídias
│   ├── helpers/               # Funções auxiliares para manipulação de arquivos
│   ├── migrations/            # Migrações da app uploader
│   ├── models/                # Modelos de metadados das mídias enviadas
│   ├── serializers/           # Serializadores de arquivos e mídias
│   ├── views/                 # Endpoints para upload/gerenciamento de mídias
│   ├── admin.py
│   ├── apps.py
│   ├── router.py              # Rotas do uploader
│   ├── storage.py             # Integração com armazenamento Cloudinary
│   └── tests.py               # Testes unitários do uploader
├── http/drf/                  # Requisições de teste HTTP (REST Client / Insomnia)
├── media/videos/              # Armazenamento local temporário de mídias em desenvolvimento
├── scripts/                   # Scripts auxiliares do projeto
├── .env.example               # Exemplo de variáveis de ambiente
├── .gitignore                 # Arquivos ignorados pelo Git
├── .pdm-python                # Apontador do interpretador Python do PDM
├── .pre-commit-config.yaml    # Hooks do Git para formatação/linting pré-commit
├── .pylintrc                  # Configuração do linter PyLint
├── .python-version            # Versão especificada do Python
├── Procfile                   # Comando de inicialização no Fabroku (Gunicorn)
├── build.sh                   # Script de compilação/deploy automático para produção
├── db.sqlite3                 # Banco de dados local para desenvolvimento
├── dump.json                  # Carga/fixture inicial de dados
├── manage.py                  # CLI do Django para gerenciamento de comandos
├── pdm.lock                   # Trava com versões exatas das dependências do PDM
├── pyproject.toml             # Configurações do projeto e dependências do PDM
├── requirements.txt           # Exportação de dependências para compatibilidade
└── runtime.txt                # Versão de tempo de execução do Python para o PaaS
```

---

## Como Rodar o Projeto Localmente (Usando PDM)

### Pré-requisitos

- **Python** (v3.11 ou superior)
- **PDM** instalado na sua máquina (`pip install pdm` ou via Homebrew/Pipx)

---

### Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/Backend-Hackathon.git
   cd Backend-Hackathon
   ```

2. **Instale as dependências com o PDM**
   ```bash
   pdm install
   ```

3. **Configure as Variáveis de Ambiente**
   Crie o arquivo `.env` a partir do exemplo fornecido:
   ```bash
   cp .env.example .env
   ```
   *Edite o arquivo `.env` inserindo as credenciais de desenvolvimento (Secret Key, Cloudinary, etc.).*

4. **Execute as migrações do Banco de Dados**
   ```bash
   pdm run python manage.py migrate
   ```

5. **(Opcional) Carregue dados iniciais (Fixtures)**
   ```bash
   pdm run python manage.py loaddata dump.json
   ```

6. **Crie um superusuário administrativo**
   ```bash
   pdm run python manage.py createsuperuser
   ```

7. **Inicie o servidor de desenvolvimento**
   ```bash
   pdm run dev
   # ou: pdm run python manage.py runserver
   ```

8. **Acesse a aplicação:**
   - **API Base:** `http://localhost:8000/api/`
   - **Documentação Swagger:** `http://localhost:8000/api/swagger/`
   - **Painel Admin:** `http://localhost:8000/admin/`

---

## Autenticação (SimpleJWT)

A API utiliza autenticação baseada em Tokens JWT.

### Endpoints principais de autenticação:
- **Obter Token (Login):** `POST /api/token/`
- **Atualizar Token (Refresh):** `POST /api/token/refresh/`

Exemplo de cabeçalho de requisição autenticada:
```http
Authorization: Bearer <SEU_ACCESS_TOKEN>
```

---

## Armazenamento de Arquivos (Cloudinary)

As fotos de perfil e mídias do sistema são processadas pelo app `uploader` e armazenadas na nuvem através do **Cloudinary**.

As variáveis necessárias no arquivo `.env` para habilitar a integração são:
```env
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret
```

---

## Deploy no Fabroku

O repositório possui suporte nativo para deploy no **Fabroku** utilizando o `Procfile`, o script `build.sh` e o gerenciador `pdm`.

### Configuração no Fabroku:

1. **Atribua as Variáveis de Ambiente no painel do Fabroku:**
   - `SECRET_KEY`: Sua chave secreta do Django.
   - `DEBUG`: `False`
   - `DATABASE_URL`: URL do banco de dados PostgreSQL fornecido pelo Fabroku.
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.

2. **Script de Build (`build.sh`):**
   Garante a instalação das dependências, migrações e coleta de arquivos estáticos durante o deploy:
   ```bash
   #!/usr/bin/env bash
   set -o errexit

   pdm install --prod
   python manage.py collectstatic --no-input
   python manage.py migrate
   ```

3. **Comando de Execução (`Procfile`):**
   ```text
   web: gunicorn app.wsgi:application --log-file -
   ```

---

## Scripts e Comandos Úteis do PDM

- `pdm run dev`: Executa o servidor de desenvolvimento.
- `pdm run migrate`: Aplica migrações pendentes no banco de dados.
- `pdm run makemigrations`: Cria novas migrações a partir dos modelos.
- `pdm run lint`: Executa a verificação de código com o linter configurado.
