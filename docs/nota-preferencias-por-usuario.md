# FEAT-74 — Fixação e ordem individuais no mural

A tabela `NotaPreferencia` guarda `fixada` e `ordem` por par (nota, usuário), sem alterar quem publicou a ideia, nem afetar visualização de colegas.

- `GET /api/notas/?projeto=ID&arquivada=false`: cada participante recebe `fixada` individual, `ordem` individual e ordenação: fixadas primeiro, posição salva, restante por atualização.
- `PATCH /api/notas/{id}/preferencia/` com `{"fixada":true|false}`: qualquer integrante atual pode fixar/desafixar qualquer ideia para **si mesmo**. Não edita o conteúdo nem pin de outro usuário.
- `POST /api/notas/ordenar/` com `{"projeto":ID,"ids":[...ids das ideias não arquivadas]}`: persiste arranjo para o usuário, exige lista completa e exata daquele projeto. Ordem é guardada individualmente; não muda pins de ninguém.
- Ao criar/editar uma ideia própria, `fixada` continua aceito como campo opcional por compatibilidade, mas é convertido para preferência do autor.
- Migração `0029_nota_preferencia_por_usuario` transfere pins anteriores para o autor, evitando que o pin de autor apareça para outros.
- O campo legada `Nota.fixada` é mantido para compatibilidade do banco e não é usado para retorno/ordenação dos murais. Ao filtrar `?fixada=true`, a API usa a preferência do usuário.

Segurança: tokens são obrigatórios; notas pessoais privadas; membros só podem ordenar projetos nos quais participam; IDs de outros projetos, repetidos ou ausentes geram 400; projetos inacessíveis geram 404.

Para ativar em produção é necessário executar `python manage.py migrate` e publicar este backend antes de usar o novo frontend.
