# Proteção local do banco Render

- [x] Criar backup PostgreSQL com credencial privada, arquivo atômico e validação do dump.
- [x] Preparar agendamento systemd por hora e banco Docker isolado para recuperação.
- [x] Documentar ativação, restauração e limites (WSL desligado e anexos).
- [x] Testar sem acessar produção e executar a atualização do graphify.

Ativação depende da URL externa atualizada fornecida localmente pelo responsável.
Validação: 7 testes unitários, Ruff e sintaxe Bash passaram. Docker ainda exige
integração WSL; backup real e restauração real não foram executados. Graphify
executou com aviso de proteção contra redução do grafo existente, sem forçar sobrescrita.
