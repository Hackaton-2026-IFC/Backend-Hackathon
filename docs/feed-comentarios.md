# Feed de atividades e comentários

Requer `Authorization: Bearer <access_token>`. Somente participantes do projeto podem consultar o feed e os comentários.

## Feed

- `GET /api/projetos/{id}/atividades/?page=1&page_size=20` — histórico do projeto (mais recente primeiro).
- `GET /api/projetos/{id}/atividades/?tarefa={tarefa_id}` — filtro por tarefa, mesmo após exclusão.
- `GET /api/tarefas/{id}/atividades/` — histórico de uma tarefa existente.

Respostas paginadas incluem `count`, `next`, `previous`, `results`. Cada atividade contém `id`, `projeto`, `tarefa`, `tarefa_id_original`, `tarefa_titulo`, `autor`, `autor_nome`, `acao`, `alteracoes` e `criado_em`.

Ações automáticas: `tarefa_criada`, `tarefa_alterada`, `tarefa_excluida`, `comentario_criado`, `comentario_editado`, `comentario_excluido`. Para alterações de tarefa, `alteracoes` traz cada campo alterado com `antes` e `depois`. Após excluir uma tarefa, seu registro permanece no feed do projeto, com `tarefa=null` e `tarefa_id_original` preservado.

## Comentários

- `GET /api/tarefas/{id}/comentarios/?page=1` — lista paginada, ordem cronológica.
- `POST /api/tarefas/{id}/comentarios/`, corpo `{"conteudo":"Vou implementar essa etapa"}` — cria comentário, resposta 201.
- `PATCH /api/tarefas/{id}/comentarios/{comentario_id}/`, corpo `{"conteudo":"Corrigido e testado"}` — edita somente comentário do próprio autor.
- `DELETE /api/tarefas/{id}/comentarios/{comentario_id}/` — exclui somente comentário do próprio autor, resposta 204.

Comentários não vazios, tamanho máximo de 5000 caracteres. Não há WebSocket nem chat instantâneo nesta versão; o frontend deve atualizar via nova consulta ou polling. A criação/edição/exclusão gera entrada no feed, mas não inclui o texto do comentário no evento.
