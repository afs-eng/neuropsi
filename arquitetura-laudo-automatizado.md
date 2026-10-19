# Arquitetura — elaboração automatizada do laudo

## 1. Decisão e escopo

Decisões confirmadas pela profissional nesta conversa:

1. Um botão **Preparar laudo com IA** por avaliação, sem selecionar cada teste.
2. Revisão consolidada das interpretações antes da síntese; revisão final antes
   da aprovação/exportação definitiva. Nenhuma aprovação clínica automática.
3. Ollama local no Windows e worker no WSL, com inicialização automática a configurar.
   O computador precisa estar ligado, conectado e com capacidade disponível.

Este documento especifica o destino arquitetural, não funcionalidades já entregues.
O plano está em `laudo-automatizado-plan.md`. Não foram instalados serviços,
criadas migrations, feitas inferências ou alterados provedores nesta entrega.
Instalação, credenciais, inferência real e deploy são entregas operacionais próprias.

Objetivo: automatizar coordenação e elaboração, não substituir julgamento clínico,
validação profissional dos testes ou assinatura. Sem novo framework de agentes,
Redis/Celery, provedor pago ou aumento de orçamento nesta proposta inicial.

### Alternativas e motivos

| Decisão | Ganho | Limite aceito |
|---|---|---|
| Django + fila PostgreSQL, sem novo broker | Reutiliza stack e persistência atuais | Exige transições, leases e reconciliação bem testados |
| Um botão, não gatilho em toda edição | Menos operação manual com início explícito | A profissional ainda decide quando a avaliação está pronta |
| Dois checkpoints humanos consolidados | Remove cliques técnicos sem integrar interpretações não aprovadas | Não é produção clínica totalmente autônoma |
| Inferência local | Mantém o modelo no equipamento existente, sem provedor pago automático | Computador/rede/Render disponíveis são necessários |
| Worker via API no desenho alvo | Reduz exposição de credencial PostgreSQL e centraliza autorização | Requer pareamento, revogação, protocolo e tratamento de falhas |
| Integração gradual por flags | Preserva o legado e permite recuo controlado | Os modos precisam de identificação/proveniência separadas |

## 2. Fluxo de uso

```text
Avaliação + aplicações validadas + dados clínicos autorizados
                         │
             [Preparar laudo com IA]
                         ▼
        Pré-checagem e manifesto imutável de fontes
                         ▼
      Interpretações por aplicação/informante (fila local)
                         ▼
      Validação estrutural, numérica e regras clínicas
                         ▼
     [Revisar interpretações em uma única tela] ← profissional
                         │ todas as fontes obrigatórias aprovadas
                         ▼
        Síntese por domínios e integração entre fontes
                         ▼
         Rascunho de conclusão e recomendações
                         ▼
      Composição determinística das seções e do documento
                         ▼
       Auditoria + prévia + [Revisar e aprovar laudo]
                         ▼
             Snapshot final e DOCX versionado
```

Os dois checkpoints humanos são deliberados. Não será preciso clicar para
gerar cada componente ou avançar cada etapa técnica. Depois da revisão consolidada,
o sistema continua sozinho até a revisão final, se não houver bloqueio.
Uma falha clínica ou fonte faltante interrompe o avanço, sem aprovar por omissão.

### Pré-checagem e cobertura

- Confirmar proprietário, perfil, avaliação/paciente, relatório editável e revisão
  alvo. Se o relatório estiver aprovado, exigir nova revisão, não alterá-lo.
- Enumerar todas as aplicações relevantes, inclusive não validadas e sem suporte.
  Não usar somente uma lista filtrada que esconda o restante da avaliação.
- Distinguir dados clínicos obrigatórios ausentes de dados opcionais não informados;
  apresentar pendências, sem preencher por inferência.
- Instrumento implementado não é instrumento homologado. O modo clínico exige
  elegibilidade de perfil/modelo/regras e escopo homologados; o piloto sintético
  é separado e claramente identificado. As nove instruções atuais não bastam
  para liberar automaticamente nove instrumentos em produção.
- Para aplicação sem especialista elegível: bloquear cobertura ou permitir uma
  interpretação manual revisada, versionada e vinculada à aplicação. Exclusão
  de escopo deve ser decisão explícita da profissional, justificada e auditada.
  Nunca omitir o instrumento silenciosamente ou fabricar interpretação genérica.
- Não marcar testes como validados pelo clique de preparação. Não iniciar geração
  ao abrir página, em `autobuild=1` ou ao editar resultados.

## 3. Distribuição física

```text
Vercel: interface autenticada e acompanhamento
                  │ HTTPS
                  ▼
Render/Django: permissões, coordenação, revisão e validação autoritativa
                  │
                  ▼
PostgreSQL: execuções, dependências, fontes, tentativas e decisões
                  ▲
                  │ acesso somente pelo backend no desenho alvo
                  │
Worker WSL ── HTTPS autenticado de saída ── API de execução Django
    │
    └── loopback /v1/chat/completions ── Ollama no Windows
```

Não abrir a porta do Ollama à internet. Não supor que `127.0.0.1` no Render seja
o computador da profissional. Interface/banco/backend continuam na nuvem;
inferência local não equivale a sistema offline ou anonimização garantida.

### Coordenação durável sem daemon no Render Free

O orquestrador é lógica Django sobre estado persistido, não uma thread mantida
viva em uma requisição. Start, aprovação e conclusão de etapa gravam estado e
próximas etapas na mesma transação. O worker consulta trabalho elegível; uma
reconciliação idempotente recupera transições pendentes na consulta seguinte.
Nenhuma chamada de modelo acontece na requisição web de preparação/revisão.

Não depender de processos permanentes ou de Shell no Render Free. Suspensão do
serviço e indisponibilidade de rede geram espera visível, não perda de execução.
Heartbeat do computador não prova disponibilidade contínua do Render ou do modelo.

### Credenciais e isolamento do worker

Hoje o worker usa conexão direta ao banco e filtro por usuário. Esse filtro não
é uma barreira de segurança das credenciais PostgreSQL. Para a esteira multiusuária,
o alvo é um worker pareado a uma conta, com credencial revogável e escopos mínimos
para claim/heartbeat/resultado, sem conceder acesso ao banco clínico inteiro.

O backend deriva o proprietário da credencial, nunca de `username` enviado pelo
cliente. Não conceder revisão, aprovação final ou acesso a outras contas à
credencial do worker. Guardar segredo fora do repositório, logs e argumentos do
Agendador; preferir armazenamento protegido do sistema e provisionamento explícito.
Usar o backend para seleção de tarefas e validação de saída, mesmo quando a
validação também rodar no worker.

## 4. Componentes e reaproveitamento

| Componente | Responsabilidade e integração |
|---|---|
| Orquestrador de preparação (novo) | Manifesto, DAG de etapas, transições, bloqueios e reconciliação |
| Preflight de avaliação (novo/adaptado) | Cobertura, fontes, permissões, elegibilidade e plano de execução |
| `SpecialistRunService` | Reutilizar execução e deduplicação; adicionar associação ao workflow, roteamento e tentativas, sem reativar falhas |
| `SpecialistInputService` | Preservar fontes por aplicação; evoluir minimização, não enviar contexto integral a cada teste |
| PydanticAI/contratos BPA-2 e outros | Reutilizar estrutura/evidências; homologar regras próprias antes da liberação clínica |
| `SpecialistReviewService` | Reutilizar revisão vinculada a hashes; criar operação consolidada sem aprovar automaticamente |
| `SectionWorkflowService`/registro | Reutilizar dependências e ordem visual; ampliar vínculos com interpretações aprovadas |
| Contexto da síntese (novo) | Somente fontes permitidas e interpretações aprovadas atuais, identificadas e versionadas |
| Geradores de síntese/conclusão (novos/adaptados) | Contratos próprios, linguagem cautelosa, referências e revisão final |
| Composição determinística | Títulos, identidade, números, tabelas e gráficos vindos dos motores e fontes, nunca recalculados pelo LLM |
| `ReportApprovalService`/snapshot | Reutilizar aprovação e artefato imutável, acrescentando manifesto de proveniência da esteira |
| API/painel unificados | Um start, visão por avaliação, pendências, duas revisões e download autorizado |

### Não chamar o legado como atalho

`report_pipeline_service.py:44–75` gera seções e roda auditoria; não espera revisão
de especialistas. `report_generation_service.py:109–171` escolhe caminhos
determinísticos/IA e possui fallback próprio. Esses caminhos não constituem a
integração aprovada solicitada.

Reutilizar funções puras/contratos úteis, mas não chamar o pipeline inteiro e
declarar que o conteúdo veio de especialistas aprovados. Separar modo legado e
modo automatizado por flag e proveniência; proibir fallback silencioso entre
eles. O legado pode permanecer acessível explicitamente enquanto ocorre o piloto.

`report_pipeline_service.py:114` remove seções fora do conjunto ativo. A nova
composição deve preparar uma proposta e um diff, não repetir essa operação sobre
texto editado/revisado. O exportador também pode resolver textos antigos por
`clinical_interpretation`/fallback: no modo novo, deve usar exclusivamente as
versões selecionadas no manifesto para evitar divergência entre painel e DOCX.

## 5. Estado e dados propostos

Nomes abaixo são conceituais, a confirmar no plano de migrations. Não duplicar
`Report`, `ReportSection`, `SpecialistRun`, `SpecialistReview` ou snapshots.

| Registro | Conteúdo mínimo |
|---|---|
| Preparação do laudo | Proprietário, avaliação/revisão alvo, estado, versão do workflow, chave idempotente e manifesto de entrada |
| Etapa | Tipo, dependências, hashes de entrada/saída, versão de regras/prompt, configuração de modelo e bloqueios |
| Vínculo de fonte | Aplicação/informante, execução ou interpretação manual, revisão selecionada, hash e finalidade de uso |
| Tentativa | Etapa, worker, token/geração de lease, início/fim, orçamento reservado, contagens e falha segura |
| Worker pareado | Proprietário, versão/capacidades, configuração verificável, último heartbeat, credencial revogável e estado operacional |

Estado da preparação: `queued`, `running`, `awaiting_interpretation_review`,
`awaiting_final_review`, `blocked`, `failed`, `stale`, `cancelled`, `completed`.
`completed` exige aprovação final e snapshot preservado. Etapas têm seus próprios
estados; um job de teste `needs_review` não significa workflow finalizado.

### Manifestos e atualidade

O manifesto inicial contém identidades internas das fontes e seus hashes,
versões de regras/prompts/modelo, template imutável e escopo da avaliação. A
revisão consolidada produz um manifesto de interpretações aprovadas. A montagem
produz outro vínculo entre conteúdo, fontes e artefato. Não editar o manifesto
anterior em lugar de criar nova revisão de execução.

Revalidar propriedade, fontes, permissões, aprovações, regras e destino antes
do claim, da aceitação de saída, da síntese, da publicação da proposta e da
aprovação final. Encerrar sem publicar conteúdo se a autorização for revogada
durante a chamada. O resultado do worker é não confiável até validação no backend.

## 6. Dependências e pontos humanos

- Interpretações de aplicações distintas são independentes, mas inicialmente
  processadas em série por GPU, com concorrência de inferência igual a 1.
- Aprovação consolidada é uma ação sobre itens explicitamente conferidos, cada
  qual com seu hash e decisão. Em conflito de versão, rejeitar a operação sem
  aprovar silenciosamente uma mistura. Itens rejeitados continuam pendentes.
- Só iniciar síntese quando todas as fontes obrigatórias do escopo estiverem
  aprovadas, atuais e elegíveis. Uma interpretação manual também exige revisão.
- Anamnese/observações são fontes distintas: dados ausentes não são inventados.
  Selecionar apenas trechos necessários para integração, com proveniência; não
  enviar identificação profissional/paciente ao LLM para compor cabeçalho.
- Separar resumo de história, síntese por domínio, integração e conclusão quando
  o contexto exceder a janela; nunca truncar silenciosamente a história ou testes.
  Cada etapa deve respeitar orçamento e declarar insuficiência de contexto.
- Conclusão/recomendações são rascunhos; diagnóstico não é resultado automático
  de escala. Não inventar análise de discrepância, sintomas ou bibliografia.
- Aprovação final confere fonte/template/conteúdo e auditoria atuais; guarda
  identidade profissional, data, manifesto e bytes aprovados. Não depende de o
  worker local continuar online após o artefato ser aceito e preservado no backend.

## 7. Mudanças, edição e retomada

- Clique repetido com mesmo manifesto/política retorna a preparação existente,
  inclusive quando bloqueada/falha. Não cria nova chamada para contornar dedup.
- Mudança de uma aplicação invalida sua interpretação e etapas dependentes;
  alteração de história clínica afeta integração, não recalcula escores. Template
  afeta composição; regras/modelo podem afetar interpretação/integração. Conservar
  resultados independentes somente com prova de compatibilidade de fontes/regras.
- Criar revisão/diff para texto editado; não sobrescrever `content_edited` ou
  aprovação humana sem ação explícita. Não aplicar atualização a laudo finalizado.
- Revogação de aprovação impede novo uso das fontes e marca derivados não
  finalizados como desatualizados. Artefatos já aprovados permanecem históricos;
  correções usam nova revisão, não alteração dos bytes originais.
- Cancelamento impede novas etapas e aceitação de retornos atrasados. Não promete
  interromper instantaneamente uma inferência já em execução na GPU.
- Retry de consulta/upload é distinto de retry de inferência. Reenvio de resultado
  usa ID de tentativa e hash idempotentes, sem chamar o modelo novamente.
- Se o worker caiu após inferir e antes de confirmar gravação, consultar estado
  antes de qualquer reenvio. Resultado incerto vira bloqueio auditável. Nova
  inferência exige autorização específica e tentativa nova, sem resetar o job.
- Reservar consumo/limites da tentativa antes da chamada, preservando os limites
  existentes de cada especialista. Novas tarefas de síntese/auditoria terão limites
  explícitos e teto por preparação aprovados antes da ativação; não herdar chamadas
  ilimitadas nem ativar `AI_PROVIDER` externo por padrão.

## 8. Worker automático e saúde

Alvo operacional: Agendador de Tarefas do Windows inicia a distribuição WSL
correta e o worker após login; inicialização do Ollama e verificações prévias
devem estar coordenadas. Serviço systemd no WSL, sozinho, não inicia a distribuição
após reboot. Execução sem login é um modo separado a validar, não uma promessa.

Provisionamento único assistido: parear conta, proteger credencial, confirmar
distribuição/caminhos, modelo instalado/contexto, desligar recursos de nuvem do
Ollama, configurar tarefa sem senha/segredo em argumentos e testar reboot/login.
Sem download de modelo, troca de GPU/configuração ou exposição de portas automática.

Worker publica capacidade (etapas suportadas, versão, provedor/modelo) e heartbeat.
Backend só entrega tarefa compatível. Configuração incompatível gera pendência de
roteamento antes do claim, não falha clínica após consumir um job de outra política.
Lease com token por tentativa impede que worker atrasado sobrescreva estado atual.
Reiniciar o processo não autoriza repetir uma chamada incerta.

Computador desligado/suspenso/rede ausente: manter fila e informar motivo/último
heartbeat. Render indisponível: backoff de consultas limitado e visível. Não
prometer processamento contínuo 24h nem migrar automaticamente para provedor pago.

## 9. Documento e segurança

Identidade e tabelas/gráficos ficam na composição determinística. Tarefas de LLM
recebem entradas minimizadas; composição pode precisar de identificação, mas
esse payload não deve ser encaminhado ao modelo. Templates privados têm versão,
hash e acesso autorizado, inclusive quando entregues ao worker para renderização.

Trabalhos pesados (inferência e, se necessário, renderização) ficam fora de
requisições web longas. O worker local pode renderizar com pacote/template
compatíveis e devolver proposta de artefato; backend verifica permissões,
manifesto, limites de tamanho, integridade e validações antes de publicação.
Hashes asseguram vínculo/integridade, não garantem correção clínica ou visual.

Propostas e previews são identificadas como rascunho. Download final usa snapshot
aprovado; armazenamento privado e endpoints autorizados. Nenhum texto rejeitado,
prompt integral, segredo ou dado clínico em logs/tracing. Arquivos temporários
clínicos precisam de retenção mínima e proteção, sem cópia em repositório.

## 10. Interface

Uma tela por avaliação mostra cobertura, pendências e progresso por etapa.
Percentual global, se exibido, representa etapas encerradas e distingue falha de
sucesso. Geração do modelo continua indeterminada, com duração e último estado.
Exibir versão, fonte, worker online/offline e necessidade de ação humana.

Ações normais: Preparar laudo; Revisar interpretações; Revisar/aprovar laudo;
Baixar DOCX. Ações excepcionais: resolver pendência, aceitar diff, cancelar ou
autorizar nova tentativa. Não mostrar controles técnicos por aplicação no fluxo
principal; manter detalhes/evidências acessíveis para conferência.

## 11. Contratos de API propostos

Rotas ilustrativas, ainda não implementadas:

- `POST /api/evaluations/{id}/report-preparations`: pré-checagem/start idempotente;
  retorna preparação ou lista de bloqueios, não executa inferência na requisição.
- `GET /api/report-preparations/{id}`: escopo, etapas, cobertura e ações permitidas.
- `POST /api/report-preparations/{id}/interpretation-reviews`: decisões explícitas,
  hashes e manifesto; avanço transacional se cobertura completa.
- `POST /api/report-preparations/{id}/cancel` e `/retry-requests`: cancelamento ou
  nova tentativa autorizada, com justificativa e limites, nunca reset de histórico.
- API restrita de worker: pareamento, claim compatível, heartbeat, publicação
  idempotente de resultado e consulta do estado de tentativa. Contratos separados
  das rotas de revisão/finalização, com tamanho limitado e validação autoritativa.
- Reutilizar finalização/exportação atuais mediante extensão de proveniência e
  guardas do modo novo; não criar uma segunda aprovação final concorrente.

## 12. Critérios de liberação

Flag inicialmente desligada e piloto somente sintético. Antes de uso clínico:
regras contextuais e homologação do escopo, isolamento entre contas, concorrência
PostgreSQL em ambiente isolado, revogação/alteração durante chamada, worker
offline/reboot, prevenção de reenvio/gravação atrasada, contexto/token budgets,
preservação de edições, auditoria atual e verificação visual do DOCX.

Escopo automático não pode ultrapassar instrumentos/fontes homologados. Uma
esteira funcionando tecnicamente não homologa seus perfis nem seus resultados.
