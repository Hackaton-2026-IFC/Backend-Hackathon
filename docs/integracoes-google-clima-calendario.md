# Integrações do Hackathon 2026 (backend)

## Autenticação Google

Configure `GOOGLE_CLIENT_ID` no ambiente do Django (OAuth Client ID do tipo Web no Google Cloud).
O frontend deve usar Google Identity Services para receber um **ID token** assinado pelo Google e enviar:

```http
POST /api/auth/google/
Content-Type: application/json

{"credential":"ID_TOKEN_GOOGLE"}
```

Retorno `200`: `access`, `refresh`, `user_id`. As sessões Google carregam a claim `auth_provider=google`.
Uma conta nova é criada sem senha local. Se já existir usuário com o e-mail, **não há vinculação automática**.
Faça login tradicional nessa conta e vincule o Google explicitamente com `POST /api/auth/google/vincular/` e a mesma `credential`. Depois, inicie sessão com Google para acessar o Google Agenda.
`GET /api/auth/google/vincular/` informa se a conta já está vinculada.

> O MVP valida credenciais no endpoint Google tokeninfo, que exige acesso à rede e não é recomendado pelo Google para produção em alto volume. Antes de operar em produção, utilizar verificação local com chaves públicas usando a biblioteca oficial Google Auth, com cache de certificados.

## Meu dia inteligente

```http
GET /api/meu-dia/?limite=10&equipe=false
Authorization: Bearer ACCESS_JWT
```

Por padrão considera tarefas atribuídas ao usuário ou sem responsável. `equipe=true` amplia às tarefas de projetos que participa.
Recomendações incluem tarefa, pontuação, bloqueio e motivos. É um algoritmo determinístico, não IA generativa.

## Clima

No `POST/PATCH /api/tarefas/`, envie `clima_influencia` (booleano) e `localizacao` (nome da cidade).
`data_limite` ou `prazo_antecipado` fornecem a data da consulta.

```http
GET /api/tarefas/{id}/clima/
Authorization: Bearer ACCESS_JWT
```

Consulta Open-Meteo Geocoding + Forecast apenas para tarefas marcadas, com cache de 1 hora. Retorna `disponivel=false` em datas fora do horizonte de 16 dias. A localização deve ser uma cidade pesquisável. Não muda datas automaticamente.

## Calendário de projetos

```http
GET /api/projetos/{id}/calendario/?inicio=2026-10-23&fim=2026-11-23
POST /api/projetos/{id}/calendario/
PATCH /api/projetos/{id}/calendario/{evento_id}/
DELETE /api/projetos/{id}/calendario/{evento_id}/
```

Exemplo criação `{"titulo":"Reunião de equipe","data":"2026-10-25","hora_inicio":"14:00","hora_fim":"15:00","localizacao":"Joinville"}`.
Consulta lista eventos e tarefas com prazo no intervalo (máximo 366 dias).

## Exportação para Google Agenda

Pré-requisitos **separados**:

1. Conta vinculada ao Google e **sessão atual efetuada com Google** via `/api/auth/google/` (JWT com `auth_provider=google`).
2. O frontend deve solicitar consentimento OAuth para os escopos `openid` e `https://www.googleapis.com/auth/calendar.events` (Google Identity Services token client). O escopo de Agenda não é concedido só por fazer login.
3. Envie um **access token OAuth de curta duração** e o ID do evento já existente:

```http
POST /api/projetos/{id}/google-agenda/
Authorization: Bearer ACCESS_JWT
Content-Type: application/json

{"evento":123,"access_token":"GOOGLE_OAUTH_ACCESS_TOKEN"}
```

O backend valida escopos, verifica `sub` no Google UserInfo e exige que corresponda à conta vinculada. Em seguida cria um evento no calendário principal e retorna `id` e `htmlLink`. É uma **exportação sob demanda**, não sincronização bidirecional ou permanente: o servidor não armazena access/refresh tokens do Google.
