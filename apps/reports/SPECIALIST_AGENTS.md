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

### Orçamento local Ollama: 4.000 tokens por resposta

`SPECIALIST_OLLAMA_MAX_TOKENS=4000` é definido nas configurações do projeto e
usado somente quando o provedor persistido da execução é `ollama`. A saída total
permitida nas duas requisições é 8.000 tokens. OpenAI/OpenRouter continua em
2.000/resposta e 4.000 acumulados. Não se altera o fluxo legado, o tempo limite,
o número de requisições, as validações ou a rejeição de conteúdo truncado.
Essa configuração não é uma variável aplicada ao servidor Ollama Windows;
o cliente envia o limite de saída a cada requisição pela API compatível.

A versão de execução Ollama recebe o sufixo `-ollama-4k`, mantendo a versão
clínica anterior. Isso permite uma nova solicitação explícita com o novo orçamento,
sem reativar ou apagar a execução #7. Solicitações repetidas da mesma política
continuam deduplicadas. Saídas antigas em `needs_review`, da mesma versão clínica,
permanecem revisáveis; alterar somente o orçamento não invalida seu conteúdo.
Jobs antigos pendentes não passam silenciosamente a executar com outro orçamento.

Para usar: publicar o backend e atualizar/reiniciar o worker local, solicitar um
novo rascunho no painel e processar o laudo sintético. Sem migration nova ou
alteração de credenciais. Não é necessário mudar os arquivos de ambiente para
esse limite fixo. Nenhuma inferência real é iniciada pela atualização.

**Saída não é contexto:** 4.000 tokens de saída não aumentam a janela de contexto
do servidor Ollama. A janela precisa comportar entrada, instruções e saída;
contexto insuficiente ainda pode impedir a geração completa. Conferir a janela
no Ollama Windows durante os testes; ela não foi alterada automaticamente.

### BPA-2: redação estruturada por componentes (versão `pydantic-bpa2-5`)

O especialista usa o modelo escolhido em `SPECIALIST_AI_MODEL` (inclusive o
`qwen3.5:9b` local), sem fine-tuning ou escolha automática de modelo. As instruções
foram configuradas para o formato de introdução, AC, AD, AA, AG e análise clínica.
O painel apresenta os títulos e preserva as evidências de cada parágrafo.

- O guia de leitura mapeia os escores calculados, percentis e classificações para
  os fatos originais; não recalcula normas. `total` significa escore em pontos,
  nunca quantidade de itens. AG é medida agregada, não subteste independente.
- Há exemplos sintéticos contrastantes: todas as medidas na Média e perfil com
  AC Inferior/AG Média Inferior. Os exemplos orientam estilo, não fornecem fatos.
- O contrato exige os seis blocos na ordem, com evidências dos campos disponíveis
  em cada modalidade e das classificações/percentis na síntese. Campos ausentes
  permanecem ausentes. Escores calculados e classificados divergentes bloqueiam
  a preparação da entrada, sem escolher silenciosamente um deles.
- São validados números, apresentação do escore em pontos/percentil/classificação,
  evidências e alguns erros conhecidos (quantidades de itens, AG como subteste,
  menção a WAIS/WISC). Não é uma validação semântica clínica completa: uma frase
  pode continuar inadequada mesmo com fatos citados. Revisão profissional e
  homologação com casos diversos continuam obrigatórias.
- Recomenda-se linguagem restrita às tarefas/normas, sem declarar preservação
  global, ausência de dificuldades cotidianas, significância estatística de
  diferenças ou diagnóstico. Integração com outros instrumentos fica fora deste
  agente. Não se incluem nomes do paciente nem se copiam nomes de exemplos.
- Falhas de validação na saída permitem uma correção dentro do limite existente
  de duas requisições; não há aumento automático de tokens/tempo ou fallback.
- No Ollama, o schema nativo de `evidence_ids` enumera as chaves exatas de `facts`
  desta aplicação. É criado por requisição, sem cache compartilhado entre pacientes.
  O modelo deve copiar os IDs apontados pelo guia, não nomes de componentes nem
  caminhos de `reading_guide`. Um enum orienta a geração, mas não substitui a
  validação: respostas de provedores que ignorarem o schema continuam bloqueadas.
- Em `evidence_not_found`, a tentativa de correção recebe a lista dos IDs permitidos,
  sem converter, remover ou completar referências silenciosamente. Texto rejeitado,
  IDs desconhecidos e mensagens brutas não são persistidos em diagnósticos.
  Falhas antigas sem texto rejeitado não permitem descobrir qual ID foi inventado.
- `section_evidence_requirements` informa o mínimo obrigatório por seção, gerado
  dos mesmos fatos e usado pelo validador: `required_ids` para percentil/classificação
  e `score_one_of` para ao menos um escore equivalente calculado/classificado.
  A síntese exige os percentis/classificações disponíveis das QUATRO modalidades,
  mesmo sem repetir números. Ausências na fonte continuam ausências, não zeros.
- Em `bpa2_missing_evidence`, o retry identifica todas as seções com lacunas e os
  IDs faltantes; não modifica a resposta nem completa citações automaticamente.
  O diagnóstico persistido adiciona apenas `validation_section`, com enum fixo de
  seis seções, nunca IDs, valores ou redação. Terminal e detalhes do painel mostram
  a primeira seção afetada. Falhas antigas não ganham diagnósticos retroativos.

Para retestar: publicar backend/frontend e atualizar também o código do worker
local. Não há migration nova. Manter o mesmo modelo/endpoint configurado nos dois.
As execuções BPA-2 anteriores ficam preservadas. Sucessos `needs_review` das versões
3 e 4 (com ou sem `-ollama-4k`) continuam revisáveis quando a fonte permanece atual:
as versões 4/5 mudam grounding/instruções de IDs, não as regras clínicas de validação.
Jobs antigos pendentes/falhos não são reativados pela mudança. As demais
especialidades mantêm sua versão. No laudo sintético, selecionar BPA-2
e solicitar novamente: isso cria uma nova execução com as instruções novas, sem
reutilizar a antiga. Processar com `--once --report-id ID` e atualizar o painel.
Também é possível manter o worker contínuo `--username SEU_USUARIO` já descrito
abaixo. A versão local nova é `pydantic-bpa2-5-ollama-4k`. O transporte e os retries
foram testados com respostas sintéticas; o modelo real ainda precisa ser retestado.
Se houver jobs antigos ainda na fila, podem ser marcados como desatualizados antes
do novo job; `--once` processa no máximo um job por chamada. Nenhum resultado é
inserido automaticamente no texto final ou DOCX, mesmo após aprovação do piloto.

#### Diagnóstico de falhas sem expor dados clínicos

`HTTP 200` confirma a resposta do servidor, não sua validade clínica/estrutural.
Uma execução pode fazer duas chamadas e falhar porque o modelo não corrigiu o
contrato. A versão 3 também corrige duas rejeições indevidas: escore citado pelo
ID classificado em vez do ID calculado, quando os valores são iguais, e a redação
natural `percentil de X`. Escores divergentes e ausência de evidência do componente
continuam bloqueados. A correção de evidências da versão 3 não alterou limites;
o aumento posterior autorizado somente para Ollama está descrito abaixo.

Novas falhas persistem apenas contagens de uso e metadados allowlisted em
`usage_payload`: `finish_reason` e `validation_code`. Não se guardam resposta
rejeitada, prompts, stack trace ou texto de exceções. A captura de mensagens é
temporária, em memória, sem ativar tracing. O worker imprime os códigos seguros;
o painel os traduz para mensagens em português.

Principais códigos: `output_schema_invalid`, `output_validation_failed`,
`output_truncated`, `provider_refusal`, `provider_timeout`, `provider_connection`,
`provider_rate_limit`, `provider_auth`, `provider_error`, `usage_limit_exceeded`.
Falhas internas não classificadas permanecem `generation_failed`. Em validação,
`validation_code` distingue evidência inexistente, número sem suporte e regras
de redação/evidência do BPA-2. Uma resposta marcada como truncada ou filtrada não
é aceita, mesmo que contenha JSON aparentemente válido.

Falhas antigas com `generation_failed` não têm seu motivo recuperável a partir
dos metadados anteriores. Para testar a correção BPA-2, atualizar backend/frontend
e worker local, solicitar um novo rascunho da versão 3 em caso sintético e processar
explicitamente. O job falho anterior não é apagado nem repetido; não há retry
automático, mutation de status ou migration nova. Só uma nova execução pode
confirmar o motivo de uma falha reproduzida no ambiente real.

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
até duas requisições, limites de tempo preservados e nenhuma alternativa externa.
Os limites de saída por provedor estão descritos abaixo.
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
até duas requisições de modelo (uma tentativa de correção de formato).
OpenAI/OpenRouter mantém 2.000 tokens de saída por requisição e 4.000 no conjunto.
Ollama local usa 4.000 por requisição e 8.000 no conjunto, conforme autorização
explícita do usuário. O SDK não repete erros HTTP
automaticamente. Isso **não é um teto financeiro em reais/dólares**: os custos
dependem do provedor e dos tokens de entrada; monitorar o orçamento no provedor.

## Worker

### Acompanhamento no painel

Após solicitar rascunhos, o painel exibe o acompanhamento da solicitação, com
espera na fila, geração/validação, conclusão para revisão ou falha. O tempo de
espera usa `created_at`; o tempo de análise usa `started_at`; execuções encerradas
usam `finished_at`, sem continuar contando. Ao reabrir a página, são exibidas as
últimas execuções por aplicação, com os timestamps persistidos.

A barra individual é indeterminada: não representa percentual ou estimativa de
término. Para múltiplas execuções, a barra agregada conta execuções encerradas,
incluindo falhas/desatualizadas, e não aprovação clínica. Os detalhes e as notas
de revisão continuam separados e não são sobrescritos pela consulta automática.

Enquanto houver pendências, a aba visível consulta status a cada 5 segundos após
a consulta anterior terminar; ao voltar à aba, consulta novamente. São apenas
GETs autenticados, não novas inferências, retries de jobs ou chamadas ao Ollama.
Erros de consulta preservam o último estado e mostram aviso; não comprovam falha
da IA. Consulta acima de 20 segundos é interrompida e pode ser refeita.

Não há heartbeat do worker nem progresso de tokens: `running` significa que o
worker iniciou a execução, não que continua saudável. Esperas acima de um minuto
e análises acima de cinco minutos pedem conferência do terminal, sem declarar
timeout ou reiniciar a execução. Falhas permanecem visíveis fora dos detalhes.

Verificação frontend (na pasta `neuro-frontend`):
`node --test components/reports/specialistProgress.test.cjs`,
`npx tsc --noEmit --incremental false` e lint dos componentes alterados.
Os testes cobrem lógica de polling e renderização estática; não substituem
verificação em navegador com worker/banco reais.

### Worker contínuo por conta, sem trocar o ID de laudo

Após atualizar o código local, é possível acompanhar todas as solicitações de
uma única conta. Substituir `SEU_USUARIO` pelo username exato da conta que solicita
os rascunhos no frontend (não pelo nome exibido, nem pela conta administrativa se
ela for diferente). Primeiro, checar banco/configuração sem inferência:

```bash
env -u DATABASE_URL -u SPECIALIST_AI_ENABLED NEUROPSI_ENV_FILE=.env.specialists.local .venv/bin/python manage.py run_specialist_worker --username SEU_USUARIO --check
```

Depois, iniciar continuamente, sem `--once` nem `--report-id`:

```bash
env -u DATABASE_URL -u SPECIALIST_AI_ENABLED NEUROPSI_ENV_FILE=.env.specialists.local .venv/bin/python manage.py run_specialist_worker --username SEU_USUARIO
```

O worker consulta a fila dessa conta em todos os laudos, inclusive laudos novos:
não é preciso mudar o comando quando o ID passa de 9 para 10, por exemplo.
Solicitar os rascunhos continua sendo uma ação explícita no painel de especialistas;
abrir um laudo com `autobuild=1` não enfileira especialistas por si só. O fluxo
legado de gerar laudo/anamnese continua separado. Nenhum job falho é repetido.

`--username` filtra o `requested_by` na consulta, claim e recuperação de execuções
interrompidas. Jobs de outras contas não são processados nem têm seu estado
alterado por esse worker. Os controles existentes de autoria, paciente, avaliação,
validação, modelo/provedor e fontes atuais continuam obrigatórios por execução.
A conta selecionada deve existir, estar ativa e ter perfil clínico autorizado.
Se combinar `--username` e `--report-id`, ambos os filtros são aplicados.

O terminal informa que o worker está ativo e avisa quando está esperando novos
jobs. A espera não é repetida a cada consulta, para evitar ruído. Ctrl+C encerra.
Essa opção não instala serviço nem inicialização automática: depois de reiniciar
o computador, iniciar novamente Ollama/worker, até configurar um serviço separado
com autorização explícita. Não houve chamada real nem início automático nesta entrega.

**Banco compartilhado:** remover apenas `--report-id` sem informar `--username`
mantém o comportamento antigo de acompanhar a fila de TODAS as contas, com aviso
explícito no terminal. Não usar essa modalidade no computador pessoal conectado
à instalação multiusuária. A conta do banco ainda precisa de privilégios mínimos:
o filtro do worker não substitui a proteção das credenciais do PostgreSQL.

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
