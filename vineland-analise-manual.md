# Vineland-3 — análise do manual, formulário e implementação

Data: 2026-11-09. Escopo: análise documental e inspeção da implementação, sem alteração de código ou de aplicações existentes.

## Conclusão principal

O arquivo `aux/vineland/Vineland-formulario.pdf` é o **Formulário de Pais/Cuidadores dos Níveis de Domínio**, terceira edição. Não é o formulário extensivo nem o formulário de entrevista. O módulo atual não automatiza esse protocolo: oferece correção por totais de subdomínios extensivos e um banco separado de 58 itens de edição não confirmada.

O profissional registrará as informações no sistema, conforme solicitado. Devem permanecer separados o profissional examinador/digitador e o pai/cuidador informante. A identidade do protocolo não muda para “Entrevista” porque o profissional digita as respostas. Se a coleta modificar a administração prevista, registrar essa condição para revisão clínica, sem alegar equivalência automática com a aplicação padronizada.

## Materiais e limites da análise

- `aux/vineland/VINELAND-3-MANUAL.pdf`: 33 páginas físicas; texto misto português/espanhol, falhas de tradução e lacunas em relação à paginação impressa. Serve de referência fornecida, mas não deve ser descrito como manual integral conferido.
- `aux/vineland/Vineland-formulario.pdf`: 16 páginas físicas, digitalizadas sem camada textual. Todas as páginas foram examinadas visualmente. As referências abaixo a esse formulário usam páginas físicas, coincidentes com a numeração impressa quando presente.
- `aux/vineland/Vineland3_AppMan_APX_C.pdf`: tabelas de Pais/Cuidadores; C.3 contém blocos separados para extensivo e níveis de domínio. Exemplo conferido visualmente: página física 111, impressa 105, idades 3:0–3:3.
- `aux/vineland/Vineland3_Instrucoes_Corrigidas.md`: transcrição parcial anterior; não corresponde ao banco do novo PDF. Não deve prevalecer sobre o protocolo identificado.

As normas dos apêndices disponíveis são americanas. Formulário em português ou impresso no Brasil não demonstra normatização brasileira. Esta análise não constitui homologação clínica nem confirmação de autorização para reprodução digital do instrumento.

## Estrutura exata do formulário escolhido

| Seção | Itens | Bruto possível | Páginas do formulário |
|---|---:|---:|---|
| Comunicação — COM | 40 | 0–80 | 4–5 |
| Atividades de Vida Diária — AVD | 40 | 0–80 | 6–7 |
| Habilidades Sociais e Relacionamentos / Socialização — SOC | 40 | 0–80 | 8–9 |
| Atividade Física / Habilidades Motoras — HMOT, opcional | 25 | 0–50 | 10 |
| Problemas de comportamento A — Internalizante | 13 | 0–26 | 11 |
| Problemas de comportamento B — Externalizante | 11 | 0–22 | 11 |
| Problemas de comportamento C — Itens críticos | 11 | Sem escore composto | 12 |

São **120 itens centrais**, **145 adaptativos com motor**, ou **180 itens se todas as seções forem aplicadas**. As seções opcionais não devem ser exigidas indiscriminadamente.

Cabeçalho: avaliado, nascimento, aplicação, idade calculada, examinador, informante e vínculo. Comentários gerais: página 12. Relatório de pontuação: página 13. Critérios complementares por item: páginas 2 e 15.

## Regras relevantes para a automação

### Aplicação, idade e completude

- Formulários de níveis de domínio começam aos 3 anos; **não usam ponto de início, basal ou teto**. Todos os itens das seções aplicadas devem ser respondidos (manual, página física 10, impressa 13).
- Habilidades motoras são opcionais e normadas até os 9 anos; comportamento mal adaptativo é opcional a partir dos 3 anos (manual, páginas físicas 7 e 9). A implementação deverá confirmar os limites exatos nas tabelas próprias desta versão.
- COM, AVD e SOC são necessários para obter o CCA. O manual permite administrar domínios individualmente, mas isso não autoriza calcular CCA com domínios ausentes (página física 9).
- Permitir salvar rascunho; distinguir rascunho de protocolo completo e de resultado clinicamente revisado. Campo vazio nunca é zero.

### Respostas e critérios por item

- Respostas adaptativas: `2` usualmente/frequentemente, `1` às vezes, `0` nunca, considerando desempenho real e independente, não apenas capacidade (formulário, página 3; manual, página física 16).
- Há itens **binários**, que aceitam apenas `0` ou `2`: COM 26, 33 e 39; AVD 40; SOC 4. Validar tanto na interface quanto no servidor (formulário, páginas 4–9).
- Cada item possui uma marca independente de **estimativa**. Não substituir por N/D. O PDF não apresenta N/D como alternativas deste protocolo.
- Preservar e exibir dicas e critérios específicos das páginas 2 e 15, inclusive regras sobre ajuda, lembretes e comportamentos já superados. A avaliação clínica da resposta continua com o profissional; não atribuir nota por IA.
- Problemas de comportamento têm sentido inverso: maior pontuação significa mais problemas. Usar legenda própria (formulário, página 11).

### Percentual estimado e validade

- Calcular por domínio: `estimados / itens respondidos × 100`; para domínio completo, os denominadores são 40, 40, 40 e 25, conforme caixas do formulário.
- Manual, página física 19, impressa 23: abaixo de 15%, validade provavelmente não comprometida; de 15% a menos de 25%, interpretar com cautela; a partir de 25%, não interpretar a seção.
- Em rascunhos, não apresentar o percentual provisório como validação final. Uma estimativa precisa estar associada a uma resposta numérica.
- Recomenda-se impedir interpretação automática da seção quando atingir 25% e do CCA quando um domínio central estiver sem condições de interpretação. Essa propagação é uma regra de segurança proposta para o sistema, a homologar clinicamente.
- Com 40 itens: 6 estimados = 15%; 10 = 25%. Com 25 itens: 4 = 16%; 7 = 28%. Testar esses limites.

### Correção normativa

Fluxo necessário para esta versão:

1. Validar itens e somar respostas de cada domínio aplicado, sem atribuições de basal/teto.
2. Converter o **bruto do domínio** em escore padrão e percentil, pela idade e pelas colunas **Formulário de Níveis de Domínio** de C.3.
3. Somar os escores padrão de COM + AVD + SOC.
4. Converter essa soma pelo **ABC/CCA do bloco de níveis de domínio** de C.3; HMOT não entra no CCA.
5. Obter IC com os valores específicos do formulário, domínio, idade e nível de confiança escolhido. O manual apresenta 85%, 90% e 95%, recomendando 90% para a maioria dos propósitos (páginas físicas 25 e 29).

**Não usar C.1 → escala-v de subdomínios para os domínios desse formulário. Não reutilizar a coluna ABC extensiva.** Na página C.3 conferida, os intervalos de soma para ABC já diferem entre os dois blocos. A presença de células sem conversão deve ser respeitada; não interpolar.

O relatório do formulário, página 13, traz uma remissão impressa a “D.3” para CCA, conflitante com a identificação Pais/Cuidadores e com os apêndices. Usar a identificação completa da tabela C.3 de Pais/Cuidadores, não seguir isoladamente essa remissão nem aplicar normas de Professores.

### Comportamento mal adaptativo e interpretação

- Somar A e B separadamente e converter em escala-v pela tabela E.2 de Pais/Cuidadores e idade, após conferir sua correspondência com o protocolo (manual, página física 26).
- Seção C: destacar individualmente itens com resposta 1 ou 2; não gerar soma diagnóstica, escala unificada ou diagnóstico automático.
- O manual fornecido apresenta descritores adaptativos na página física 32: baixo 20–70; moderadamente baixo 71–85; adequado 86–114; moderadamente alto 115–129; alto 130–140. É uma referência agora disponível, mas requer validação da fonte/terminologia antes de habilitar no produto.
- Não confundir esses intervalos com os descritores das escalas mal adaptativas. O manual adverte sobre limites dos rótulos qualitativos e sobre não interpretar o teste isoladamente (páginas físicas 30–31).
- Níveis de domínio não oferecem o perfil de subdomínios do extensivo. Não produzir equivalentes etários ou escores de crescimento de subdomínios para esse protocolo.

## Diferenças em relação ao sistema atual

| Local | Situação encontrada | Mudança necessária |
|---|---|---|
| `apps/tests/vineland3/item_protocol.py` | 58 itens parciais, edição não confirmada, respostas 0/1/2/N/D | Novo protocolo versionado com os itens deste PDF, sem reinterpretar registros antigos |
| `apps/tests/vineland3/config.py` | Três formulários exclusivamente extensivos | Identificar explicitamente informante e nível do formulário; incluir Pais/Cuidadores — níveis de domínio |
| `apps/tests/vineland3/api.py` | Modo `items` exige protocolo antigo e `form: null`; salva sem cálculo | Aceitar protocolo novo com identificação e validação próprias, preservando legado |
| `apps/tests/vineland3/validators.py` | Bloqueia correção item a item | Validação específica por idade, seção, resposta binária, estimativa e completude |
| `apps/tests/vineland3/import_norms.py` | Extrai somente bloco extensivo; seleciona os primeiros cabeçalhos | Importar separadamente bloco de níveis de domínio, IC e normas mal adaptativas pertinentes |
| `apps/tests/vineland3/norms.json` | Normas extensivas, sem separação por nível | Versionar esquema e origem; nunca sobrepor as colunas de versões distintas |
| `apps/tests/vineland3/calculators.py` | Bruto por subdomínio → escala-v → domínio → CCA extensivo | Implementar caminho próprio: bruto por domínio → C.3 de níveis de domínio → CCA correspondente |
| `neuro-frontend/components/tests/VinelandItemFields.tsx` | Legenda fixa com N/D; sem estimativa ou opções por item | Resposta digitável 0/1/2, restrições binárias, estimativa, dicas, pendências e seções opcionais |
| `neuro-frontend/app/dashboard/tests/vineland3/page.tsx` | Totais extensivos ou registro parcial sem correção | Fluxo do protocolo escolhido, distinguindo examinador de informante |
| `apps/tests/vineland3/interpreters.py` | Texto quantitativo, sem classificação ou IC | Texto determinístico usando resultados validados, alertas e identidade exata do formulário |

As proteções atuais de não corrigir o banco parcial são apropriadas e devem ser mantidas. Os novos PDFs identificam o novo protocolo; **não confirmam retroativamente os 58 itens antigos**.

## Plano de implementação e verificação

- [ ] Cadastrar protocolo novo com origem, versão e conferência dos 180 itens, dicas e cinco itens binários → comparar com páginas 2–12 e 15 do formulário.
- [ ] Separar o esquema normativo por informante e nível → conferir extração das colunas C.3 de níveis de domínio, incluindo ABC e IC, contra todas as páginas aplicáveis.
- [ ] Implementar persistência e validação específicas, sem migração automática do banco antigo → testar reabertura, edição, isolamento entre pacientes e preservação do legado.
- [ ] Implementar correção determinística e limites de estimativas → testar zeros, máximos, itens binários, omissões, idades limítrofes, motor opcional e CCA sem motor.
- [ ] Adequar a tela para preenchimento profissional e relatório → identificar informante, vínculo, examinador, versão, normas americanas e alertas.
- [ ] Verificar regressões, consistência entre tela/gráfico/laudo e casos corrigidos independentemente pelo profissional → só então habilitar uso clínico revisado.

## Resultado desta etapa

Identificação do protocolo e incompatibilidades confirmadas. Há material para iniciar a implementação correta, mas a transcrição do banco, importação das colunas adequadas e homologação de casos ainda não foram executadas. Nenhuma aplicação foi recalculada e nenhum bloqueio clínico foi removido.
