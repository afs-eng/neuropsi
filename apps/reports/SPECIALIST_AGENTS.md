# Especialistas PydanticAI — geração de rascunhos

## Entrega

Integração `pydantic-ai-slim[openai]==2.57.0` com respostas estruturadas,
evidências por achado, validações e fila persistente no PostgreSQL/Django.
Sem CrewAI, LangGraph, Redis ou Celery adicionais nesta etapa. Não há memória
compartilhada entre agentes: cada execução cria um agente/contexto novos.

Escopos iniciais: WISC-IV, WAIS-III, WASI, BPA-2, RAVLT, FDT, E-TDAH-PAIS,
SCARED e SRS-2. O catálogo declarativo contém outros instrumentos, mas eles são
explicitamente ignorados para execução até terem contratos/instruções próprios.
O registro **não certifica especialização clínica**. Os escopos atuais são
conservadores; manuais licenciados e referências autorizadas ainda precisam de
curadoria e homologação pela profissional antes de uso clínico em produção.

## Ativação controlada

Padrão: `SPECIALIST_AI_ENABLED=false`. Publicar a mudança não inicia chamadas
nem muda o pipeline atual. Para homologação, configure no backend **e no worker**:

```dotenv
AI_PROVIDER=openai
SPECIALIST_AI_ENABLED=true
SPECIALIST_AI_INSTRUMENTS=wisc4,bpa2,ravlt,fdt,etdah_pais,scared,srs2
SPECIALIST_AI_MODEL=<identificador-do-modelo-homologado>
```

Reutiliza `OPENAI_API_KEY` e `OPENAI_BASE_URL`, com suporte ao endpoint de chat
compatível da OpenAI/OpenRouter. Não há fallback silencioso de modelo ou provedor.
O modelo deve conseguir devolver JSON conforme o contrato; resposta inválida
falha fechada. Não ativar um modelo apenas por ser gratuito. Avaliar também as
políticas de retenção, subprocessadores e tratamento dos dados sensíveis.

Cada execução tem timeout HTTP de 120 segundos, limite global de 270 segundos,
até duas requisições de modelo (uma tentativa de correção de formato), 2.000 tokens
de saída por requisição e 4.000 no conjunto. O SDK não repete erros HTTP
automaticamente. Isso **não é um teto financeiro em reais/dólares**: os custos
dependem do provedor e dos tokens de entrada; monitorar o orçamento no provedor.

## Worker

Após instalar dependências e aplicar a migração `reports.0006`:

```bash
python manage.py run_specialist_worker
```

Para processar no máximo uma execução e sair:

```bash
python manage.py run_specialist_worker --once
```

No Render, criar um **Background Worker separado**, com o mesmo código, banco e
variáveis do backend. Build: `pip install -r requirements.txt`. Start:
`python manage.py run_specialist_worker`. As migrações devem ser aplicadas antes
de iniciar o worker (o comando de startup atual do web já as executa).

Não anexar o worker ao comando do Gunicorn. Não criar múltiplos processos por
instrumento. O worker processa sequencialmente e pode ter custo adicional no
Render; nenhum serviço pago foi criado automaticamente. Se o worker estiver
parado, as solicitações permanecem no banco, não na memória do servidor web.

## API privada

Bearer obrigatório. Somente o autor do laudo pode consultar/solicitar; o papel
admin de outro usuário não dá acesso. Solicitações exigem papel neuropsychologist
ou admin, aplicações validadas da mesma avaliação e laudo não finalizado/enviado.

- `POST /api/reports/{report_id}/specialist-runs`
  - JSON `{}`: solicita os instrumentos habilitados daquela avaliação.
  - JSON `{"application_ids": [123, 456]}`: limita às aplicações escolhidas.
  - Resposta `202`: `run_ids` e lista `skipped` dos instrumentos não habilitados.
  - O `202` confirma persistência, não conclusão nem aprovação.
- `GET /api/reports/{report_id}/specialist-runs`
  - Até 100 execuções mais recentes, com resultados, evidências, uso e estado.
  - `is_current=false` / `status=stale` se os dados tiverem mudado posteriormente.
  - `requires_professional_review=true` sempre.

Os especialistas usam os resultados atuais das aplicações no banco, não uma
interpretação antiga nem o snapshot salvo potencialmente desatualizado do laudo.
SCARED de autorrelato e de responsáveis permanecem execuções separadas quando
registrados como aplicações separadas. Não há comparação automática entre eles.

## Dados e estados

Entradas: resultados calculados/classificados, formulário disponível e idade em
meses na aplicação (somente se houver data de referência). Não envia cadastro,
anamnese, documentos, respostas brutas de itens ou interpretações antigas.
Há remoção de campos identificadores conhecidos e nomes conhecidos dos valores;
isso é **minimização**, não garantia de anonimização de qualquer JSON arbitrário.
Resultados psicométricos continuam sendo dados sensíveis.

Cada achado deve citar fatos existentes; números novos são recusados. O contrato
não prova validade clínica nem detecta todas as contradições ou classificações
incorretas: a revisão profissional continua obrigatória. Não enviar traces
clínicos a Logfire/LangSmith; esta integração não habilita esses serviços.

Fluxo: `queued → running → needs_review | failed | stale`. Não existe aprovação
automática nem estado aprovado nesta etapa. Nenhum resultado é copiado ao
`TestApplication.interpretation_text`, às seções do laudo ou ao DOCX.

Solicitações idênticas reutilizam a execução existente, inclusive quando falhou;
não há endpoint de retry nesta etapa. Mudanças de resultados geram nova chave e
nova execução. Mudança de modelo/endpoint gera execução separada. Atualizações nas
instruções/contratos exigem incrementar `SpecialistRunService.VERSION`.

Um job `running` há mais de dez minutos é marcado `failed/worker_interrupted`
pelo próximo ciclo do worker. Não há reenvio automático, porque o provedor pode
já ter processado/cobrado a solicitação. Execução reclamada por outro worker não
é processada novamente. Falhas externas não são registradas com seu texto bruto
(que pode conter dados clínicos ou credenciais).

## Validação e próximos passos

```bash
python manage.py test apps.reports.test_specialist_runs apps.reports.test_private_templates apps.reports.tests apps.reports.test_wais3_docx_model
```

Os testes usam `FunctionModel` e provedores bloqueados: nenhum caso clínico real é
enviado para avaliação automática. A homologação com o modelo escolhido deve ser
feita posteriormente, com casos anonimizados/autorizados e revisão profissional.
Os testes locais de persistência usam SQLite; a concorrência entre workers no
PostgreSQL e a operação no Render ainda precisam de verificação no ambiente de
homologação. A exclusão de uma aplicação remove seus rascunhos de especialistas,
preservando a compatibilidade com as rotas de exclusão anteriores.

Ainda faltam: interface dos agentes, revisão/aprovação vinculada ao snapshot,
retry explícito auditável, integração clínica e liberação do conteúdo aprovado
para DOCX. O fluxo de exportação anterior não foi alterado nesta entrega.
