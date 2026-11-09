# Cadastro das perguntas Vineland-3

- [x] Cadastrar as 180 perguntas em protocolo próprio, conferindo trechos de OCR no PDF.
- [x] Integrar API e tela com respostas 0/1/2, itens binários, Est. e observações, preservando o protocolo antigo.
- [x] Testar persistência, validação, reabertura, proteção do legado e componente; executar lint e atualização do grafo.

Escopo: cadastro e preenchimento, sem liberar correção normativa ou laudo.

## Verificação

- 37 testes Django do Vineland e 13 testes do componente passaram.
- Ruff, ESLint dos componentes alterados, TypeScript e Bandit passaram.
- Testes do componente cobrem estrutura e eventos, não homologação clínica ou validação visual em navegador.
- `npm audit` encontrou 15 vulnerabilidades nas dependências existentes (7 moderadas, 7 altas e 1 crítica); nenhuma dependência foi alterada nesta tarefa.
- `graphify update .` executado: relatório regenerado; `graph.json` preservado pela ferramenta devido ao alerta de redução de nós. Não foi forçada sobrescrita.

## Correção do acesso pela avaliação

- O fluxo de adicionar teste cria um registro vazio e abre a tela com `application_id`. A tela anteriormente assumia totais para todo registro existente e a API impedia inicializá-lo com perguntas.
- Registros realmente vazios agora abrem perguntas e podem ser preenchidos no mesmo ID; dados antigos e registros travados continuam protegidos. Para aplicações já preenchidas há um link explícito para as 180 perguntas em nova aplicação.
- Regressões verificadas: 40 testes Django e 16 de interface/renderização passaram; TypeScript, ESLint e Ruff passaram. Não foi validado em navegador autenticado no ambiente publicado: a URL fornecida exige login da Vercel. Frontend e backend precisam receber esta versão para o comportamento aparecer no ambiente remoto.
