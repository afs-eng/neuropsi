---
name: gopsi-clinical-ai-quality
description: Auditar e evoluir os especialistas de interpretação neuropsicológica do GoPsi (Django, PostgreSQL, PydanticAI, worker WSL e Ollama), com foco em segurança clínica, rastreabilidade, homologação e integração controlada ao laudo.
---

# Skill — Qualidade clínica dos especialistas de IA do GoPsi

## Missão
Aprimorar o fluxo existente de especialistas sem reescrever a arquitetura nem alterar os motores psicométricos. A IA redige rascunhos fundamentados exclusivamente em dados validados; a profissional habilitada revisa e aprova. Sucesso técnico não equivale a homologação clínica.

## Contexto conhecido (confirmar no repositório)
- Frontend na Vercel; backend Django e PostgreSQL no Render.
- Fila persistente no PostgreSQL; worker Django executado no WSL consulta jobs e chama Ollama no Windows.
- Modelo inicial: `qwen3.5:9b-16k`; PydanticAI fornece contrato estruturado e tentativas controladas.
- Perfis: WISC-IV, WAIS-III, WASI, BPA-2, RAVLT, FDT, E-TDAH-PAIS, SCARED e SRS-2.
- BPA-2 já possui seis seções, guia e verificações específicas; execução #14 passou na validação técnica, sem aprovação clínica presumida.
- Fluxo legado de geração de laudos e novo fluxo de especialistas permanecem separados.
- Já existem fila com deduplicação, contratos com evidências, revisão vinculada a hashes da entrada/saída e diagnósticos seguros. Confirmar sua implementação e reutilizá-la; não criar serviços paralelos para as mesmas responsabilidades.
- O isolamento atual é por proprietário da conta. Não presumir um modelo de clínicas, equipes, compartilhamento ou administrador com acesso clínico global.

## Regras inegociáveis
1. Inspecionar o código, testes, migrações e contratos atuais antes de propor mudanças. Não presumir caminhos, classes ou nomes de tabelas.
2. Não recalcular, reinterpretar tabelas normativas ou alterar escores, percentis e classificações dos motores de testes. Usar somente aplicações marcadas como validadas e fontes atuais, conforme o contrato existente. Essa validação técnica não equivale a homologação clínica do perfil de IA.
3. Não inferir diagnóstico, ausência de transtorno, significância estatística, causalidade, precisão/erros, validade ou prejuízo funcional a partir de um escore isolado.
4. Não inventar observações clínicas, dados de outros testes, citações, normas ou evidências. Dados ausentes devem ser marcados como ausentes.
5. Não enviar identificadores pessoais ao modelo quando não forem necessários. Não registrar PHI/PII, prompts integrais ou textos clínicos em logs operacionais.
6. Não substituir automaticamente textos revisados nem integrar rascunhos ao DOCX. Toda aprovação precisa de identidade, data, versão e trilha de auditoria.
7. Preservar compatibilidade do fluxo legado, isolamento por proprietário da conta e controle de permissões; aplicar migrações seguras e reversíveis. Uma futura estrutura de clínicas/equipes exige projeto e autorização próprios.
8. A IA nunca homologa a própria qualidade clínica. Revisão humana é obrigatória.
9. Não trocar/baixar modelos, aumentar limites, ativar provedores pagos, tracing externo, serviços ou inicialização automática sem autorização específica. Preservar a política local/externa existente e a ausência de fallback automático entre provedores.
10. Testes automatizados devem usar dados sintéticos e transporte mockado/offline. Chamadas reais ao modelo, uso de dados clínicos reais, mutações no banco compartilhado, deploy e instalação desta skill são ações separadas, não autorizadas implicitamente por este documento.

## Procedimento obrigatório

### Fase 0 — Reconhecimento e linha de base
- Localizar modelos de job, worker, integração Ollama, perfis PydanticAI, validadores, API, frontend de revisão e pipeline DOCX.
- Mapear estados e transições, retries, idempotência, bloqueios de concorrência, timeout e política de recuperação.
- Executar testes atuais e documentar resultado. Não editar código até produzir um plano com arquivos afetados, riscos e estratégia de rollback.
- O rollback deve preservar execuções, revisões, aprovações e artefatos existentes. Prever compatibilidade de leitura e desativação por feature flag; não apagar histórico ou descartar trabalho da profissional para reverter uma entrega.
- Separar o que está implementado, o que foi verificado nesta execução e o que depende de ambiente real ou avaliação profissional. Não apresentar contagens antigas de testes como resultados atuais.
- Verificar contratos do Ollama realmente suportados pela versão instalada; não supor que `think`, `num_predict` ou métricas funcionem de modo idêntico em todos os endpoints.
- Confirmar o endpoint usado pelo projeto. Uma chamada sintética real só pode ser feita com autorização; sem ela, documentar o suporte ainda não verificado, em vez de presumir sucesso.

### Ordem de entrega e limites de avanço
- Primeiro concluir a Fase 0 e aguardar aprovação do plano, sem implementar alterações no sistema.
- Na Fase 1, consolidar o BPA-2 existente, sem reconstruir contratos, fila ou revisão já implementados.
- Priorizar a Fase 2 e a avaliação clínica da Fase 5 antes de expandir instrumentos ou integrar ao laudo. Implementar somente os registros mínimos necessários para essa avaliação.
- Planejar as demais métricas e a robustez operacional (Fases 3 e 4) como entregas próprias. Não é obrigatório implantar toda a telemetria para iniciar avaliação sintética controlada.
- Nenhuma fase autoriza automaticamente a seguinte. Cada entrega deve ter escopo aprovado, testes, riscos e critério de conclusão demonstrável.

### Fase 1 — BPA-2 como referência
- Preservar as seis seções existentes e os requisitos de evidências.
- Vincular cada afirmação factual a IDs de evidência atribuídos pelo backend; IDs desconhecidos ou não pertencentes ao job invalidam a resposta.
- Validar correspondência entre cada domínio (AC, AD, AA, AG), seus valores e classificação, sem recálculo pela IA.
- Distinguir desempenho em teste de funcionamento cotidiano. Nunca usar BPA-2 isoladamente para confirmar/excluir TDAH ou outro transtorno.
- Não concluir significância estatística de diferenças entre percentis sem análise apropriada explicitamente fornecida.
- Tratar comparação entre domínios como descritiva, sem superestimar pequenas diferenças.

### Fase 2 — Validação semântica em camadas
Implementar validadores determinísticos e auditáveis antes de considerar um segundo modelo crítico:
- Vocabulário de risco contextual: `fragilidade significativa`, `déficit comprovado`, `precisão limitada`, `ausência de transtorno`, `não possui TDAH`, `significância estatística`, `comprometimento severo`, `causado por`.
- Não bloquear por palavra isolada: considerar negação, citação, contexto, domínio, classificação e evidência.
- Regras determinísticas cobrem riscos conhecidos, não compreensão clínica completa. Definir escopo, severidade, evidência exigida, exemplos permitidos/proibidos e falsos positivos conhecidos por regra.
- Tipificar achados: `erro_factual`, `afirmacao_sem_evidencia`, `extrapolacao_clinica`, `estatistica_nao_sustentada`, `alerta_estilistico`.
- Bloquear erros factuais e afirmações clínicas críticas sem evidência; alertas estilísticos podem ir para revisão.
- Separar achados bloqueantes de avisos: nenhum aviso representa aprovação clínica. Quando a distinção depender de julgamento profissional, documentar a política aprovada, sem classificá-la silenciosamente como segura.
- Mensagens no painel clínico autenticado podem apontar seção, trecho mínimo, regra e evidência necessária, com acesso restrito ao proprietário autorizado. Não colocar trechos, valores, IDs clínicos ou mensagens brutas em logs operacionais, terminal ou telemetria; usar códigos e metadados explicitamente permitidos.
- Não passar a persistir respostas clínicas rejeitadas para melhorar mensagens. Qualquer retenção clínica adicional exige finalidade, acesso, prazo e autorização definidos. Sem trecho retido, mostrar somente a regra e os metadados disponíveis, sem reconstruir a resposta. Saídas inteiramente sintéticas de testes podem compor fixtures de regressão, claramente identificadas como tais.
- Nunca corrigir silenciosamente texto, inserir citações ou alterar conteúdo já aprovado. Mudanças materiais exigem nova versão e revisão vinculada ao conteúdo atual.

### Fase 3 — Contrato estruturado e observabilidade
- Evoluir schemas Pydantic preservando compatibilidade ou versionando explicitamente.
- Reutilizar inicialmente `findings`, `section`, `statement`, `evidence_ids`, `limitations` e `review_questions` quando esses forem os campos reais. Não renomear para `sections` nem duplicar a análise clínica existente apenas por preferência de formato.
- Metadados como versão do schema, instrumento, versão do prompt, modelo e achados de validação são conceitos a mapear sobre o contrato atual; novos campos exigem necessidade demonstrada e compatibilidade ou versionamento explícito.
- O backend, não o modelo, determina status, autoria, identidade de evidências e metadados de auditoria.
- `validation_findings`, severidade, bloqueios e decisões de revisão são resultados do backend/profissional. Uma autoavaliação do LLM não substitui os validadores nem pode atribuir aprovação.
- Persistir métricas por tentativa, quando disponíveis: `prompt_eval_count`, `eval_count`, `prompt_eval_duration`, `eval_duration`, `total_duration`, versão do modelo, quantização quando verificável, tempo de fila, tempo de validação, retry, tipo de falha.
- Tratar métricas ausentes como `null`, nunca como zero. Calcular tokens/s apenas quando contagem e duração forem válidas.
- Distinguir métricas nativas do provedor de tempos medidos no worker, registrando origem e unidade. Não trocar o endpoint só para obter métricas sem avaliar compatibilidade e obter aprovação.
- Um nome/tag de modelo não comprova pesos, digest, quantização ou revisão exatos. Registrar identidade verificável quando disponível; caso contrário, marcar como desconhecida e não inventar metadados.
- Aplicar retenção mínima e acesso restrito aos dados de execução.

### Fase 4 — Robustez da fila
- Garantir transições atômicas e idempotência por chave adequada (aplicação + perfil + versão de dados + versão de prompt, conforme regra do projeto).
- Implementar lease/heartbeat ou mecanismo equivalente, timeout, retomada segura de jobs abandonados e prevenção de dupla gravação.
- Recuperar o controle de um job não significa repetir sua chamada. A inferência pode ter terminado antes de uma queda do worker; heartbeat não garante execução exatamente uma vez.
- Preservar o comportamento atual de não reativar automaticamente jobs falhos. Uma nova tentativa precisa de política explícita aprovada, autorização auditada, identidade própria e vínculo ao job anterior, com limites de custo/tempo; rejeição clínica nunca dispara retry automático.
- Vincular gravações ao responsável/tentativa ativa e impedir que um worker atrasado sobrescreva outra execução, decisão ou recuperação. Preservar histórico; não resetar registros antigos para `queued`.
- Separar falha de transporte, modelo, schema, validação e revisão profissional.
- Não fazer retries infinitos nem reprocessar automaticamente uma rejeição clínica.
- Testar worker desligado, Ollama indisponível, timeout, duas instâncias e reinício após gravação parcial.

### Fase 5 — Homologação clínica
- Criar conjunto inicial de 20–30 casos BPA-2 sintéticos ou devidamente desidentificados, cobrindo perfis homogêneos, discrepantes, extremos, limítrofes, inconsistentes e dados incompletos.
- Guardar fixtures sintéticas, saídas de avaliação e versões em local apropriado. Dados derivados de pacientes, mesmo desidentificados, exigem avaliação de risco de reidentificação, autorização, acesso e retenção definidos; não incluí-los no repositório por padrão. Não copiar itens protegidos ou tabelas de manuais sem autorização/licença.
- Rubrica proposta: fidelidade 30%, adequação psicométrica 25%, prudência clínica 20%, clareza 15%, consistência 10%. É instrumento interno de comparação, não validação científica.
- Aplicar critérios eliminatórios antes da nota: erro de escore/classificação/domínio, referência inventada, diagnóstico indevido ou vazamento de dados impede homologação da versão avaliada até correção e reavaliação, independentemente da média ponderada. Casos deliberadamente inconsistentes devem ser recusados conforme o contrato; sua recusa correta não é erro do perfil.
- Os 20–30 casos constituem uma avaliação inicial, não evidência de validade clínica geral. Definir critérios de aprovação e cobertura com a profissional antes das execuções; incluir variações de redação, negação e casos adversariais, não apenas exemplos que passaram anteriormente.
- Registrar avaliação por profissional e justificativa; distinguir `tecnicamente_valido`, `clinicamente_homologado` (perfil/versão) e `aprovado_para_paciente` (texto específico).
- Vincular homologação ao instrumento, regras/prompt e modelo verificável, além do conjunto de casos e avaliação profissional. Mudanças materiais exigem reavaliação; aprovação de um rascunho individual não homologa o perfil inteiro.
- Comparar 9B e 27B somente com autorização específica e se ambos estiverem disponíveis, com mesmos dados e parâmetros documentados. Não baixar/trocar modelo, ativar provedor pago nem ampliar orçamento por iniciativa do agente.

### Fase 6 — Expandir para os outros instrumentos
- Criar matriz de riscos e regras por instrumento. Não copiar cegamente as regras BPA-2.
- Priorizar casos de fronteira e dados ausentes; verificar evidências e termos técnicos de cada teste.
- Exigir revisão de conteúdo clínico e critérios de homologação antes de habilitar produção.

### Fase 7 — Integração controlada ao laudo (feature flag)
- Criar mecanismo explícito de seleção de versão aprovada por profissional para cada instrumento.
- A síntese integrativa deve ser etapa separada, usando apenas dados validados e interpretações aprovadas, com fontes identificadas.
- Exportação DOCX deve preservar autoria, versão, proveniência e não sobrescrever edição manual sem confirmação.
- Manter fluxo legado como fallback; começar com feature flag desativada e rollout gradual.
- Testar rejeição, revogação de aprovação, edição posterior, geração repetida e isolamento multi-tenant.
- Neste projeto, testar inicialmente isolamento entre proprietários de contas; testes de clínicas/equipes só se esse modelo existir e estiver autorizado.
- No novo caminho de integração, aprovação expirada, revogada ou incompatível com hashes/versões atuais bloqueia a inserção. Fallback legado deve ser explícito e identificado, nunca uma forma de contornar a aprovação exigida para texto de especialista.

## Casos de aceitação obrigatórios BPA-2
Entrada de referência: AC=75/P40/Média; AD=79/P60/Média; AA=88/P50/Média; AG=242/P50/Média.
- Saída descreve corretamente os quatro componentes e a faixa média, sem trocar números ou domínios.
- Pode mencionar maior posicionamento descritivo da AD, sem afirmar diferença estatisticamente significativa.
- Não afirma que o paciente não tem TDAH, que não possui dificuldades cotidianas ou que há vantagem clinicamente significativa.
- Não cita WAIS, observações, sintomas ou diagnósticos se ausentes da entrada.
- IDs de evidência são válidos e pertencem à aplicação.
- Resposta com `fragilidade significativa` não sustentada gera achado bloqueante ou solicitação de revisão conforme a regra.
- `Há diferença estatisticamente significativa` sem análise fornecida deve ser bloqueado; `Não foi fornecida análise que permita afirmar significância estatística` deve ser permitido. `As diferenças não possuem significância estatística` também exige suporte: ausência de análise não comprova ausência de significância.
- `Precisão limitada` não pode ser inferida apenas do escore total baixo. Referências válidas de escore/percentil, por si só, não sustentam toda afirmação clínica do parágrafo.
- Citação ou negação não torna automaticamente uma frase segura: avaliar o que o trecho efetivamente afirma, com testes positivos e negativos para cada regra.
- Falha de validação nunca muda status para aprovação clínica.
- Job repetido não duplica interpretação nem substitui versão aprovada.

## Entregáveis por fase
1. Diagnóstico do código atual, com evidências (arquivos e linhas) e lacunas.
2. Plano de implementação incremental, riscos, migrações e rollback.
3. Código e testes automatizados com resultados reproduzíveis.
4. Relatório de antes/depois: taxa de schema válido, falhas factuais, extrapolações, tempo, tokens e avaliações humanas.
5. Documentação operacional do worker e do processo de aprovação.

## Critérios de conclusão
- Todos os testes existentes continuam passando, salvo mudanças explicitamente justificadas.
- Novos testes cobrem regras clínicas, segurança, concorrência, isolamento e integração.
- No novo caminho de integração de especialistas, nenhum texto sem aprovação profissional atual chega ao laudo final. Não presumir que essa garantia foi aplicada retroativamente ao fluxo legado; auditar esse fluxo separadamente.
- Nenhum resultado psicométrico é recalculado pelo LLM.
- Não declarar homologação clínica sem avaliação profissional registrada.

## Instrução de execução ao agente de programação
Comece exclusivamente pela Fase 0: inspecione o repositório, localize os componentes reais, execute somente testes seguros e apresente o diagnóstico e um plano em etapas. Pare para aprovação do plano antes de editar código do sistema. Não implemente todas as fases de uma vez. Após aprovação, execute apenas a entrega autorizada e seus testes; avance por entregas pequenas, demonstráveis e reversíveis. Uma solicitação de análise ou melhoria deste documento não autoriza instalar a skill, iniciar inferências nem executar suas fases no sistema.
