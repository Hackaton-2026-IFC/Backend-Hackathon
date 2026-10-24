# FEAT-72 — Mural multimídia (ideias com texto, links e fotos)

Amplia o CRUD existente de notas pessoais sem alterar a rota principal.

## API
- `GET /api/notas/` mantém paginação/filtros e agora retorna `link` e `imagem_url`.
- `POST /api/notas/` aceita JSON para ideias de texto/link ou `multipart/form-data` para enviar uma foto diretamente no campo `imagem`.
- `PATCH /api/notas/{id}/` aceita JSON para editar campos/limpar foto (`{\"imagem\":null}`) ou multipart para substituir foto.
- `DELETE /api/notas/{id}/` elimina a ideia; operações são limitadas ao dono.

Campos: `titulo`, `conteudo`, `link`, `imagem` (entrada opcional), `imagem_url` (somente leitura), `cor`, `fixada`, `arquivada`, `etiquetas`, `projeto`.
Uma ideia pode conter somente um link ou somente uma foto. Upload JPG, PNG, WEBP ou GIF com limite de 5 MB e 20 MP; URLs apenas HTTP(S). Fotos são armazenadas pelo storage padrão do Django (Cloudinary, quando configurado no servidor).

## Privacidade e operação
O endpoint de notas isola por usuário; isso **não torna a URL pública do arquivo privativa**. Não incluir imagens sigilosas se o storage de mídia permitir acesso por URL. Verificar política de mídia na implantação.

## Integração
Frontend: enviar `FormData` com `imagem` quando houver foto nova, usando JWT; sem foto, JSON continua válido. Se `etiquetas` for enviado via multipart, serializar como JSON. Aplicar `python manage.py migrate` após deploy. Não exige uma nova API de upload.
