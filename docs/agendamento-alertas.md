# FEAT-64 — Execução automática dos alertas

O serviço de alertas e o comando `processar_prazos` já existem e têm testes de idempotência. Para que os avisos surjam sem intervenção, **o agendador precisa rodar no mesmo ambiente e banco do Django em produção**.

## Agendamento de produção

No servidor que executa o backend, configure um cron diário às 08:00 no fuso `America/Sao_Paulo` (adequar o caminho real de instalação):

```cron
CRON_TZ=America/Sao_Paulo
0 8 * * * cd /caminho/Backend-Hackathon && /caminho/para/pdm run python manage.py processar_prazos >> /var/log/momentum-prazos.log 2>&1
```

Alternativa: use um job/scheduler do provedor de hospedagem para executar `pdm run python manage.py processar_prazos` diariamente com as mesmas variáveis `DATABASE_URL` e `SECRET_KEY` do serviço web.

## Verificação

1. Rode `pdm run python manage.py processar_prazos` manualmente no ambiente correto.
2. Verifique a criação de notificações de vencimento e os logs do job.
3. Rode novamente no mesmo dia: os alertas de mesmo tipo/prazo não devem duplicar.
4. Confirme que o job diário está ativo no painel do provedor. **Este commit não ativa cron automaticamente na hospedagem.**

Não rode a tarefa no GitHub Actions contra banco local: o runner não compartilha o banco de produção.

> Verifique que o scheduler usa o mesmo banco de dados do serviço Django; a execução local não produz notificações na base publicada.
