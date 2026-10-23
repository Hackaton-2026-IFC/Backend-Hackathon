# Backend Hackathon 2026

API REST Django + Django REST Framework para gerenciamento colaborativo de projetos do Hackathon 2026 (IFC Araquari).

## Stack e ambiente
- Python **3.13** (alinhado ao `runtime.txt` da plataforma)
- PDM, Django 5, Django REST Framework e SimpleJWT
- SQLite para desenvolvimento; PostgreSQL no deploy
- Cloudinary opcional para arquivos de mídia
- Swagger/OpenAPI em `/api/doc/`; schema em `/api/schema/`

## Principais recursos
- Login JWT, registro e perfil do usuário.
- Projetos com membros owner/admin/member, convites, transferência de propriedade, prazos e fixação individual.
- Tarefas, prioridade, urgência automática/manual, dependências sem ciclos e microtarefas em sequência.
- Kanban por projeto, dashboard e progresso, filtros, busca e ordenação.
- Links/documentos de referência associados a projetos e tarefas.

## Instalação
```bash
git clone https://github.com/Hackaton-2026-IFC/Backend-Hackathon.git
cd Backend-Hackathon
cp .env.example .env
pdm install
pdm run python manage.py migrate
pdm run dev
```

Edite o `.env` e use sua própria `SECRET_KEY`. O arquivo não deve ser enviado ao Git. Cada colaborador deve usar seu próprio banco `db.sqlite3` local, criado pelas migrations; não compartilhe o banco no repositório.

## Endpoints
- `POST /api/registro/`
- `POST /api/token/`, `POST /api/token/refresh/`, `POST /api/token/verify/`
- `GET /api/usuarios/me/`
- `/api/projetos/`, `/api/tarefas/`, `/api/microtarefas/`, `/api/convites/` e `/api/recursos/`
- `GET /api/projetos/{id}/kanban/` e `GET /api/projetos/{id}/dashboard/`
- `GET /api/projetos/dashboard/`
- `GET /api/doc/`, `GET /api/redoc/` e `GET /api/schema/`

As listagens aceitam filtros específicos, `?search=` e `?ordering=`; consulte o Swagger. Envie `Authorization: Bearer <token>` nas rotas autenticadas.

## Verificação local
```bash
pdm run python manage.py check
pdm run python manage.py makemigrations --check --dry-run
pdm run python manage.py test core uploader
```

## Mídia e deploy
Configure `CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name` para habilitar Cloudinary. Sem ela, os arquivos ficam no diretório local `media/`. No Fabroku configure `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `FRONTEND_URLS`, `DATABASE_URL` PostgreSQL e `CLOUDINARY_URL` se necessário. O deploy usa `build.sh` e `Procfile`; mantenha as versões de Python compatíveis com o ambiente de hospedagem.

## Fluxo de contribuição
`main` = versão estável; `DEV` = integração; `FEAT-NUMERO` e `FIX-NUMERO` = branches isoladas nascidas de `DEV`. Abra PR para `DEV`, valide CI e somente depois integre `DEV` na `main`.
