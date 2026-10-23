# FEAT-56 — Agente de IA para projetos

## Endpoint

`POST /api/projetos/{id}/agente/`

Exemplo:

```json
{
  "objetivo": "Entregar o MVP até amanhã",
  "ideias": [
    "Adicionar resumo automático",
    "Organizar tarefas por dependência"
  ]
}
```

O agente recebe contexto seguro do projeto, tarefas, membros e apenas as notas pessoais do usuário autenticado vinculadas ao projeto.

Quando `OPENAI_API_KEY` está configurada, o backend usa a OpenAI Responses API. A chave fica somente no servidor.
Se a integração externa estiver indisponível, o endpoint retorna um relatório local estruturado para não quebrar a experiência.

Variáveis:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (padrão: `gpt-4.1-mini`)
