# BPA-2: evidências obrigatórias por seção

Execução #13: `bpa2_missing_evidence`, sem saída rejeitada persistida. O log não
permite identificar qual referência faltou. A configuração/conexão funciona.

Fragilidade verificável: o enum global exige IDs existentes, mas não explicita
o conjunto mínimo por seção. O retry informa falta de referências sem indicar
as ausências. Na síntese, o validador exige as quatro modalidades, enquanto a
instrução menciona apenas modalidades discutidas.

- [x] Reproduzir ausência em componente/síntese com respostas sintéticas.
- [x] Compartilhar requisitos exatos entre guia e validação, com alternativas de escore.
- [x] Informar todas as referências faltantes no retry e seção allowlisted no diagnóstico.
- [x] Versionar solicitação nova, preservando sucessos anteriores e falhas terminais.
- [x] Testar bloqueio, recuperação, privacidade, regressões e atualizar documentação/grafo.

Sem completar citações automaticamente, reduzir validação, aumentar limites,
iniciar inferência, reativar jobs, publicar ou alterar credenciais.

Verificação: os três testes de reprodução falharam antes do ajuste e passaram
depois. Total de 319 testes backend (6 novos), Ruff, TypeScript, lint do componente,
diff-check e consistência de migrations passaram. Não há migration nova.

Versão nova: `pydantic-bpa2-5-ollama-4k` no Ollama. Atualizar backend e worker antes
da solicitação explícita sintética; frontend atualizado mostra a seção quando
disponível. Não há garantia de aprovação clínica ou de sucesso no modelo real.
Graphify executado sem force: relatório/cache atualizados, redução de graph.json
de 9030 para 7674 nós recusada. Não houve inferência real nem teste em navegador.
