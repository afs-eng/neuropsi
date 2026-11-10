# Vineland — completar análise de uma aplicação

Escopo: três Extensivos com IC95%, classificação, B/C/D.4–.6, subdomínios e fontes; consistência na tela/PDF/DOCX e revisão explícita. Preservar os três Níveis de Domínio e bancos de perguntas. Sem longitudinal, publicação ou alteração de pacientes reais.

- [x] Integrar normas específicas, médias não arredondadas, direção, taxas de base conservadoras e ausência distinta de zero; casos de referência e limites.
- [x] Recalcular leituras e vincular a revisão explícita dos Extensivos aos dados/resultados atuais, protegendo DOCX e atualização genérica.
- [x] Exibir análises, agrupamento e observações na interface; comparações adicionais recolhidas.
- [x] Completar PDF/DOCX e corrigir aviso de Motor; verificar PDFs reais e paginação.
- [x] Rodar regressões, lint/tipos/segurança, documentação e tentativa protegida de atualização do grafo, sem commit/deploy.

## Evidências e limites

- Caso `aux/VINELAND3-90.pdf`: EP COM/AVD/SOC/HMOT/CCA = 73/98/72/49/78; IC95% = 67–79/92–104/66–78/41–57/74–82. Fixture independente em `apps/tests/test_vineland_extensive_analysis.py`.
- IC95% e p=0,05 são configurações independentes fixas nesta etapa. Médias excluem CCA; subdomínios usam apenas escala-v. Taxas com células vazias são limitadas pelos limiares efetivamente publicados, sem inventar percentuais exatos.
- Resultados e revisão dos Extensivos são reconstruídos nas leituras. Nova aprovação é obrigatória para novos laudos Extensivos; a versão de revisão dos Níveis de Domínio permanece 1, sem invalidar aprovações por regras que não mudaram. Não há migração de dados ou alteração de snapshots finalizados.
- Comparações entre domínios diferentes ficam recolhidas na tela e em anexo identificado no PDF/DOCX. Não são testes de mudança longitudinal.
- PDFs sintéticos locais: três Extensivos com oito páginas (seis principais e duas de anexo), três Níveis de Domínio com quatro. HTML/PDF e imagens de inspeção em `/tmp/opencode/vineland-analysis-pdfs/`; nenhuma escrita em pacientes reais.
- Caso de referência e caso sem Motor com observações longas também renderizados; final das observações preservado. Regressão protege coordenadas SVG contra localização decimal com vírgula; tabelas mantêm formatação pt-BR.
- Validação: 219 testes backend, 37 testes de interface, TypeScript, ESLint, Ruff nos módulos específicos, Bandit sem achados e `git diff --check`. Os dois arquivos compartilhados grandes mantêm seus 46 achados Ruff preexistentes, confirmados por comparação com HEAD; nenhum achado novo.
- Homologação clínica independente continua necessária. Sem deploy ou verificação de produção.
- `npm audit`: 15 vulnerabilidades preexistentes (7 moderadas, 7 altas, 1 crítica), sem alteração de dependências.
- `graphify update .` executado: extraiu 8.177 nós, mas protegeu o `graph.json` existente de 9.030 nós contra substituição parcial; sem forçar sobrescrita.
