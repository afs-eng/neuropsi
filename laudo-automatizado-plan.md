# Plano — laudo automatizado com duas revisões profissionais

Arquitetura: `arquitetura-laudo-automatizado.md`.
Status: decisões de produto aprovadas; primeiro inventário implementado sob flag;
esteira de execução e instalação ainda não executadas.
Este plano complementa `clinical-ai-implementacao-plan.md`, não substitui seus
requisitos de segurança/homologação. Etapas pequenas com flags inicialmente desligadas.

## 1. Pré-checagem, manifesto e coordenação persistente

Primeiro incremento implementado sob flag desligada: ver
`report-preparation-primeira-entrega-plan.md` e `apps/reports/REPORT_PREPARATION.md`.
É inventário e registro de etapas, sem agendamento, DAG executável ou inferência.
Os demais incrementos e requisitos de liberação abaixo continuam planejados.

- Propostos: `report_preparation_service.py`, `report_preflight_service.py`,
  contratos de preparação e testes próprios em `apps/reports/`.
- Alterações aditivas em `apps/reports/models.py` e migrations: preparação,
  etapas/dependências, vínculos de fontes e tentativas. Refinar os nomes na entrega.
- Definir relatório/revisão alvo, chave idempotente, cobertura de aplicações,
  versões, escopo, elegibilidade e regras de bloqueio; excluir nenhuma aplicação
  silenciosamente. Sem inferência nesta primeira entrega.
- API autenticada de pré-checagem/start/status; transições e etapas seguintes
  persistidas atomicamente. Reconciliar no próximo poll, sem daemon no Render.
- Aceite: clique duplicado não duplica preparação; conta alheia não consulta nem
  inicia; fonte inválida/faltante gera bloqueio; laudo aprovado exige nova revisão.
- Risco: manifesto incompleto, duplicação ou autorização ampla. Rollback: desativar
  nova API/flag, manter tabelas e registros, sem alterar o legado.

## 2. Worker pareado, roteamento, lease e orçamento

- Adaptar `specialist_run_service.py`, worker atual e transporte; adicionar API
  restrita e credencial revogável por conta. Não publicar acesso global de fila.
- Capacidade/configuração compatíveis antes do claim; lease/tentativa com gravação
  condicional, validação no backend, resultado idempotente e heartbeat.
- Planejar migração do acesso direto PostgreSQL para API, mantendo caminhos
  explicitamente separados durante a transição. Não operar simultaneamente dois
  consumidores incompatíveis sobre a mesma fila nova.
- Reservar limites antes de inferir e definir tetos por etapa/preparação; manter
  os budgets existentes de especialistas. Novas etapas não habilitam provedor pago.
- Aceite offline: duas instâncias, expiração de lease, alteração/revogação durante
  chamada, resultado repetido, late write, crash e estado incerto. Testar também
  PostgreSQL isolado antes de habilitar; SQLite não prova concorrência real.
- Risco: duplicação de inferência ou uso de credenciais entre contas. Rollback:
  parar consumidores novos, revogar pareamento se necessário e preservar tentativas;
  nenhum reset de job nem execução de worker antigo sobre leases ainda ativos.

## 3. Uma ação por avaliação e revisão consolidada

- Integrar preparação aos especialistas existentes; reaproveitar deduplicação e
  contratos, vinculando cada aplicação/informante ao manifesto.
- Novos endpoints de revisão consolidada sobre `SpecialistReviewService`, com
  decisões/hashes por item, sem atalhos de aprovação nem marcação automática.
- Painel de preparação na avaliação/laudo, usando o progresso já existente como
  base; manter o painel experimental disponível para diagnóstico do piloto.
- Aceite: uma ação agenda toda a cobertura elegível; rejeição/edição/fonte antiga
  bloqueia síntese; aprovações atuais disparam a próxima etapa sem outro botão de
  geração; fechar a aba não perde estado. Sem inferência no frontend/Render.
- Risco: revisão em lote esconder falhas. Rollback: desativar avanço/painel novos,
  conservar decisões individuais; nenhuma aprovação histórica é removida.

## 4. Qualidade clínica e elegibilidade do escopo (gate de liberação)

- Executar regras contextuais e avaliação profissional previstas no plano clínico
  para os instrumentos do piloto. Registro de homologação separado de revisão
  individual e vinculado a perfil, regras/prompt, modelo e casos.
- Pré-checagem exige escopo homologado ou interpretação manual revisada. Piloto
  sintético pode exercitar instrumentos sem homologação, sem liberar uso clínico.
- Aceite: riscos semânticos conhecidos, negações/ressalvas e casos adversariais
  cobertos; erro crítico veta liberação independentemente da nota ponderada.
- Risco: equiparar nove perfis executáveis a nove perfis homologados. Rollback:
  retirar elegibilidade futura, preservar registro/artefatos e informar bloqueio.

## 5. Síntese, conclusão e recomendações na fila local

- Propostos: contexto de fontes aprovadas e serviços/contratos próprios de síntese
  e conclusão; adaptar `section_workflow_service.py` e registro de seções.
- Definir contratos, budgets e decomposição por domínio antes de ativar chamadas.
  Somente fontes autorizadas, minimizadas, identificadas e aprovadas atuais.
- Proibir dependência silenciosa de `AI_PROVIDER` legado; explicitamente local
  para esta esteira. Sem diagnóstico conclusivo automático ou referências inventadas.
- Aceite: contexto incompleto/excedido gera bloqueio, nunca truncamento silencioso;
  mudança/revogação de fonte invalida derivados; não copiar texto stale de outra
  avaliação, nem misturar versões/formulários/informantes.
- Risco: extrapolação clínica e contexto insuficiente. Rollback: suspender geração
  dessas etapas, manter rascunhos/versionamento, não tratá-los como aprovados.

## 6. Composição, auditoria e aprovação final

- Adaptar contexto/seções, `report_export_service.py`, auditoria e
  `report_approval_service.py`; reutilizar snapshots existentes.
- Novo modo usa manifesto aprovado como fonte autoritativa, não prioridades de
  texto/fallback do exportador legado. Tabelas/gráficos e identidade determinísticos.
- Preparar proposta e diff sem excluir capítulos editados nem sobrescrever edição
  humana. Vincular auditoria à versão materializada do conteúdo, fontes e template.
- Aceite: aprovação final falha com fontes/regras/revisões/auditoria incompatíveis;
  bytes aprovados preservados; reexportação histórica estável; seleção de template
  privada e sem troca durante a geração. Verificação visual Word/LibreOffice.
- Risco: divergência painel/DOCX ou perda de edição. Rollback: desativar composição
  nova; preservar snapshots e propostas, sem reexportar aprovado pelo fluxo legado.

## 7. Inicialização automática e operação assistida

- Entrega operacional separada: provisionar conta/credencial protegida, escolher
  distribuição WSL/caminhos reais, validar Ollama local e ausência de nuvem,
  configurar Agendador do Windows após login e supervisão do worker.
- Não assumir que systemd sozinho inicia WSL após reboot. Não guardar segredo na
  tarefa, logs ou repositório. Singleton e capacidade de uma inferência por GPU.
- Aceite: reboot/login, suspensão, rede/Ollama/Render indisponíveis, atualização
  de versões e revogação da credencial. Painel mostra heartbeat e pendências,
  sem promessa de 24h. Testes reais/instalação exigem janela operacional combinada.
- Rollback: desabilitar somente a tarefa/serviço instalado nesta entrega, revogar
  credencial e preservar fila; não apagar distribuição, modelo, banco ou arquivos.

## 8. Piloto e rollout

- Flags independentes propostas para preparação, síntese e integração ao documento;
  todas desligadas por padrão até seus respectivos critérios de aceite.
- Piloto sintético de ponta a ponta, depois escopo clínico homologado e autorizado.
  Não usar inferências reais para testes unitários nem o banco clínico para testes
  destrutivos/concorrentes. Monitoramento sem dados clínicos em logs.
- Reexecutar regressões backend, frontend, migrations, isolamento e exportação;
  medir tempos/contagens reais quando disponíveis e registrar avaliação humana.
- Publicação gradual por conta/escopo autorizado, com rollback exercitado antes de
  liberar. Não alternar silenciosamente uma execução em andamento para o legado.

## Dependências e autorização

1 → 2 → 3 fornece a esteira técnica. A etapa 4 é obrigatória para uso clínico,
não precisa esperar a UI inteira e pode ser desenvolvida antes. Etapas 5/6 ficam
sob flag e dependem de fontes aprovadas/contratos. Etapa 7 pode ser preparada
após 2, mas não deve consumir etapas clínicas não liberadas. Etapa 8 verifica tudo.

A aprovação das três recomendações fixa o destino arquitetural. Este documento
não aplica migrations, instala tarefas, altera credenciais ou inicia inferências.
O primeiro incremento de implementação é a etapa 1: pré-checagem, manifesto,
coordenação e API com testes offline, sem nova chamada de modelo.
