# FEAT-70 — Verificação pré-deploy

Execute **no ambiente publicado**, com as variáveis de produção já carregadas:

```bash
pdm run python manage.py check --deploy
pdm run python manage.py checar_producao
pdm run python manage.py showmigrations --plan
```

O comando adicional valida DEBUG, SECRET_KEY, ALLOWED_HOSTS, origens CORS e a conectividade com o banco sem mostrar credenciais. Não prova que o proxy, DNS, HTTPS ou frontend publicado funcionam. Verifique também os endpoints de health e login via HTTPS, migrações aplicadas, permissões e scheduler no painel de deploy.
