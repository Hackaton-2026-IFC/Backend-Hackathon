# FEAT-73 — Mural compartilhado por projeto

Cada projeto tem mural próprio de ideias (texto, links e imagem), utilizando as notas existentes. Não há migração: o campo `projeto` já existe e as notas de projeto publicadas antes da FEAT passam a ser compartilhadas com a equipe.

## Regras
- `GET /api/notas/?projeto={id}`: todos os membros atuais veem as notas daquele projeto (inclusive criadas por outros membros). Inclui nome do autor (`usuario_nome`) e identificador (`usuario`).
- `POST /api/notas/` com `projeto:{id}`: qualquer membro pode publicar texto, link ou imagem.
- `GET /api/notas/` sem filtro mantém listagem de notas do próprio usuário (pessoais e de projetos), sem misturar notas de colegas.
- `GET /api/notas/{id}/`: notas pessoais só para autor; notas de projeto para membros atuais.
- Somente o **autor** pode alterar, fixar, arquivar ou excluir sua ideia. Outros membros recebem 403; usuários externos recebem 404.
- `POST/PATCH /api/notas/` e `PATCH /api/notas/{id}/` mantêm formatos JSON e multipart da FEAT-72.
- Ao deixar o projeto, o usuário perde acesso às notas dele imediatamente, mesmo às que havia criado no mural.
- Projetos distintos nunca compartilham as mesmas notas. Notas pessoais permanecem privadas.

## Frontend
Uma rota de mural de cada projeto deve carregar exclusivamente `/api/notas/?projeto={id}`, preencher `projeto` ao criar e esconder edição/exclusão para não autores. Deve identificar o autor nos cartões. Separar do mural geral `/notes` para evitar misturar projetos.

## Atenção à mídia
O filtro de permissões protege os endpoints de notas. Links públicos diretos para imagens de storage público não são protegidos pelo Django; não armazenar dados sigilosos sem política de mídia privada.
