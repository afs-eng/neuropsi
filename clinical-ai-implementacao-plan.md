# IA clínica — plano incremental após a Fase 0

Diagnóstico: `clinical-ai-fase0-diagnostico.md`. Status: **proposto, aguardando
aprovação**. A autorização desta sessão abrangeu apenas reconhecimento/testes.

Atualização de escopo: posteriormente foram aprovadas as decisões de produto de
um botão por avaliação, revisão consolidada antes da síntese e worker local com
inicialização automática a configurar. Ver `arquitetura-laudo-automatizado.md` e
`laudo-automatizado-plan.md`. São especificações, não instalação/implementação já
executadas. As regras clínicas e critérios de homologação deste plano continuam
obrigatórios; o formato editorial BPA-2 foi tratado separadamente em
`bpa2-modelo-redacao-plan.md`.

## Entrega 1 — Consolidar BPA-2 (Fase 1)

- Arquivos existentes: `apps/reports/test_bpa2_specialist.py`,
  `test_specialist_diagnostics.py`, `test_specialist_pilot.py`,
  `test_specialist_runs.py`, `apps/reports/SPECIALIST_AGENTS.md`.
- Confirmar cobertura dos dois perfis sintéticos de referência, resultados
  incompletos, zeros versus ausência, escores equivalentes, fontes divergentes,
  troca de modalidades, evidências da síntese, mudanças durante geração/revisão,
  idempotência e preservação da edição humana. Adicionar testes faltantes.
- Documentar limitações semânticas e submeter a matriz de regras/severidades à
  profissional. Não transformar casos que hoje passam indevidamente em critérios
  de aceitação permanente nem declarar homologação porque a suíte passa.
- Aceite: novos testes de fundamentos e regressões passam offline; não há mudança
  de scores, saída pública, budgets ou integração. Sem migration prevista.
- Risco: confundir consolidação com aprovação clínica. Rollback: remover somente
  novos testes/documentação desta entrega, preservando histórico e artefatos.

## Entrega 2 — Regras clínicas contextualizadas (Fase 2)

- Aprovar previamente exemplos, severidades e limites: precisão inferida de total,
  diagnóstico/exclusão, significância afirmada ou negada sem análise, causalidade
  e generalização funcional. Definir a política de “fragilidade significativa”.
- Arquivo novo proposto: `apps/reports/services/bpa2_clinical_validation.py`;
  integrar ao `bpa2_specialist.py`/`specialist_contracts.py`, `specialist_errors.py`,
  `specialist_agent_service.py` e `specialist_review_service.py` conforme necessário.
- Reutilizar os seis blocos atuais. Achados gerados pelo backend, com tipo,
  regra, severidade, seção e versão das regras. Não pedir ao LLM que autorize
  sua própria saída; não completar citações nem corrigir texto silenciosamente.
- Testar negação, ressalvas, citação, contexto entre frases, domínio, classificações
  e lacunas. Regex não será anunciada como compreensão semântica completa.
- Rever compatibilidade em `specialist_run_service.py` e cálculo de aprovação
  atual em `api/specialist_endpoints.py`. Novas regras materiais exigem política
  de revalidação dos rascunhos antigos, sem reescrever decisões históricas.
- Painel `SpecialistPilotPanel.tsx`: mostrar bloqueios/avisos do backend; somente
  códigos seguros em logs. Nenhuma retenção nova de resposta clínica rejeitada.
- Aceite: os riscos reproduzidos no diagnóstico seguem a política aprovada;
  ressalvas legítimas passam; uma falha nunca vira aprovação; revisão não
  contorna bloqueio; até duas requisições e budgets existentes preservados.
- Schema: preferir evolução aditiva e desativável. Qualquer novo registro de
  avaliação requer migration própria aprovada; não reutilizar decisões humanas
  como se fossem avaliações automáticas. Sem backfill/revisão em massa automática.
- Rollout: flag específica inicialmente desligada. Rollback: desligar novos
  consumidores/geração; preservar metadados, novas avaliações e textos históricos.
  Não reabilitar para uso clínico saídas sabidamente bloqueadas apenas para
  restaurar compatibilidade. Definir leitura de dados aditivos antes de migrar.

## Entrega 3 — Avaliação inicial (Fase 5 e registro mínimo da Fase 3)

- Fixtures inteiramente sintéticas (20–30 casos) em diretório proposto
  `apps/reports/fixtures/clinical_ai/bpa2/`, sem itens protegidos/manuais.
- Matriz com saída esperada, recusa esperada e regras de risco. Rubrica interna,
  critérios eliminatórios e avaliação profissional vinculada a casos/versões.
- Definir registro restrito de avaliação de perfil/modelo/regras, separado de
  `SpecialistReview`. Modelo/migration aditivos dependem do desenho aprovado.
- Comparar antes/depois de validade estrutural, erros críticos, avisos e avaliação
  humana. Sem inventar taxa, tempo, identidade do modelo ou métricas ausentes.
- Execução real do modelo e armazenamento de suas saídas sintéticas exigem
  autorização própria. Nenhum 27B, download ou provedor pago está incluído.
- Aceite: a profissional registra decisão/justificativa e limites do escopo;
  erros críticos vetam homologação, independentemente da nota ponderada.
- Rollback: desativar o perfil para novos usos quando necessário, mantendo registros
  de avaliação e decisões. Não apagar evidência de falha ou aprovações históricas.

## Entrega 4 — Operação e concorrência (Fases 3/4)

- Arquivos: modelos/migration aditiva, `specialist_run_service.py`, worker,
  `specialist_agent_service.py`, API/painel e testes de fila.
- Projetar tentativa auditada, lease/heartbeat e gravação condicional por tentativa
  ativa. Testar duas instâncias, crash, atraso, indisponibilidade e timeout com
  PostgreSQL de teste isolado, nunca o banco compartilhado clínico.
- Distinguir recuperação de estado de reenvio. Reenvio não automático e com
  autorização/histórico, sem resetar falhas antigas para `queued`.
- Contagens e tempos por tentativa quando verificáveis; unidades/origem explícitas,
  ausências `null`. Nenhuma troca de endpoint/tracing para coletar métricas sem
  aprovação. Testes de rede reais são uma autorização separada.
- Aceite: nenhum worker atrasado sobrescreve outra tentativa/revisão, contagens
  respeitam limites e o painel não promete saúde contínua sem heartbeat válido.
- Rollback: parar workers afetados e desativar reenvio/novos consumidores; manter
  tabelas e histórico. Não executar worker antigo sobre leases ativos sem política
  de compatibilidade. Nenhuma migration destrutiva de rollback.

## Entregas futuras — expansão e documento (Fases 6/7)

- Regras/contrato e homologação próprios para cada instrumento, sem cópia cega.
- Integração aprovada explicitamente, em feature flag desligada inicialmente:
  selecionar versão com revisão atual para cada aplicação/informante; síntese
  separada, proveniência e proteção de edição humana.
- Arquivos candidatos: serviço de seleção novo, contexto/seções do laudo,
  `report_approval_service.py`, `report_export_service.py` e painel.
- Aceite: recusa/revogação/mudança de fontes ou regras bloqueia a nova inserção;
  exportação aprovada continua usando seu snapshot original; fallback legado não
  mascara ausência de aprovação de especialista. Testar isolamento entre contas.
- Rollback: desligar nova integração, preservando versões, revisões e snapshots.

## Critério de avanço

Cada entrega exige aprovação de escopo, testes offline, revisão dos riscos e
demonstração de resultado antes de avançar. Nenhuma delas autoriza alterar motores
psicométricos, limites, modelos, credenciais, deploy ou inicialização automática.
