# FEAT-58 — alertas automáticos de vencimento

Executar **uma vez por dia**, preferencialmente às 09:00 no horário de São Paulo:

```bash
python manage.py processar_prazos
```

Exemplo de cron no servidor (`CRON_TZ=America/Sao_Paulo`):
```cron
CRON_TZ=America/Sao_Paulo
0 9 * * * cd /caminho/backend && /caminho/backend/.venv/bin/python manage.py processar_prazos
```

**Importante:** o comando não roda sozinho. Configure o agendador do servidor/worker, e monitore a execução. A branch DEV não ativa jobs automaticamente no ambiente hospedado.

- Um dia antes: `prazo_amanha`.
- No dia: `prazo_hoje`.
- Depois do vencimento: `prazo_atrasada`, uma única vez para cada prazo e destinatário.
- Não avisa tarefas concluídas.
- Se a tarefa tem responsável, avisa somente ele. Sem responsável, avisa os membros do projeto.
- Usa o prazo antecipado se houver; caso contrário, o prazo oficial.
- Evita notificações duplicadas por destinatário, tarefa, data de prazo e tipo de aviso.
- SMTP segue o controle opcional `NOTIFICATION_EMAIL_ENABLED`.
- O dashboard e a API da tarefa retornam `atrasada`, `vence_hoje` e `dias_para_prazo`.
