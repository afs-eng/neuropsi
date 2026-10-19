# Preparação do laudo — inventário inicial

Primeiro incremento de `laudo-automatizado-plan.md`. Implementado: pré-checagem,
manifesto de hashes, registro persistente idempotente, API privada e painel na
visão geral da avaliação. **Não é a esteira de geração completa.**

## Operação e ativação

- Flag backend `REPORT_PREPARATION_ENABLED=false` por padrão. Desligada: GET
  autorizado retorna somente `{"enabled": false}`, o painel fica oculto e POST
  é recusado, sem acessar as tabelas novas para consultar preparações.
- Migration aditiva: `reports.0010_report_preparation`. Publicar e aplicar no
  ambiente escolhido antes de ligar a flag; não foi aplicada no banco clínico
  nesta entrega. Publicar também o frontend para mostrar o painel.
- Não altera credenciais, modelo ou budgets dos especialistas. A configuração
  existente é inspecionada localmente, sem testar conexão ou disponibilidade.
- Usuários responsáveis com perfil neuropsicólogo/admin podem registrar fontes;
  leitura segue o escopo de proprietário/examinador do projeto. Admin de outra
  conta não tem acesso global. Registro não equivale a validação ou aprovação.
- Com nenhum laudo existente, o clique cria um rascunho vazio da própria conta.
  GET nunca cria laudo. Com vários laudos editáveis, selecionar explicitamente.
  Sem laudo editável, abrir revisão no fluxo existente; não criar automaticamente
  outra versão para contornar aprovação, envio ou geração em andamento.
- Rollback operacional: desligar a flag. Manter tabelas/manifestos e não reverter
  dados clínicos, seções, snapshots ou migrations em produção por conveniência.

Não foram realizados deploy, inferência real, instalação de serviço, alteração
de ambiente ou migration compartilhada durante o desenvolvimento deste incremento.

## API

Autenticação Bearer existente e `Cache-Control: private, no-store` nas respostas
da funcionalidade:

```text
GET  /api/report-preparations/evaluations/{evaluation_id}[?report_id=123]
POST /api/report-preparations/evaluations/{evaluation_id}
     {"report_id": 123} ou {} para seleção automática
```

GET: cobertura atual, pendências, candidatos a laudo alvo e preparação corrente
ou mais recente daquele laudo. POST: 201 para registro novo, 200 para reutilizado;
403 se desabilitado/perfil não autorizado, 404 para recursos fora de escopo e
409 para destino ambíguo/encerrado. Não retorna 202 nem afirma ter agendado IA.
Report IDs explicitamente enviados também são conferidos contra avaliação,
paciente e autoria. IDs desconhecidos/não pertencentes retornam 404.

## Persistência e atualidade

`ReportPreparation` guarda versão do workflow, manifesto, hash, pendências e
estado registrado; `ReportPreparationStep` guarda a sequência de etapas. A única
etapa concluída é o inventário; as outras ficam `unavailable`, não `queued`.
`ready_for_execution` é sempre **false** nesta versão, mesmo sem pendências.

Manifesto contém identificadores e hashes de paciente, profissional, avaliação,
seções/laudo, todas as aplicações e fontes clínicas (anamneses/templates,
evoluções e metadados de documentos). Mantém aplicações/informantes distintos,
inclusive não validados e sem especialista. Não persiste textos clínicos,
respostas, prompts ou chaves de provedor no manifesto.

Os hashes são um inventário de versões, **não uma cópia congelada/reproduzível
dos dados brutos**. Não devem ser usados sozinhos como snapshot de execução futura;
a próxima etapa deverá reconstruir/verificar fontes e congelar as entradas
efetivamente utilizadas. Também não provam anonimização ou correção clínica.

Alterações detectadas mostram `stale` por comparação, sem reescrever o registro
anterior. Novo clique cria registro para a nova versão; fontes e versão iguais
reutilizam o registro. A chave única no banco reforça a deduplicação. A transação
trava avaliação/laudo no PostgreSQL para serializar cliques desta funcionalidade.
Não existe garantia de serialização contra todos os escritores do legado;
nenhum registro daqui autoriza consumo automático por agente.

Os hashes são conservadores e incluem metadados/timestamps: até mudanças sem
efeito clínico podem requerer novo registro. O GET é uma leitura do estado atual,
não uma promessa de estabilidade futura; o clique verifica novamente o destino.

## Limites deliberados

- Não agenda especialistas, não consulta Ollama, não calcula novos escores, não
  valida aplicações, não aprova interpretações e não modifica seções/conteúdo.
- Verifica presença e utilizabilidade básica dos fatos do especialista, **não**
  recalcula normas nem faz validação clínica completa dos resultados.
- Não seleciona template DOCX, não verifica bytes de anexos, não gera documento,
  não faz auditoria e não comprova backup, armazenamento ou disponibilidade do worker.
- Perfil executável não significa perfil homologado. O painel não libera uso
  clínico dos nove especialistas; homologação e seus gates serão entregues depois.
- Limite planejado de 30 aplicações é apresentado como pendência, sem omitir
  aplicações excedentes do inventário. Fontes com paciente divergente bloqueiam
  o avanço sem divulgar conteúdo do paciente incorreto.
- Não usa `autobuild=1`. O botão legado “Gerar Laudo” permanece separado e não
  passa a consumir este manifesto ou interpretações aprovadas automaticamente.
- Atualização do painel é explícita; não há progresso de modelo/heartbeat para
  monitorar nesta entrega. Navegar/fechar a aba não apaga registros persistidos.

## Validação

- Novos testes: `apps/reports/test_report_preparation.py`; frontend:
  `neuro-frontend/components/reports/reportPreparation.test.cjs`.
- Executados offline com SQLite em memória e bloqueio de rede, mais regressões
  existentes. Verificar resultado consolidado no plano da primeira entrega.
- Testes de interface são renderização/estados, não automação de navegador.
  Concorrência real PostgreSQL, validação visual/browser, deploy e ensaio de
  infraestrutura permanecem pendentes; não usar SQLite como prova desses itens.
