# FEAT-57 — Notificações no site e por e-mail

## API

- `GET /api/notificacoes/` — lista somente as notificações do usuário autenticado.
- `GET /api/notificacoes/nao-lidas/` — contador para badge no frontend.
- `POST /api/notificacoes/{id}/ler/` — marca uma notificação como lida.
- `POST /api/notificacoes/ler-todas/` — marca todas como lidas.

Eventos atuais:

- tarefa criada;
- tarefa alterada;
- tarefa excluída;
- comentário criado.

## E-mail

O envio é opcional e desativado por padrão. Configure no servidor:

- `NOTIFICATION_EMAIL_ENABLED=True`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS=True`
- `DEFAULT_FROM_EMAIL`

O site continua funcionando se o SMTP estiver indisponível. Senhas de e-mail nunca devem ir para o frontend ou para o repositório.
