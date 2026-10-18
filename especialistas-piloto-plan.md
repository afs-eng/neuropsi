# Piloto dos especialistas com worker local

- [x] Expor configuração/eligibilidade privada sem chamadas de IA e sem escolher modelo automaticamente.
- [x] Acrescentar revisão profissional auditável dos rascunhos, sem copiar textos para o laudo.
- [x] Criar painel experimental por aplicação com solicitação, status, evidências e revisão.
- [x] Preparar worker local com checagem sem consumo e filtro por laudo; documentar banco compartilhado e variáveis.
- [x] Verificar isolamento, resultados desatualizados, revisão, worker e regressões com modelos offline; validar TypeScript e Ruff.

O fluxo legado permanece intacto e identificado. Não alterar arquivos de credenciais,
não iniciar worker/chamadas reais, não ativar infraestrutura paga. Modelo e referências
clínicas exigem escolha/homologação antes do uso real. A ativação não será presumida.

Verificação: 249 testes direcionados, TypeScript, ESLint do componente, Ruff dos
arquivos novos/alterados do piloto e consistência da migration passaram.
Sem chamada real, deploy ou worker iniciado. Operação no PostgreSQL compartilhado,
renderização no navegador e homologação clínica continuam pendentes.
Migration nova: `reports.0008_specialistreview`. Instruções de ativação e comandos
sem consumo em `apps/reports/SPECIALIST_AGENTS.md`.
