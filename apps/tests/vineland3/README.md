# Vineland-3 — correção extensiva e Níveis de Domínio

Formulários extensivos: `entrevista`, `pais_cuidadores`, `professores`.
Código canônico: `vineland3` (o antigo rótulo genérico `vineland` no exportador não é um módulo de correção).

## Formulário de Pais/Cuidadores dos Níveis de Domínio — 180 itens

- Novas aplicações item a item usam `vineland3_parent_domain_180_v1`, de `domain_protocol.py`.
- Fonte: `aux/vineland/Vineland3_Todas_As_Areas_180_Itens.md`, com correção dos erros de OCR por consulta visual a `aux/vineland/Vineland-formulario.pdf`, páginas 4–12. O Markdown original foi preservado.
- Sete seções: Comunicação (40), Atividades de Vida Diária (40), Habilidades Sociais e Relacionamentos (40), Atividade Física opcional (25), Problemas de Comportamento A/B/C (13/11/11). Numeração independente por seção.
- Respostas digitáveis `0/1/2` e observações gerais. A tabela exibe apenas número, pergunta e resposta; estimativas e observações por item de registros anteriores continuam preservadas no payload. Binários: COM 26/33/39, AVD 40 e SOC 4 aceitam apenas `0/2`. N/D não pertencem ao novo protocolo.
- Banco completo significa completude do **cadastro**, não aplicação completa ou homologação clínica. Rascunhos e seções opcionais vazias podem ser salvos; estimativa sem resposta numérica é rejeitada. Não há basal ou teto nessa versão.
- Rascunhos são somente registro. Finalizados recebem correção normativa própria em `normative_results` (ver abaixo), sem inclusão automática no laudo. Critérios complementares das páginas 2 e 15 continuam exigindo consulta/revisão clínica; as dicas impressas junto aos itens estão vinculadas às perguntas.
- A API `/protocol` retorna o novo cadastro em `item_protocol` e o antigo em `legacy_item_protocol`. `/submit` aceita ambos por ID, com `entry_mode: "items"`, `form: null`, `raw_scores: {}`. Não se pode trocar o banco numa aplicação existente.
- Aplicações antigas continuam com os 58 itens originais e os códigos N/D. Não há migração automática de respostas entre bancos.
- Aplicações vazias criadas pelo botão de adicionar teste na avaliação abrem o cadastro de perguntas e podem recebê-lo no mesmo ID. A exceção só vale sem dados brutos, calculados, classificados, revisados, interpretação ou validação; registros travados continuam protegidos. Aplicações com dados anteriores exibem um atalho para abrir as 180 perguntas em outra aplicação, sem copiar ou substituir respostas.
- O profissional registra os dados; o campo respondente identifica o pai/cuidador informante. O preenchimento pelo profissional não altera a identidade do formulário para Entrevista.
- A entrada padrão de `/dashboard/tests/vineland3` é o questionário. O link da avaliação explicita `entry=items`. Se o ID recebido pertencer a totais extensivos ou outro banco de itens com dados salvos, a tela abre um questionário novo, avisa qual registro será preservado e envia `application_id: null` ao salvar. Para consultar o lançamento original, o link usa `entry=totals`; a edição explícita (`edit=true`) também preserva seu modo. Questionários atuais são reabertos e salvos no próprio ID.
- Rota de formulário unificada: `/dashboard/tests/vineland` contém a página; `/dashboard/tests/vineland3` reexporta a mesma página para compatibilidade. `lib/vineland-navigation.ts` gera o endereço usado pela avaliação, com `evaluation_id`, `application_id` e `entry=items`. A API e o código do instrumento continuam sendo `vineland3`; não há migração ou duplicação de dados.

### Finalização e resultado normativo

- O formulário mantém o salvamento parcial e oferece **Finalizar teste e ver resultados**. A API recebe `finalize: true` somente para finalizar o banco de 180 perguntas. O banco legado não permite essa finalização.
- COM, AVD e SOC precisam estar completas. Motor e comportamento A/B/C são opcionais: inteiramente vazios ficam não aplicados; se houver resposta, todos os itens da seção precisam ser preenchidos. Zero conta como resposta, vazio não. Os erros identificam a seção e os itens faltantes, sem alterar o registro salvo.
- O servidor salva `completion_status: finalized` e `item_summary` em `raw_payload`, gerando somas descritivas, contagem de respostas e itens críticos individuais. A seção C não recebe soma; somente itens com resposta 1 ou 2 são destacados para revisão.
- `/dashboard/tests/vineland/[id]/result` segue o layout WISC4: identificação, tabelas, perfil padronizado com IC, edição e retorno à avaliação. O botão **Imprimir / PDF** baixa o relatório próprio gerado no servidor; não imprime mais a tela HTML.
- O questionário finalizado reabre no resultado; `edit=true` restaura as respostas para edição. Nova finalização recalcula o resumo; salvar parcialmente remove o resumo anterior para não mostrar resultados desatualizados.
- `computed_payload`, `classified_payload` e interpretação continuam vazios para não alterar os bloqueios de inclusão no laudo do modo item a item. A API retorna a correção em `normative_results`, separada da validação clínica. É necessário publicar frontend e backend juntos.

### Cálculo específico — `domain_scoring.py`

- `domain_norms.json`: C.3, somente bloco Níveis de Domínio; IC 95%; C.4 (p = 0,05); C.5 (p = 0,05 e direção da diferença); E.2, exclusivamente Pais/Cuidadores. Não usa C.1 nem soma escala-v de subdomínios extensivos.
- Fonte primária: PDFs C/E fornecidos, com SHA-256 registrado. Conferência com os apêndices ingleses: 9.777 células C.3, 90 páginas, 30 conjuntos de IC, C.4/C.5/E.2 coincidentes. A planilha foi inspecionada, mas não é executada: contém referências erradas à E.1 e diferenças/lacunas de transcrição na C.3.
- Idade por meses completos das datas atuais do paciente/aplicação. COM/AVD/SOC a partir dos 3 anos; HMOT até 9:11; sem extrapolação acima do último intervalo da C.3 (90:11). Cada ausência é identificada por seção. CCA vem da conversão da soma dos EP de COM + AVD + SOC; HMOT nunca entra na soma do CCA.
- Média intrapessoal C.4 inclui os 3 ou 4 domínios com escores disponíveis (HMOT somente quando aplicado e normatizado). Compara diferenças não arredondadas aos valores críticos; apresentação em duas casas decimais. Taxas de base são faixas conservadoras das tabelas, nunca percentis interpolados.
- Níveis adaptativos do manual (página física 32): 20–70 Baixo; 71–85 Moderadamente baixo; 86–114 Adequado; 115–129 Moderadamente alto; 130–140 Alto. Não são diagnósticos.
- Ao abrir/exportar questionários antigos finalizados do mesmo protocolo, recalcula respostas, resumo e normas sem gravar, migrar, modificar validação ou alterar o payload armazenado. Legados parciais e totais extensivos permanecem separados. Dados inválidos retornam erro de conferência em vez de resultados em cache.
- `item_summary` permanece um resumo descritivo; `normative_results` é o contrato normativo e é usado tanto na tela quanto no PDF. Sem interpretação por IA.

```bash
uv run --no-project --with pymupdf python -m apps.tests.vineland3.import_domain_norms
uv run --no-project --with pymupdf python -m apps.tests.vineland3.import_domain_norms --verify-english
```

### PDF próprio no padrão WISC4

- Modelo visual consultado: `aux/vineland/modelo-wisc4.pdf` e imagens do relatório Vineland de níveis de domínio. Não há leitura do PDF modelo em produção nem reutilização de seus dados pessoais.
- Serviço `pdf_service.py` e template `templates/tests/pdf/vineland3_report.html`, com cabeçalho compartilhado `header.html`. Usa o mesmo gerador Chromium/Playwright dos demais instrumentos, com margens A4, tabelas azuis e rodapé numerado.
- Quatro seções/páginas usuais: identificação e finalidade; pontuação adaptativa, perfil padrão/IC e comportamento A/B; forças/fraquezas e diferenças, mais os 11 itens críticos individuais quando aplicados; síntese normativa e observações. Observações longas podem gerar páginas adicionais, sem truncamento.
- O resumo é recalculado a partir das respostas na exportação. Nomes, profissional/CRP, nascimento e idade vêm da avaliação/paciente atual, não do PDF modelo nem de um resumo antigo. Dados de texto são escapados pelo template Django.
- Registrado em `TestPdfExportService`: `GET /api/tests/applications/{id}/export-pdf` exige autenticação e acesso ao paciente. Recusa rascunhos, banco legado, totais extensivos e registros inconsistentes. O PDF é exclusivo do banco de 180 perguntas finalizado.
- Escores padrão, CCA, IC, percentis, escala-v e análises inferenciais são calculados pelo mesmo serviço da tela. Ausências por idade ou seção não aplicada são indicadas, sem zeros fictícios. O gráfico representa EP e hastes de IC95, não somas brutas.

## Disponível

- Entrada de pontuações brutas já corrigidas no protocolo, por subdomínio.
- Idade em meses completos calculada pelas datas de nascimento e aplicação.
- Tabelas B.1/C.1/D.1: bruto → escala-v; B.3/C.3/D.3: somas → escore padrão e percentil.
- Subdomínios aplicáveis dependem da idade e do formulário; motor é opcional, mas exige os dois subdomínios.
- CCA calculado com COM + AVD + SOC, sem incluir habilidades motoras.
- Aplicações independentes por respondente; atualizações somente por ID explícito.
- API autenticada, telas de entrada/resultado, gráfico e bloco DOCX para aplicações revisadas/validadas.
- Percentis extremos preservam `<1`/`>99`; sem extrapolação ou substituição por curva normal.
- Aplicações salvas **não validadas**, para revisão clínica antes de inclusão no laudo.
- Registro item a item do banco parcial fornecido: 58 perguntas em cinco domínios, respostas digitáveis `2/1/0/N/D` e pendências. Um único campo de observações gerais fica abaixo das perguntas e é compartilhado entre os domínios. Letras minúsculas são convertidas para maiúsculas; zero, vazio, N e D permanecem distintos.
- `general_observations` salva o texto geral (até 10.000 caracteres). Observações antigas por item continuam preservadas e são reunidas, com domínio e número do item, ao abrir um registro que ainda não possui o campo geral.
- Este banco tem **edição e formulário não confirmados**: não está associado aos três formulários extensivos e não recebe conversão normativa, classificação, interpretação ou inclusão no laudo, mesmo se marcado como validado.

## Fonte e rastreabilidade

Os apêndices fornecidos são explicitamente **normas americanas**, não uma amostra normativa brasileira.
`norms.json` contém apenas tabelas numéricas extensivas extraídas dos PDFs, sem dados pessoais das marcas d'água.
Cada resultado identifica arquivo, SHA-256 e páginas físicas do PDF.

Reimportação (dependência somente de desenvolvimento, sem alteração do ambiente da aplicação):

```bash
uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py
```

O importador confere cabeçalhos, marcadores laterais, continuidade dos intervalos e três páginas por tabela de escores padrão. Não executa macros da planilha.

## Novos materiais conferidos

- `aux/vineland/Vineland3_Instrucoes_Corrigidas.md`: fonte das perguntas e do layout; declara transcrição parcial e edição não comprovada. Banco versionado: `vineland_partial_transcription_v1`. Inputs de texto de um caractere, navegação por domínio preservando o estado e descrição/legenda imediatamente acima do domínio ativo. Por solicitação posterior, as observações passaram a um campo geral em vez de campos por item.
- `aux/vineland/vineland-3-manual-appendices.pdf`: edição inglesa de 2016, 525 páginas, apêndices B–E. Não contém regras de base/teto nem comprova a edição das perguntas transcritas.
- Conferência automatizada das **309 tabelas por faixa etária** (226 de subdomínios e 83 de domínios) contra esse PDF: **sem divergências** nos intervalos etários, intervalos brutos, escores e percentis. As normas e páginas originais em português foram preservadas.

Para repetir a conferência sem sobrescrever `norms.json`:

```bash
uv run --no-project --with pymupdf python apps/tests/vineland3/import_norms.py --verify-english
```

O modo `items` de `/api/tests/vineland3/submit` exige `item_protocol_id`, `form: null`, `raw_scores: {}` e `item_responses: {dominio: {item: {response, observation}}}`. Salva somente o registro, identificado pela aplicação/paciente/avaliação; respostas vazias são permitidas, valores inválidos não. Modos não podem ser trocados na mesma aplicação para evitar perda ou interpretação indevida dos dados.

## Limitações e revisão clínica

O PDF e a correção normativa identificam o protocolo **de níveis de domínio**, não os extensivos. A correção genérica continua rejeitando o modo `items`; o serviço específico é chamado pela finalização e pela leitura/exportação. As limitações do banco parcial antigo continuam válidas.

Os níveis adaptativos estão integrados ao serviço de níveis de domínio. A interpretação extensiva anterior não foi alterada. Nenhuma classificação representa validação clínica automática.

Ainda pendentes: equivalentes etários/VEC (não derivados das somas deste formulário), comparações entre informantes, homologação clínica independente dos casos e verificação autenticada em produção. Esses recursos não devem ser apresentados como concluídos.
