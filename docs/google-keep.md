# FEAT-55 — Notas estilo Google Keep

## Endpoints

- `GET /api/notas/` — lista somente as notas do usuário autenticado.
- `POST /api/notas/` — cria uma nota.
- `GET /api/notas/{id}/` — detalha uma nota do próprio usuário.
- `PATCH /api/notas/{id}/` — edita, fixa ou arquiva.
- `DELETE /api/notas/{id}/` — exclui.
- Filtros: `projeto`, `fixada`, `arquivada`.
- Busca: `?search=texto`.
- Ordenação: `titulo`, `criada_em`, `atualizada_em`, `lembrete_em`.

## Campos

`titulo`, `conteudo`, `cor`, `fixada`, `arquivada`, `etiquetas`, `lembrete_em` e vínculo opcional com `projeto`.

As notas são pessoais mesmo quando vinculadas a um projeto: um membro não consegue ler as notas privadas de outro membro.
