# FEAT-69: Ativação dos alertas no servidor

O job precisa ser cadastrado no cron ou scheduler do provedor (Fabroku) por alguém com acesso à implantação. Este repositório inclui um exemplo em `deploy/cron-processar-prazos.example`, mas a simples inclusão do arquivo NÃO agenda nenhuma execução.

1. Confirmar fuso `America/Sao_Paulo`, persistência do banco e variáveis de ambiente.
2. Executar `pdm run python manage.py processar_prazos` no container do backend.
3. Cadastrar o comando para rodar todo dia às 08:00 no scheduler da hospedagem, ou configurar cron em um processo persistente.
4. Inspecionar a saída da primeira execução e a seguinte; execução repetida não deve criar alertas duplicados.
5. Conferir que a próxima execução foi agendada no painel do provedor.

Não coloque credenciais do banco, da IA ou tokens de acesso no cron versionado.
