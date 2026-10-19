# IA clínica — diagnóstico da Fase 0

Data: 18/10/2026. Referência: `aux/neuropsi-clinical-ai-skill/SKILL.md`.
Escopo: reconhecimento, linha de base e plano. Nenhum código de aplicação,
configuração, migration, aprovação ou dado clínico foi alterado nesta entrega.
Não houve instalação da skill, inferência, acesso ao PostgreSQL compartilhado ou deploy.

## 1. Conclusão

A arquitetura existente atende ao piloto de rascunhos separados do laudo. Deve
ser evoluída, não substituída. A principal lacuna reproduzida é semântica: IDs e
números corretos não garantem que a afirmação clínica seja sustentada.

O BPA-2 atual é `pydantic-bpa2-5`, com sufixo local `-ollama-4k`. O sucesso #14
foi informado pela usuária; não foi consultado no banco nem considerado aprovação
ou homologação clínica nesta análise.

## 2. Mapa da implementação (linhas na revisão inspecionada)

| Responsabilidade | Evidência | Situação |
|---|---|---|
| Job, fontes, saída, configuração e uso | `apps/reports/models.py:169–201` | `SpecialistRun`, cinco estados e unicidade no banco |
| Histórico de revisão | `apps/reports/models.py:204–218` | Decisão, profissional, data, hashes; sem entidade de homologação do perfil |
| Preparação de fatos | `apps/reports/services/specialist_input_service.py:20–90` | Fingerprint de fontes, filtro de identificadores, limites de tamanho e guia BPA-2 |
| Instruções por instrumento | `apps/reports/services/specialist_instructions.py:4–33` | Nove perfis, sem treinamento individual de modelos |
| Contratos e suporte numérico | `apps/reports/services/specialist_contracts.py:27–95` | JSON estruturado, seis seções BPA-2, enum local de IDs e validação posterior |
| Regras específicas BPA-2 | `apps/reports/services/bpa2_specialist.py:89–177` | Requisitos por seção, alternativas equivalentes de escore e regras semânticas limitadas |
| Transporte e tentativas | `apps/reports/services/specialist_agent_service.py:37–148` | PydanticAI/OpenAI-compatible, Ollama nativo, limites e diagnósticos seguros |
| Fila, atualidade e recuperação | `apps/reports/services/specialist_run_service.py:65–218` | Transações, deduplicação, compare-and-swap e interrupção sem reenvio |
| Worker local | `apps/reports/management/commands/run_specialist_worker.py:16–83` | Filtros por conta/laudo, polling, check sem inferência e códigos seguros |
| Revisão profissional | `apps/reports/services/specialist_review_service.py:20–49` | Proprietário, perfil/CRP cadastrado, hashes e revalidação antes de aprovar |
| API privada | `apps/reports/api/specialist_endpoints.py:42–169` | Consulta, solicitação e revisão; não integra texto automaticamente |
| Propriedade dos dados | `apps/common/clinical_access.py:6–34` | Escopo individual; administrador não ganha acesso clínico global |
| Interface | `neuro-frontend/components/reports/SpecialistPilotPanel.tsx:74–228` | Consulta automática, revisão, evidências e notas preservadas em estado separado |
| Progresso | `neuro-frontend/components/reports/SpecialistProgressPanel.tsx`; `specialistProgress.ts` na mesma pasta | Tempo, barra indeterminada, espera prolongada e último estado; sem heartbeat |
| Aprovação do laudo | `apps/reports/services/report_approval_service.py:38–108` | Auditoria e snapshot de conteúdo, DOCX/HTML e modelo; separado da revisão do especialista |
| Exportação | `apps/reports/services/report_export_service.py:373–436,5807–5840` | Snapshot aprovado ou pipeline legado de contexto/seções; não consome aprovação de especialista |

Migrações inspecionadas: `reports.0006_specialistrun` (fila),
`0007_reportapprovalsnapshot` (artefato aprovado), `0008_specialistreview`
(revisão) e `0009_specialist_provider` (provedor na configuração/unicidade).
A execução dos testes construiu o banco efêmero com a cadeia de migrations;
isso não comprova quais migrations estão aplicadas no Render.

## 3. Estados e garantias atuais

```text
solicitação explícita → queued → running → needs_review
                                    ├──→ failed
                                    └──→ stale
needs_review → revisão aprovada/rejeitada em SpecialistReview
```

- Aprovação/rejeição não é novo estado do job e não altera o laudo.
- A chave de deduplicação é relatório + aplicação + hash de fontes + versão do
  especialista + modelo + endpoint + provedor (`models.py:198–201`). Repetir
  essa chave reutiliza o registro, inclusive se falhou; não repete inferência.
- O claim usa atualização condicional `queued → running`; somente quem consegue
  essa transição prossegue (`specialist_run_service.py:154–166`). Os testes atuais
  verificam exclusão sequencial; não comprovam concorrência PostgreSQL real.
- Antes da chamada, conferem-se perfil ativo, laudo editável, instrumento,
  configuração e fontes. Após geração, a atualidade das fontes é reavaliada.
  Revogação de perfil/status/configuração DURANTE a chamada requer testes próprios:
  `is_current` não repete todas essas verificações prévias. A revisão possui seus
  bloqueios próprios; isso não comprova segurança de uma integração futura.
- Jobs `running` com início anterior a dez minutos viram `failed/worker_interrupted`
  na próxima recuperação do worker no escopo selecionado. Não há heartbeat,
  agendador independente, lease ou identidade de tentativa. Com worker parado,
  essa recuperação não acontece sozinha.
- A gravação final exige estado ainda `running`; com a política atual, um job
  recuperado como falho não é sobrescrito pelo retorno atrasado. Introduzir
  reenvio exige proteção adicional por tentativa/lease, não apenas pelo status.
- A API pode apresentar um registro como `stale` por incompatibilidade atual,
  sem que o status persistido do histórico tenha sido reescrito.

## 4. Contrato Ollama e limites

- O caminho real é `/v1/chat/completions` via `OllamaProvider`, não `/api/chat`.
- Usa `NativeOutput`, `max_tokens` e `reasoning_effort=none`; não envia diretamente
  `num_ctx`, `num_predict` ou `think`. O efeito desses campos no servidor Windows
  não foi verificado nesta execução.
- URL restrita a loopback com `/v1`; proxies de ambiente e redirects desabilitados.
  Sem fallback externo; o cliente usa chave local, não a credencial OpenAI.
- Local: 4.000 tokens por resposta, 8.000 acumulados; externo: 2.000/4.000.
  Até duas requisições por execução; SDK sem retries de transporte.
- Timeout HTTP configurado em 120 s e limite global em 270 s. A janela de
  contexto é definida no Ollama, não por esses limites de saída.
- Contexto 16k, GPU, versão instalada, digest e quantização não foram consultados.
  Nome `qwen3.5:9b-16k` não comprova pesos/identidade ou contexto efetivo.
- Contagens agregadas de tokens/requisições existem; não há métricas nativas
  de duração por etapa do Ollama nem série persistente por tentativa. Não inferir
  essas métricas ou tokens/s dos dados agregados atuais.

## 5. Lacunas e riscos prioritários

### P1 — Qualidade semântica: reproduzida offline

Foi usado `synthetic_facts()` / `synthetic_output()` de
`apps/reports/test_bpa2_specialist.py`, com seis seções válidas e sem alterar
escores, percentis ou referências. Cada frase abaixo foi acrescentada isoladamente
ao componente AC ou à síntese e submetida a `validate_evidence`:

| Variação inteiramente sintética | Resultado atual | Resultado pretendido |
|---|---|---|
| `O desempenho ocorreu com precisão limitada.` | Aceita | Bloquear inferência de precisão apenas de escore total |
| `Há fragilidade significativa na atenção concentrada.` | Aceita | Regra contextual explícita, com severidade aprovada pela profissional |
| `As diferenças entre percentis não possuem significância estatística.` | Aceita | Bloquear conclusão estatística sem análise fornecida |
| `O paciente não possui TDAH.` | Aceita | Bloquear exclusão diagnóstica pelo teste isolado |
| `Não foi fornecida análise que permita afirmar significância estatística.` | Aceita | Preservar redação prudente |

As instruções proíbem extrapolações, mas o validador não implementa todas essas
proibições. Referências existentes sustentam os dados, não necessariamente todas
as inferências. Estes probes não são uma bateria de homologação e não medem a
frequência dessas frases no modelo real.

### P1 — Política de novas regras versus revisões antigas

`specialist_run_service.py:108–132` aceita sucessos BPA-2 de versões anteriores
como compatíveis; `specialist_endpoints.py:42–60` vincula revisão a hashes e
atualidade, não a uma versão independente dos validadores. Essa compatibilidade
foi criada para mudanças de grounding, não endurecimento clínico. Ao introduzir
novas regras, decidir como exigir reavaliação/revisão para uso futuro sem apagar
aprovações históricas nem reexportar artefatos já aprovados. Não estender
automaticamente a lista de compatibilidade à nova semântica.

### P2 — Robustez operacional e privacidade

- Faltam lease/heartbeat e tentativa auditada de reenvio; manter falhas terminais
  até haver política e proteção de gravação apropriadas.
- Controles de privacidade da entrada usam exclusões de campos e nomes conhecidos
  (`specialist_input_service.py:11–17,43–69`). São minimização de melhor esforço,
  não anonimização comprovada para qualquer campo/string. Avaliar allowlists por
  instrumento e testes adversariais antes de ampliar entradas.
- Logs/diagnósticos filtram códigos; não ampliar retenção de resposta rejeitada
  para exibir trechos. Painel clínico e observabilidade operacional têm requisitos
  diferentes. Configuração externa de logging/tracing também exige auditoria;
  os testes locais não certificam todos os logs de produção.
- Histórico de revisão não é homologação de perfil. Não existe ainda entidade
  específica que vincule avaliação profissional, casos, regras e modelo verificado.

### P3 — Integração e expansão

Sem seleção explícita de interpretação aprovada para consumo por síntese/DOCX.
Fluxo legado permanece separado. Outros oito perfis não têm a mesma profundidade
de contrato/regras do BPA-2. Não expandir por cópia cega das regras de atenção.

## 6. Linha de base executada nesta Fase 0

| Verificação | Resultado |
|---|---|
| Backend direcionado (especialistas, isolamento, revisão, laudo e exportação) | 319 testes OK, 31,961 s |
| Rede no runner backend | Bloqueada; `PHASE0_NETWORK_ATTEMPTS=0` |
| Banco | SQLite `:memory:`, sem leitura do `.env` pelo manage.py |
| Frontend `specialistProgress.test.cjs` | 10 testes OK; lógica e renderização estática |
| `tsc --noEmit --incremental false` | OK |
| Lint dos três componentes/utilitários de progresso e `lib/api.ts` | OK |

Log final backend: `/tmp/opencode/clinical-ai-phase0-backend-baseline.log`.
Runner local reproduzível: `/tmp/opencode/clinical_ai_phase0.py`, executado da raiz
com `PYTHONPATH=. .venv/bin/python /tmp/opencode/clinical_ai_phase0.py`.
Esses arquivos temporários não são artefatos versionados nem garantia de CI.

O runner define explicitamente settings locais, SQLite em memória e credenciais
fictícias, não executa `manage.py` (que carrega `.env`), e intercepta
`socket.socket.connect/connect_ex`, recusando conexões e exigindo contagem zero.
Usa os 19 módulos abaixo; os testes de transporte usam mocks/FunctionModel.

```text
apps.reports.test_specialist_worker_scope apps.reports.test_specialist_token_limits
apps.reports.test_specialist_diagnostics apps.reports.test_bpa2_specialist
apps.reports.test_specialist_ollama apps.reports.test_specialist_pilot
apps.reports.test_specialist_runs apps.reports.test_clinical_audit
apps.common.test_clinical_access apps.reports.test_report_approval
apps.reports.test_section_workflow apps.reports.test_private_templates
apps.reports.tests apps.reports.test_wais3_docx_model apps.patients.tests
apps.evaluations.tests apps.tests.test_wisc4_api apps.tests.test_thcp apps.api.tests
```

Transparência: a primeira execução isolada forçou o provedor global `ollama` e
teve duas falhas de expectativas de configuração em `test_specialist_runs`.
Foi ajustado apenas o runner temporário para `SPECIALIST_AI_PROVIDER=''`, usando
o fallback `AI_PROVIDER=openai` fictício esperado por esses testes. A suíte
completa foi reexecutada e passou, sem mudança no código/testes da aplicação.
Ambas as execuções tiveram zero tentativas reais de conexão.

Avisos de ausência de Times New Roman ocorreram; nenhum teste falhou por isso.
Não houve inspeção visual Word/LibreOffice, navegador real, teste PostgreSQL
concorrente, prova end-to-end de privacidade ou homologação profissional.

## 7. Próximo passo e limite desta entrega

Plano: `clinical-ai-implementacao-plan.md`. Aguardar sua aprovação antes de
iniciar a Fase 1. Nenhuma regra nova foi ativada; as lacunas acima permanecem
no comportamento atual até implementação/testes e revisão das políticas.
