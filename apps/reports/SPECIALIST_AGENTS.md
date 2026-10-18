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

### Ollama Windows + worker no WSL (piloto local)

Ollama é uma opção dos **especialistas**, independente de `AI_PROVIDER` usado pela
geração legada/auditoria. Não é necessário instalar Ollama ou ROCm no Ubuntu quando
o servidor já roda no Windows e o WSL em rede espelhada acessa `127.0.0.1:11434`.

Configurar **no backend que enfileira e no worker**:

```dotenv
SPECIALIST_AI_PROVIDER=ollama
SPECIALIST_AI_MODEL=qwen3:8b
SPECIALIST_OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
SPECIALIST_AI_INSTRUMENTS=wisc4
```

Manter `SPECIALIST_AI_ENABLED=false` até preparar os testes sintéticos. Exemplo
local: `infra/local/specialists-ollama.env.example`. Não trocar `AI_PROVIDER` ou
as chaves OpenRouter para configurar apenas os especialistas. Quando
`SPECIALIST_AI_PROVIDER` está vazio, o comportamento anterior via `AI_PROVIDER`
é mantido. Execuções existentes recebem `provider_name=openai` na migration
`reports.0009_specialist_provider`; não são reclassificadas silenciosamente.

**No Render, `127.0.0.1` é o próprio Render, não seu Windows.** O backend apenas
registra o destino na fila; somente o worker no seu WSL deve processar os jobs
Ollama. Ambos devem usar o mesmo banco. Não iniciar um worker Ollama no Render,
não expor a porta 11434 à internet, não abrir túnel público e não ativar dois
workers com configurações diferentes na mesma fila: um worker incompatível
marca o job como falha `configuration_changed`, sem enviá-lo ao outro provedor.

A implementação usa `/v1/chat/completions`, `OllamaProvider` do PydanticAI e schema
JSON nativo (`NativeOutput`). Solicita `reasoning_effort=none` (equivalente a
`think=false` para o Qwen3 nesta API). O teste anterior em `/api/chat` não comprova
sozinho essa rota: ainda é necessário testar o contrato completo de especialista
no Ollama real. Evidências e números continuam validados deterministicamente;
até duas requisições, mesmos limites de tempo/tokens, nenhuma alternativa externa.
Conexões locais ignoram proxies de ambiente e não seguem redirecionamentos.

A URL Ollama fica restrita a loopback com `/v1`; a chave externa não é usada.
Nomes contendo `cloud` ou namespace remoto são recusados, mas aliases locais
podem ocultar modelos remotos: **desative também recursos de nuvem no Ollama
Windows** (`OLLAMA_NO_CLOUD=1`, reiniciando o aplicativo) e confira a origem do
modelo. O código Django não consegue garantir sozinho o comportamento interno
de um servidor Ollama administrado fora dele. Use o modelo local baixado.

O teste técnico de JSON e GPU não é homologação clínica. O contexto observado
de 4096 tokens também não comprova capacidade para uma aplicação completa:
valide o tamanho de entrada, saída e ausência de truncamento com casos
sintéticos; ajuste o contexto no Ollama antes de homologar entradas maiores.

Depois de publicar/aplicar `0009` e preencher o arquivo local, a checagem de
configuração/banco (sem chamada de modelo) continua sendo:

```bash
NEUROPSI_ENV_FILE=.env.specialists.local .venv/bin/python manage.py run_specialist_worker --check --report-id 123
```

Não executa inferência e não comprova que o modelo está acessível. O comando
`--once --report-id 123` realiza uma execução real e deve ser usado inicialmente
somente com um laudo sintético autorizado. O piloto não foi ativado por esta
alteração e nenhum dado clínico foi enviado ao Ollama durante os testes offline.

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

### Piloto local com Render Free

O painel **Especialistas de IA — piloto experimental**, na página do laudo, é
separado dos botões de geração legada. Ele permite escolher aplicações, solicitar
rascunhos, atualizar o status manualmente, consultar evidências e registrar uma
decisão profissional. Não afirma que o worker está ligado e não faz polling nem
chamadas de IA automaticamente ao abrir a página.

1. Publicar backend/frontend e aplicar as migrações até `reports.0008` (o startup
   do Render já chama `migrate --noinput`). Nenhum worker pago é necessário para
   preparar o piloto; nenhum processo foi iniciado automaticamente.
2. Escolher explicitamente um modelo para homologação. Não foi escolhido um
   modelo automaticamente nem foram alteradas credenciais. Ser gratuito não
   implica qualidade clínica ou política de privacidade adequada. Usar primeiro
   casos sintéticos/anonimizados e autorizados.
3. Copiar `infra/local/specialists.env.example` para `.env.specialists.local`
   (ignorado pelo Git), preencher os valores e só então ativar o piloto. O backend
   Render e o worker precisam do mesmo modelo, endpoint e lista de instrumentos.
   O backend também precisa de `SPECIALIST_AI_ENABLED=true`; o arquivo local não
   modifica variáveis do Render. `SECRET_KEY` do worker pode ser uma chave local
   aleatória própria; não precisa copiar a chave de assinatura do backend.
4. **Banco compartilhado:** para processar solicitações feitas no site publicado,
   preencher `DATABASE_URL` com a URL externa do MESMO PostgreSQL do backend e
   `DATABASE_SSL_REQUIRE=true`. Uma cópia SQLite local não recebe a fila do site.
   Permitir conexão do computador nas regras de rede do banco, se necessário.
   Credenciais dão acesso a dados sensíveis: não publicar, não enviar em prints
   e preferir uma conta de banco com privilégios mínimos apropriados.
5. Conferir configuração/banco sem executar agentes, substituindo `123` pelo ID
   real de um laudo de teste:

   ```bash
   NEUROPSI_ENV_FILE=.env.specialists.local .venv/bin/python manage.py run_specialist_worker --check --report-id 123
   ```

   Variáveis já exportadas no terminal têm precedência sobre o arquivo. A checagem
   não reclama jobs, não altera seus estados, não valida a qualidade do modelo e
   não chama o provedor.
6. Solicitar as aplicações selecionadas no painel. Para processar **no máximo um
   job desse laudo**, deliberadamente (pode consumir quota/créditos):

   ```bash
   NEUROPSI_ENV_FILE=.env.specialists.local .venv/bin/python manage.py run_specialist_worker --once --report-id 123
   ```

   Para acompanhar continuamente somente esse laudo, remover `--once`. Encerrar
   com Ctrl+C. Não usar `nohup`, cron ou serviço em background sem decisão explícita.
   O filtro também limita a recuperação de execuções interrompidas ao laudo.
7. Atualizar o painel, revisar achados, limitações e evidências. Aprovar/rejeitar
   exige profissional responsável com CRP; rejeitar exige motivo. O histórico
   registra autor, instante e hashes dos dados/saída. Dados corrigidos ou conteúdo
   diferente invalidam a decisão para o rascunho atual. É possível registrar uma
   nova decisão sem apagar a anterior.

**Aprovar um rascunho do piloto não aprova o laudo.** Não há cópia automática para
seções, interpretações de testes, conclusão ou DOCX. A revisão experimental não
substitui homologação clínica. O histórico acompanha a execução: excluir uma
aplicação remove seus rascunhos e as respectivas revisões; não é um registro
clínico definitivo independente da aplicação. Laudos aprovados e seus snapshots
continuam protegidos pelo fluxo separado de aprovação.

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
  - `requires_professional_review=false` apenas quando a última decisão do piloto
    está aprovada e vinculada aos hashes atuais; isso não aprova o laudo.
- `GET /api/reports/{report_id}/specialist-status`
  - Configuração, modelo explícito, aplicações elegíveis e permissões do autor.
  - Não consulta o provedor nem comprova que o worker está online.
- `POST /api/reports/{report_id}/specialist-runs/{run_id}/reviews`
  - JSON com `decision` (`approved`/`rejected`), `notes`, `source_sha256` e
    `output_sha256` obtidos na consulta. A decisão fica vinculada ao conteúdo
    efetivamente revisado. Notas de rejeição são obrigatórias; máximo 2.000 caracteres.

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

Fluxo: `queued → running → needs_review | failed | stale`. As decisões profissionais
são registros separados em `SpecialistReview`, sem alterar o estado de execução.
Não existe aprovação automática. Nenhum resultado é copiado ao
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
python manage.py test apps.reports.test_specialist_pilot apps.reports.test_specialist_runs apps.reports.test_private_templates apps.reports.tests apps.reports.test_wais3_docx_model
```

Os testes usam `FunctionModel` e provedores bloqueados: nenhum caso clínico real é
enviado para avaliação automática. A homologação com o modelo escolhido deve ser
feita posteriormente, com casos anonimizados/autorizados e revisão profissional.
Os testes locais de persistência usam SQLite; a concorrência entre workers no
PostgreSQL e a operação no Render ainda precisam de verificação no ambiente de
homologação. A exclusão de uma aplicação remove seus rascunhos de especialistas,
preservando a compatibilidade com as rotas de exclusão anteriores.

Ainda faltam: retry explícito auditável, homologação clínica/modelo, monitoramento
operacional do worker e integração clínica dos rascunhos aprovados ao snapshot
final/DOCX. O piloto não substitui o fluxo legado e não modifica a exportação.
